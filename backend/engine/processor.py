import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterable, Iterator, List, Optional

from backend.config import load_settings
from backend.database import DatabaseManager
from backend.models import JobStatus, FileClassification, RuleDefinition
from backend.engine.control import get_job_control, clear_job_control, JobControl
from backend.engine.extractor import extract_direct_text, extract_pdf_text_layer
from backend.engine.ocr import extract_ocr_text, extract_pdf_ocr_text
from backend.engine.owner_detector import detect_owner, normalize_owner_name, find_validated_customer
from backend.engine.classifier import classify_document
from backend.engine.gemini_service import classify_document_with_gemini
from backend.engine.router import route_file

logger = logging.getLogger(__name__)

# Fast pass: a PDF whose text layer has at least this many characters is
# classified immediately without OCR. Shorter/empty layers are scanned PDFs
# and are queued for the background OCR layer.
MIN_PDF_TEXT_CHARS = 20

# AI fallback results below this self-reported confidence are ignored.
MIN_AI_CONFIDENCE = 40.0


def max_job_workers() -> int:
    """How many files are processed in parallel (override: DOCKET_JOB_WORKERS)."""
    env = os.environ.get("DOCKET_JOB_WORKERS")
    if env:
        try:
            return max(1, int(env))
        except ValueError:
            logger.warning("Invalid DOCKET_JOB_WORKERS=%r, using default", env)
    return max(1, min(4, os.cpu_count() or 1))

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt",
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
OFFICE_EXTENSIONS = {".docx", ".doc", ".xlsx", ".xls"}


@dataclass
class _BackgroundOutcome:
    """A file that finished OCR but is not sorted yet (candidate for AI)."""
    file_path: Path
    unsorted_path: Path
    fc: FileClassification
    text: str


