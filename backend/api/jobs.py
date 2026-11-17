import csv
import io
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from backend.database import DatabaseManager
from backend.models import JobCreate, Job, FileClassification
from backend.config import load_settings, load_rules, DB_FILE, resolve_data_path
from backend.engine.control import get_job_control
from backend.engine.processor import JobProcessor
from backend.engine.job_manager import JobManager
from backend.engine.router import route_file
from backend.engine.owner_detector import normalize_owner_name, find_validated_customer
from backend.engine.default_roster import DEFAULT_VALIDATED_CUSTOMERS
from backend.engine.gemini_service import classify_document_with_gemini
from pydantic import BaseModel

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
db = DatabaseManager(DB_FILE)
db.init_db()

# Jobs execute in background threads; the SSE stream only subscribes to them,
# so disconnecting the client no longer aborts processing.
job_manager = JobManager(
    db=db,
    processor_factory=lambda: JobProcessor(db=db, rules=load_rules()),
)

def build_directory_tree(folder: Path) -> Dict[str, Any]:
    """Builds a nested dictionary tree of directories and files."""
    folder = Path(folder)
    if not folder.exists():
        return {"name": folder.name, "type": "directory", "children": []}

    def walk_dir(current: Path) -> Dict[str, Any]:
        node: Dict[str, Any] = {
            "name": current.name,
            "path": str(current),
            "type": "directory",
            "children": []
        }
        try:
            entries = sorted(current.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in entries:
                if entry.is_dir():
                    node["children"].append(walk_dir(entry))
                else:
                    node["children"].append({
                        "name": entry.name,
                        "path": str(entry),
                        "type": "file",
                        "size": entry.stat().st_size
                    })
        except Exception:
            pass
        return node

    return walk_dir(folder)

@router.post("", response_model=Job)
def create_and_start_job(job_req: JobCreate):
    source_p = Path(job_req.source_path).resolve()
    if not source_p.exists():
        raise HTTPException(status_code=400, detail="Source directory does not exist")

    settings = load_settings()
    out_p = resolve_data_path(job_req.output_path or settings.output_path)
    file_mode = job_req.file_mode or settings.file_mode
    threshold = job_req.confidence_threshold or settings.confidence_threshold
    template = job_req.folder_template or settings.folder_template

    job = db.create_job(
        source_path=str(source_p),
        output_path=str(out_p),
        mode=file_mode,
        threshold=threshold,
        template=template
    )
    return job

@router.post("/upload", response_model=Job)
def upload_and_start_job(
    files: List[UploadFile] = File(...),
    relative_paths: List[str] = Form(default=[]),
    output_path: Optional[str] = Form(None),
    file_mode: Optional[str] = Form(None),
    confidence_threshold: Optional[float] = Form(None),
    folder_template: Optional[str] = Form(None)
):
    import uuid
    intake_id = str(uuid.uuid4())
    temp_dir = resolve_data_path("./temp_intake") / intake_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    for idx, uploaded_file in enumerate(files):
        rel_path = relative_paths[idx] if idx < len(relative_paths) else uploaded_file.filename
        clean_rel = rel_path.lstrip("/\\")
        target_file_path = temp_dir / clean_rel
        target_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file_path, "wb") as f:
            f.write(uploaded_file.file.read())

    settings = load_settings()
    out_p = resolve_data_path(output_path or settings.output_path)
    mode = file_mode or settings.file_mode
    threshold = confidence_threshold or settings.confidence_threshold
    template = folder_template or settings.folder_template

    job = db.create_job(
        source_path=str(temp_dir.resolve()),
        output_path=str(out_p),
        mode=mode,
        threshold=threshold,
        template=template
    )
    return job

