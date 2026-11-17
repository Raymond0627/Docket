from fastapi import APIRouter
from backend.models import AppSettings
from backend.config import load_settings, save_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("", response_model=AppSettings)
def get_settings():
    return load_settings()

@router.put("", response_model=AppSettings)
def update_settings(settings: AppSettings):
    save_settings(settings)
    return load_settings()