class JobProcessor:
    def __init__(self, db: DatabaseManager, rules: List[RuleDefinition]):
        self.db = db
        self.rules = rules

    def discover_files(self, source_dir: Path) -> List[Path]:
        """Recursively scans directory for supported files."""
        matched = []
        if not source_dir.exists():
            return []
        for p in source_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                matched.append(p)
        return sorted(matched)

    @staticmethod
    def _relative(file_path: Path, source_root: Path) -> Path:
        try:
            return file_path.relative_to(source_root)
        except Exception:
            return Path(file_path.name)

    def _queued_result(
        self, file_path: Path, rel_path: Path,
        output_root: Path, template: str, mode: str,
    ) -> FileClassification:
        """Queue for OCR but place it in Unsorted/ right away."""
        owner = detect_owner(
            rel_path,
            validated_customers=load_settings().validated_customers or None,
        )
        dest = route_file(
            source_file=file_path, destination_root=output_root,
            owner=owner, doc_type="Unsorted", target_folder="Unsorted",
            template=template, is_unsorted=True, mode=mode,
        )
        return FileClassification(
            original_path=str(file_path),
            file_name=file_path.name,
            doc_type="Pending OCR",
            owner=owner,
            confidence=0.0,
            destination_path=str(dest),
            status="queued",
            is_unsorted=False,
            stage="ocr",
        )

    def _route_guarded(
        self,
        control: JobControl,
        source_file: Path,
        destination_root: Path,
        owner: str,
        doc_type: str,
        target_folder: str,
        template: str,
        is_unsorted: bool,
        mode: str,
    ) -> Optional[Path]:
        """Route a file unless a manual override won the race.

        Routing is serialized per job so the background thread and a manual
        reclassify request can never move the same file twice.
        """
        with control.lock:
            if control.is_cancelled(source_file):
                return None
            return route_file(
                source_file=source_file,
                destination_root=destination_root,
                owner=owner,
                doc_type=doc_type,
                target_folder=target_folder,
                template=template,
                is_unsorted=is_unsorted,
                mode=mode,
            )

    def process_file(
        self,
        file_path: Path,
        source_root: Path,
        output_root: Path,
        threshold: float,
        template: str,
        mode: str
    ) -> FileClassification:
        """Layer 1 — fast pass (no OCR).

        PDFs use the embedded text layer, Office/TXT files are read directly.
        Images and image-only PDFs are returned with status="queued" so the
        caller can run them through the background OCR layer.
        """
        suffix = file_path.suffix.lower()
        rel_path = self._relative(file_path, source_root)
        text = ""
        error_msg = None

        if suffix == ".pdf":
            text = extract_pdf_text_layer(file_path)
            if len(text.strip()) < MIN_PDF_TEXT_CHARS:
                return self._queued_result(
                    file_path, rel_path, output_root, template, mode
                )
        elif suffix in IMAGE_EXTENSIONS:
            return self._queued_result(file_path, rel_path, output_root, template, mode)
        elif suffix in OFFICE_EXTENSIONS:
            text = extract_direct_text(file_path)
        elif suffix == ".txt":
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""

        owner = detect_owner(
            rel_path, text,
            validated_customers=load_settings().validated_customers or None,
        )

        if error_msg:
            classification_doc_type = "Unsorted"
            target_folder = "Corrupt"
            confidence = 0.0
            is_unsorted = True
            matched_keywords = []
        else:
            clf = classify_document(text, self.rules, threshold=threshold)
            classification_doc_type = clf.doc_type
            target_folder = clf.target_folder
            confidence = clf.confidence
            is_unsorted = clf.is_unsorted
            matched_keywords = clf.matched_keywords

        try:
            dest_path = route_file(
                source_file=file_path,
                destination_root=output_root,
                owner=owner,
                doc_type=classification_doc_type,
                target_folder=target_folder,
                template=template,
                is_unsorted=is_unsorted,
                mode=mode
            )
            dest_str = str(dest_path)
        except Exception as e:
            dest_str = ""
            error_msg = f"Routing error: {str(e)}"
            is_unsorted = True

        status = "error" if error_msg else ("unsorted" if is_unsorted else "sorted")

        return FileClassification(
            original_path=str(file_path),
            file_name=file_path.name,
            doc_type=classification_doc_type,
            owner=owner,
            confidence=confidence,
            destination_path=dest_str,
            status=status,
            is_unsorted=is_unsorted,
            error_message=error_msg,
            matched_keywords=matched_keywords,
            stage="fast",
        )

    def process_file_background(
        self,
        file_path: Path,
        unsorted_path: Path,
        source_root: Path,
        output_root: Path,
        threshold: float,
        template: str,
        mode: str,
        control: JobControl,
    ) -> Optional[_BackgroundOutcome]:
        """Layer 2 — OCR a scanned PDF or image in the background.

        Returns None when the file was cancelled (manual override) before it
        could be routed. Sorted results are routed here; unsorted results are
        returned as candidates for the AI fallback (layer 3) without being
        copied to Unsorted yet.
        """
        suffix = file_path.suffix.lower()
        cancel_event = control.event_for(file_path)
        rel_path = self._relative(file_path, source_root)
        read_path = file_path if file_path.exists() else unsorted_path

        try:
            if suffix == ".pdf":
                text = extract_pdf_ocr_text(read_path, cancel_event=cancel_event)
            else:
                text = extract_ocr_text(read_path, cancel_event=cancel_event)
        except Exception as exc:
            logger.warning("Background OCR failed for %s: %s", file_path, exc)
            text = ""

        if text is None:
            return None  # cancelled while OCR was running
        if control.is_cancelled(file_path):
            return None

        owner = detect_owner(
            rel_path, text,
            validated_customers=load_settings().validated_customers or None,
        )
        clf = classify_document(text or "", self.rules, threshold=threshold)

        if not clf.is_unsorted:
            try:
                dest = self._route_guarded(
                    control=control,
                    source_file=unsorted_path if unsorted_path.exists() else read_path,
                    destination_root=output_root,
                    owner=owner,
                    doc_type=clf.doc_type,
                    target_folder=clf.target_folder,
                    template=template,
                    is_unsorted=False,
                    mode="move",
                )
            except Exception as exc:
                dest = None
                logger.warning("Routing failed for %s: %s", file_path, exc)
            if dest is None:
                return None
            return _BackgroundOutcome(
                file_path=file_path,
                unsorted_path=unsorted_path,
                fc=FileClassification(
                    original_path=str(file_path),
                    file_name=file_path.name,
                    doc_type=clf.doc_type,
                    owner=owner,
                    confidence=clf.confidence,
                    destination_path=str(dest),
                    status="sorted",
                    is_unsorted=False,
                    matched_keywords=clf.matched_keywords,
                    stage="ocr",
                ),
                text=text or "",
            )

        return _BackgroundOutcome(
            file_path=file_path,
            unsorted_path=unsorted_path,
            fc=FileClassification(
                original_path=str(file_path),
                file_name=file_path.name,
                doc_type="Unsorted",
                owner=owner,
                confidence=clf.confidence,
                destination_path=str(unsorted_path),
                status="unsorted",
                is_unsorted=True,
                matched_keywords=clf.matched_keywords,
                stage="ocr",
            ),
            text=text or "",
        )

    def _ai_fallback(
        self,
        outcome: _BackgroundOutcome,
        control: JobControl,
        output_root: Path,
        template: str,
        mode: str,
    ) -> Optional[FileClassification]:
        """Layer 3 — ask Gemini to classify an OCR-unsorted document."""
        settings = load_settings()
        if not settings.ai_fallback_enabled or not settings.gemini_api_key:
            return None

        try:
            result = classify_document_with_gemini(
                file_path=outcome.unsorted_path if outcome.unsorted_path.exists() else outcome.file_path,
                rules=self.rules,
                text=outcome.text,
                api_key=settings.gemini_api_key,
                model_name=settings.gemini_model,
            )
        except Exception as exc:
            logger.warning("AI fallback failed for %s: %s", outcome.file_path, exc)
            return None

        if not isinstance(result, dict):
            return None
        doc_type = str(result.get("doc_type") or "").strip()
        try:
            confidence = float(result.get("confidence") or 0)
        except (TypeError, ValueError):
            confidence = 0.0
        rule = next(
            (r for r in self.rules if r.enabled and r.name == doc_type),
            None,
        )
        if rule is None or confidence < MIN_AI_CONFIDENCE:
            return None

        ai_owner = str(result.get("owner") or "").strip()
        owner = normalize_owner_name(
            ai_owner if ai_owner and ai_owner.lower() != "general" else outcome.fc.owner
        )
        vc = load_settings().validated_customers
        matched = find_validated_customer(owner, vc)
        if vc and not matched:
            return None
        if matched:
            owner = matched
        try:
            dest = self._route_guarded(
                control=control,
                source_file=outcome.unsorted_path if outcome.unsorted_path.exists() else outcome.file_path,
                destination_root=output_root,
                owner=owner,
                doc_type=rule.name,
                target_folder=rule.target_folder,
                template=template,
                is_unsorted=False,
                mode="move",
            )
        except Exception as exc:
            logger.warning("AI routing failed for %s: %s", outcome.file_path, exc)
            return None
        if dest is None:
            return None

        return FileClassification(
            original_path=outcome.fc.original_path,
            file_name=outcome.fc.file_name,
            doc_type=rule.name,
            owner=owner,
            confidence=min(100.0, confidence),
            destination_path=str(dest),
            status="sorted",
            is_unsorted=False,
            matched_keywords=[f"ai:{rule.name}"],
            stage="ai",
        )

    def _finalize_unsorted(
        self,
        outcome: _BackgroundOutcome,
        control: JobControl,
        output_root: Path,
        template: str,
        mode: str,
        stage: str,
    ) -> Optional[FileClassification]:
        """Layer 2/3 end: file stays Unsorted and is copied there now."""
        if control.is_cancelled(outcome.file_path):
            return None
        return outcome.fc.model_copy(update={
            "status": "unsorted",
            "is_unsorted": True,
            "stage": stage,
        })

    def _fast_pass(
        self,
        files: Iterable[Path],
        source_root: Path,
        output_root: Path,
        threshold: float,
        template: str,
        mode: str,
    ) -> Iterator[FileClassification]:
        """Layer 1 in parallel (bounded by max_job_workers), in input order."""
        file_list = list(files)
        workers = min(max_job_workers(), len(file_list)) if len(file_list) > 1 else 1

        if workers == 1:
            for file_path in file_list:
                yield self.process_file(
                    file_path=file_path,
                    source_root=source_root,
                    output_root=output_root,
                    threshold=threshold,
                    template=template,
                    mode=mode,
                )
            return

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(
                    self.process_file,
                    file_path=file_path,
                    source_root=source_root,
                    output_root=output_root,
                    threshold=threshold,
                    template=template,
                    mode=mode,
                )
                for file_path in file_list
            ]
            for future in futures:
                yield future.result()

    def run_job_generator(self, job_id: str) -> Generator[dict, None, None]:
        """Runs the layered pipeline, yielding real-time progress events.

        Layer 1 (fast)  : text layer / office / txt -> classify & route.
        Layer 2 (bg)    : queued scans & images -> RapidOCR -> classify & route.
        Layer 3 (AI)    : still unsorted -> Gemini classification (if enabled).
        Layer 4 (manual): user override cancels that file's background work.
        """
        job = self.db.get_job(job_id)
        if not job:
            yield {"event": "job_error", "job_id": job_id, "error": "Job not found"}
            return

        source_root = Path(job.source_path)
        output_root = Path(job.output_path)
        files = self.discover_files(source_root)
        total_files = len(files)
        control = get_job_control(job_id)

        self.db.update_job_status(job_id, JobStatus.PROCESSING, total_files=total_files)

        yield {
            "event": "job_started",
            "job_id": job_id,
            "total_files": total_files,
            "source_path": str(source_root),
            "output_path": str(output_root)
        }

        start_time = time.time()
        fast_start = time.time()
        sorted_count = 0
        unsorted_count = 0
        queued_count = 0
        pending_paths: List[str] = []

        # ── Layer 1: fast pass ──────────────────────────────────────────
        for idx, fc in enumerate(self._fast_pass(
            files,
            source_root=source_root,
            output_root=output_root,
            threshold=job.confidence_threshold,
            template=job.folder_template,
            mode=job.file_mode,
        )):
            if fc.status == "queued":
                self.db.add_pending_file(job_id, fc)
                queued_count += 1
                pending_paths.append(fc.original_path)
            else:
                self.db.add_job_file(job_id, fc)
                if fc.is_unsorted or fc.status == "error":
                    unsorted_count += 1
                else:
                    sorted_count += 1

            yield {
                "event": "file_processed",
                "job_id": job_id,
                "processed_count": idx + 1,
                "total_files": total_files,
                "sorted_files": sorted_count,
                "unsorted_files": unsorted_count,
                "queued_files": queued_count,
                "file": fc.model_dump(),
            }

        fast_duration = round(time.time() - fast_start, 2)
        self.db.recompute_job_counts(job_id)

        yield {
            "event": "fast_pass_completed",
            "job_id": job_id,
            "total_files": total_files,
            "sorted_files": sorted_count,
            "unsorted_files": unsorted_count,
            "queued_files": queued_count,
            "duration_seconds": fast_duration,
        }

        # ── Layer 2: background OCR of scanned PDFs & images ─────────────
        ai_candidates: List[_BackgroundOutcome] = []
        background_done = 0

        for path_str in pending_paths:
            if control.is_cancelled(path_str):
                continue
            file_path = Path(path_str)
            if not file_path.exists():
                # A manual override already moved the file; nothing to do.
                continue

            self.db.mark_job_file_processing(job_id, path_str, stage="ocr")
            processing_row = self.db.get_job_file(job_id, path_str)
            unsorted_path = (
                Path(processing_row.destination_path)
                if processing_row and processing_row.destination_path
                else file_path
            )
            if processing_row is not None:
                yield {
                    "event": "file_updated",
                    "job_id": job_id,
                    "file": processing_row.model_dump(),
                }

            outcome = self.process_file_background(
                file_path=file_path,
                unsorted_path=unsorted_path,
                source_root=source_root,
                output_root=output_root,
                threshold=job.confidence_threshold,
                template=job.folder_template,
                mode=job.file_mode,
                control=control,
            )
            if outcome is None:
                continue

            if outcome.fc.status == "sorted":
                self.db.update_job_file_result(job_id, outcome.fc)
            else:
                ai_candidates.append(outcome)
                # Keep the row marked unsorted until AI gets its chance; the
                # file is not copied anywhere yet.
                self.db.update_job_file_result(job_id, outcome.fc)

            background_done += 1
            counts = self.db.recompute_job_counts(job_id)
            yield {
                "event": "file_updated",
                "job_id": job_id,
                "processed_count": background_done,
                "total_files": total_files,
                "sorted_files": counts[0],
                "unsorted_files": counts[1],
                "queued_files": counts[2],
                "file": outcome.fc.model_dump(),
            }

        # ── Layer 3: AI fallback for OCR-unsorted files ──────────────────
        settings = load_settings()
        ai_available = bool(settings.ai_fallback_enabled and settings.gemini_api_key)

        for outcome in ai_candidates:
            if control.is_cancelled(outcome.file_path):
                continue

            fc = self._ai_fallback(
                outcome=outcome,
                control=control,
                output_root=output_root,
                template=job.folder_template,
                mode=job.file_mode,
            ) if ai_available else None

            if fc is None:
                fc = self._finalize_unsorted(
                    outcome=outcome,
                    control=control,
                    output_root=output_root,
                    template=job.folder_template,
                    mode=job.file_mode,
                    stage="ai" if ai_available else "ocr",
                )
            if fc is None:
                continue

            self.db.update_job_file_result(job_id, fc)
            counts = self.db.recompute_job_counts(job_id)
            background_done += 1
            yield {
                "event": "file_updated",
                "job_id": job_id,
                "processed_count": background_done,
                "total_files": total_files,
                "sorted_files": counts[0],
                "unsorted_files": counts[1],
                "queued_files": counts[2],
                "file": fc.model_dump(),
            }

        # ── Finish ───────────────────────────────────────────────────────
        counts = self.db.recompute_job_counts(job_id)
        duration = round(time.time() - start_time, 2)
        self.db.complete_job(
            job_id,
            sorted_count=counts[0],
            unsorted_count=counts[1],
            duration_seconds=duration,
        )
        clear_job_control(job_id)

        yield {
            "event": "job_completed",
            "job_id": job_id,
            "total_files": total_files,
            "sorted_files": counts[0],
            "unsorted_files": counts[1],
            "queued_files": 0,
            "duration_seconds": duration,
        }
