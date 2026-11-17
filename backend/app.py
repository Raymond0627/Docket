from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.jobs import router as jobs_router
from backend.api.rules import router as rules_router
from backend.api.settings import router as settings_router
from backend.api.system import router as system_router
from backend.api.files import router as files_router
from backend.api.ai import router as ai_router
from backend.database import DatabaseManager
from backend.config import DB_FILE

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = DatabaseManager(DB_FILE)
    db.init_db()
    yield

app = FastAPI(title="Docket Lean Core", version="1.0.0", lifespan=lifespan)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(jobs_router)
app.include_router(rules_router)
app.include_router(settings_router)
app.include_router(system_router)
app.include_router(files_router)
app.include_router(ai_router)

# Mount static frontend build if it exists
from backend.config import RESOURCE_DIR
STATIC_DIR = RESOURCE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend_spa(full_path: str):
        file_candidate = STATIC_DIR / full_path
        if file_candidate.is_file():
            return FileResponse(file_candidate)
        return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "Docket Lean Core"}
