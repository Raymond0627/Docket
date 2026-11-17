import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Generator, Iterable, Iterator, List
from backend.database import DatabaseManager
from backend.models import JobStatus, FileClassification, RuleDefinition
from backend.engine.extractor import extract_direct_text
from backend.engine.ocr import extract_ocr_text, extract_pdf_ocr_text
from backend.engine.owner_detector import detect_owner
from backend.engine.classifier import classify_document
from backend.engine.router import route_file

logger = logging.getLogger(__name__)


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

    def process_file(
        self,
        file_path: Path,
        source_root: Path,
        output_root: Path,
        threshold: float,
        template: str,
        mode: str
    ) -> FileClassification:
        """Processes a single document: extract -> owner -> classify -> route."""
        suffix = file_path.suffix.lower()
        text = ""
        error_msg = None

        try:
            if suffix == ".pdf":
                text, is_digital = extract_direct_text(file_path)
                if not is_digital:
                    text = extract_pdf_ocr_text(file_path)
            elif suffix in (".docx", ".doc", ".xlsx", ".xls"):
                text, _ = extract_direct_text(file_path)
            elif suffix == ".txt":
                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    text = ""
            elif suffix in IMAGE_EXTENSIONS:
                text = extract_ocr_text(file_path)
        except Exception as e:
            error_msg = str(e)
            text = ""

        try:
            rel_path = file_path.relative_to(source_root)
        except Exception:
            rel_path = Path(file_path.name)

        owner = detect_owner(rel_path, text)

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
            matched_keywords=matched_keywords
        )

    def _process_all(
        self,
        files: Iterable[Path],
        source_root: Path,
        output_root: Path,
        threshold: float,
        template: str,
        mode: str,
    ) -> Iterator[FileClassification]:
        """Processes files in parallel (bounded by max_job_workers), yielding
        results in input order so progress events stay sequential."""
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
        """Executes a batch job and yields real-time progress events."""
        job = self.db.get_job(job_id)
        if not job:
            yield {"event": "job_error", "job_id": job_id, "error": "Job not found"}
            return

        source_root = Path(job.source_path)
        output_root = Path(job.output_path)
        files = self.discover_files(source_root)
        total_files = len(files)

        self.db.update_job_status(job_id, JobStatus.PROCESSING, total_files=total_files)

        yield {
            "event": "job_started",
            "job_id": job_id,
            "total_files": total_files,
            "source_path": str(source_root),
            "output_path": str(output_root)
        }

        start_time = time.time()
        sorted_count = 0
        unsorted_count = 0

        results = self._process_all(
            files,
            source_root=source_root,
            output_root=output_root,
            threshold=job.confidence_threshold,
            template=job.folder_template,
            mode=job.file_mode,
        )

        for idx, fc in enumerate(results):

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
                "file": fc.model_dump()
            }

        duration = round(time.time() - start_time, 2)
        self.db.complete_job(job_id, sorted_count=sorted_count, unsorted_count=unsorted_count, duration_seconds=duration)

        yield {
            "event": "job_completed",
            "job_id": job_id,
            "total_files": total_files,
            "sorted_files": sorted_count,
            "unsorted_files": unsorted_count,
            "duration_seconds": duration
        }