@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/{job_id}/files", response_model=List[FileClassification])
def get_job_files(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db.get_job_files(job_id)

@router.get("/{job_id}/tree")
def get_job_tree(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return build_directory_tree(Path(job.output_path))

@router.get("/{job_id}/csv")
def export_job_csv(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    files = db.get_job_files(job_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Original Path", "File Name", "Document Type",
        "Owner", "Confidence (%)", "Status",
        "Destination Path", "Matched Keywords", "Error"
    ])
    for f in files:
        writer.writerow([
            f.original_path, f.file_name, f.doc_type,
            f.owner, f.confidence, f.status,
            f.destination_path, "; ".join(f.matched_keywords), f.error_message or ""
        ])

    output.seek(0)
    filename = f"Docket_Report_{job_id[:8]}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{job_id}/stream")
def stream_job_progress(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    def event_stream():
        for event in job_manager.subscribe(job_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

class ReclassifyRequest(BaseModel):
    original_path: str
    new_doc_type: str
    new_owner: str
    target_folder: Optional[str] = None

class AnalyzeRequest(BaseModel):
    original_path: str

@router.post("/{job_id}/reclassify")
def reclassify_job_file(job_id: str, payload: ReclassifyRequest):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Layer 4: manual override. Serialize against background routing and
    # cancel this file's OCR/AI work so the manual result always wins.
    control = get_job_control(job_id)
    with control.lock:
        target_file = db.get_job_file(job_id, payload.original_path)
        if not target_file:
            raise HTTPException(status_code=404, detail="File not found in job")

        is_pending = target_file.status in ("queued", "processing") or not target_file.destination_path
        if is_pending:
            control.cancel(payload.original_path)
            destination_copy = (
                Path(target_file.destination_path) if target_file.destination_path else None
            )
            if destination_copy is not None and destination_copy.exists():
                source_path, route_mode = destination_copy, "move"
            else:
                source_path, route_mode = Path(target_file.original_path), job.file_mode
            if not source_path.exists():
                raise HTTPException(
                    status_code=400,
                    detail="Original file no longer exists (it may have been moved already)",
                )
            new_dest = route_file(
                source_file=source_path,
                destination_root=Path(job.output_path),
                owner=payload.new_owner,
                doc_type=payload.new_doc_type,
                target_folder=payload.target_folder,
                template=job.folder_template,
                is_unsorted=False,
                mode=route_mode,
            )
        else:
            # Already routed (sorted or unsorted): move it from the current
            # destination to the new one.
            current_dest = Path(target_file.destination_path)
            if not current_dest.exists():
                raise HTTPException(status_code=400, detail="Current destination file does not exist on disk")
            new_dest = route_file(
                source_file=current_dest,
                destination_root=Path(job.output_path),
                owner=payload.new_owner,
                doc_type=payload.new_doc_type,
                target_folder=payload.target_folder,
                template=job.folder_template,
                is_unsorted=False,
                mode="move",
            )

        updated = db.reclassify_file(
            job_id=job_id,
            original_path=payload.original_path,
            new_doc_type=payload.new_doc_type,
            new_owner=payload.new_owner,
            new_destination_path=str(new_dest)
        )

    return {"success": True, "file": updated.model_dump() if updated else None}

@router.post("/{job_id}/analyze")
def analyze_job_file(job_id: str, payload: AnalyzeRequest):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    settings = load_settings()
    if not settings.gemini_api_key:
        raise HTTPException(status_code=400, detail="AI is not configured. Add an API key in Settings.")

    control = get_job_control(job_id)
    with control.lock:
        target = db.get_job_file(job_id, payload.original_path)
        if not target:
            raise HTTPException(status_code=404, detail="File not found in job")
        control.cancel(payload.original_path)
        dest = Path(target.destination_path) if target.destination_path else None
        source = dest if dest and dest.exists() else Path(target.original_path)
        if not source.exists():
            raise HTTPException(status_code=400, detail="File no longer exists on disk")

        try:
            result = classify_document_with_gemini(
                file_path=source, rules=load_rules(),
                api_key=settings.gemini_api_key,
                model_name=settings.gemini_model,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"AI analysis failed: {exc}")

        doc_type = str((result or {}).get("doc_type") or "").strip()
        rule = next((r for r in load_rules() if r.enabled and r.name == doc_type), None)
        if rule is None:
            raise HTTPException(status_code=422, detail="AI could not match this document to a known type")

        ai_owner = str((result or {}).get("owner") or "").strip()
        owner = normalize_owner_name(
            ai_owner if ai_owner and ai_owner.lower() != "general" else (target.owner or "General")
        )
        vc = load_settings().validated_customers
        matched = find_validated_customer(owner, vc)
        if vc and not matched:
            raise HTTPException(status_code=422, detail="AI detected an owner not in the Validated Customers list")
        if matched:
            owner = matched
        new_dest = route_file(
            source_file=source, destination_root=Path(job.output_path),
            owner=owner, doc_type=rule.name, target_folder=rule.target_folder,
            template=job.folder_template, is_unsorted=False, mode="move",
        )
        updated = db.reclassify_file(
            job_id=job_id, original_path=payload.original_path,
            new_doc_type=rule.name, new_owner=owner,
            new_destination_path=str(new_dest), stage="ai",
        )
    return {"success": True, "file": updated.model_dump() if updated else None}

class ReorganizeRequest(BaseModel):
    folder_template: str

@router.post("/{job_id}/reorganize")
def reorganize_job_output(job_id: str, payload: ReorganizeRequest):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    rules = load_rules()
    rule_map = {r.name: r.target_folder for r in rules}

    db.update_job_template(job_id, payload.folder_template)

    files = db.get_job_files(job_id)
    for f in files:
        if f.is_unsorted or f.status == "error":
            continue
        current_dest = Path(f.destination_path)
        if not current_dest.exists():
            continue

        target_folder = rule_map.get(f.doc_type, f.doc_type)
        new_dest = route_file(
            source_file=current_dest,
            destination_root=Path(job.output_path),
            owner=f.owner,
            doc_type=f.doc_type,
            target_folder=target_folder,
            template=payload.folder_template,
            is_unsorted=False,
            mode="move"
        )
        db.update_job_file_dest(job_id, f.original_path, str(new_dest))

    return {"success": True, "files": [item.model_dump() for item in db.get_job_files(job_id)]}
