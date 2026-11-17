import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from backend.models import Job, JobStatus, FileClassification

class DatabaseManager:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    output_path TEXT NOT NULL,
                    file_mode TEXT NOT NULL DEFAULT 'copy',
                    confidence_threshold REAL NOT NULL DEFAULT 70.0,
                    folder_template TEXT NOT NULL DEFAULT '{owner}/{doc_type}/',
                    status TEXT NOT NULL DEFAULT 'pending',
                    total_files INTEGER NOT NULL DEFAULT 0,
                    sorted_files INTEGER NOT NULL DEFAULT 0,
                    unsorted_files INTEGER NOT NULL DEFAULT 0,
                    duration_seconds REAL NOT NULL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS job_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    original_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    destination_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    is_unsorted INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT,
                    matched_keywords TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_job_files_job_id ON job_files (job_id);
            """)

    def create_job(
        self,
        source_path: str,
        output_path: str,
        mode: str = "copy",
        threshold: float = 70.0,
        template: str = "{owner}/{doc_type}/"
    ) -> Job:
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO jobs (
                    id, source_path, output_path, file_mode,
                    confidence_threshold, folder_template, status,
                    total_files, sorted_files, unsorted_files, duration_seconds,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, source_path, output_path, mode,
                threshold, template, JobStatus.PENDING.value,
                0, 0, 0, 0.0, now, now
            ))
            conn.commit()
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            return Job(
                id=row["id"],
                source_path=row["source_path"],
                output_path=row["output_path"],
                file_mode=row["file_mode"],
                confidence_threshold=row["confidence_threshold"],
                folder_template=row["folder_template"],
                status=JobStatus(row["status"]),
                total_files=row["total_files"],
                sorted_files=row["sorted_files"],
                unsorted_files=row["unsorted_files"],
                duration_seconds=row["duration_seconds"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        total_files: Optional[int] = None
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            if total_files is not None:
                conn.execute("""
                    UPDATE jobs SET status = ?, total_files = ?, updated_at = ? WHERE id = ?
                """, (status.value, total_files, now, job_id))
            else:
                conn.execute("""
                    UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?
                """, (status.value, now, job_id))
            conn.commit()

    def complete_job(
        self,
        job_id: str,
        sorted_count: int,
        unsorted_count: int,
        duration_seconds: float,
        failed: bool = False
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        status = JobStatus.FAILED if failed else JobStatus.COMPLETED
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE jobs SET
                    status = ?,
                    sorted_files = ?,
                    unsorted_files = ?,
                    duration_seconds = ?,
                    updated_at = ?
                WHERE id = ?
            """, (status.value, sorted_count, unsorted_count, duration_seconds, now, job_id))
            conn.commit()

    def add_job_file(self, job_id: str, fc: FileClassification) -> None:
        now = datetime.now(timezone.utc).isoformat()
        import json
        keywords_json = json.dumps(fc.matched_keywords)
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO job_files (
                    job_id, original_path, file_name, doc_type,
                    owner, confidence, destination_path, status,
                    is_unsorted, error_message, matched_keywords, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, fc.original_path, fc.file_name, fc.doc_type,
                fc.owner, fc.confidence, fc.destination_path, fc.status,
                1 if fc.is_unsorted else 0, fc.error_message, keywords_json, now
            ))
            conn.commit()

    def get_job_files(self, job_id: str) -> List[FileClassification]:
        import json
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM job_files WHERE job_id = ? ORDER BY id ASC",
                (job_id,)
            ).fetchall()
            results = []
            for r in rows:
                kw = json.loads(r["matched_keywords"]) if r["matched_keywords"] else []
                results.append(FileClassification(
                    original_path=r["original_path"],
                    file_name=r["file_name"],
                    doc_type=r["doc_type"],
                    owner=r["owner"],
                    confidence=r["confidence"],
                    destination_path=r["destination_path"],
                    status=r["status"],
                    is_unsorted=bool(r["is_unsorted"]),
                    error_message=r["error_message"],
                    matched_keywords=kw
                ))
            return results

    def reclassify_file(
        self,
        job_id: str,
        original_path: str,
        new_doc_type: str,
        new_owner: str,
        new_destination_path: str
    ) -> Optional[FileClassification]:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM job_files WHERE job_id = ? AND original_path = ?",
                (job_id, original_path)
            ).fetchone()
            if not row:
                return None

            was_unsorted = bool(row["is_unsorted"])

            conn.execute("""
                UPDATE job_files
                SET doc_type = ?, owner = ?, destination_path = ?, status = 'sorted', is_unsorted = 0, confidence = 100.0
                WHERE job_id = ? AND original_path = ?
            """, (new_doc_type, new_owner, new_destination_path, job_id, original_path))

            if was_unsorted:
                conn.execute("""
                    UPDATE jobs
                    SET sorted_files = sorted_files + 1,
                        unsorted_files = MAX(0, unsorted_files - 1),
                        updated_at = ?
                    WHERE id = ?
                """, (now, job_id))

            conn.commit()

        files = self.get_job_files(job_id)
        for f in files:
            if f.original_path == original_path:
                return f
        return None

    def update_job_template(self, job_id: str, new_template: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE jobs SET folder_template = ?, updated_at = ? WHERE id = ?
            """, (new_template, now, job_id))
            conn.commit()

    def update_job_file_dest(self, job_id: str, original_path: str, new_dest: str) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE job_files SET destination_path = ? WHERE job_id = ? AND original_path = ?
            """, (new_dest, job_id, original_path))
            conn.commit()
