# AGENTS.md — Docket Local

Desktop app: FastAPI backend + React frontend, packaged with PyInstaller. Not a git repo (lives inside the outer `VS code` repo).

## Layout

- `backend/` — FastAPI (PyMuPDF, RapidOCR, OpenCV), tests in `backend/tests/`
- `frontend/` — React + Vite + TypeScript + Tailwind
- `build_exe.py` — PyInstaller packaging; `build/`, `dist/` are generated output
- `docs/`, `sample_documents/`, `temp_intake/`

## Commands

```bash
# Backend (from repo root)
python start.py            # or run.bat — uvicorn on :8000
python -m pytest backend/tests/

# Frontend
cd frontend
npm run dev                # vite dev server
npm run build
```

⚠️ **No `requirements.txt`** — backend deps are only inferable from imports and README. If you add a dependency, record it (consider creating `backend/requirements.txt`).

## Conventions

- Backend changes: run `python -m pytest backend/tests/` before finishing.
- Frontend changes: `npm run build` must pass.
- Don't edit `build/`, `dist/`, `__pycache__/` — generated.
- `temp_intake/` holds runtime input; treat files there as untrusted user data (parse defensively).
