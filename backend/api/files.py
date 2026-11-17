import mimetypes
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/files", tags=["files"])

@router.get("/preview")
def preview_file(path: str = Query(..., description="Absolute path of the file to preview")):
    file_path = Path(path).resolve()
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    mime, _ = mimetypes.guess_type(str(file_path))
    if not mime:
        suffix = file_path.suffix.lower()
        if suffix in (".jpg", ".jpeg"):
            mime = "image/jpeg"
        elif suffix == ".png":
            mime = "image/png"
        elif suffix == ".pdf":
            mime = "application/pdf"
        elif suffix == ".txt":
            mime = "text/plain; charset=utf-8"
        else:
            mime = "application/octet-stream"

    return FileResponse(str(file_path), media_type=mime)
