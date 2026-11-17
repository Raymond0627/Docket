from fastapi import APIRouter
from backend.models import AppSettings, ValidatedCustomer
from typing import List
from backend.config import load_settings, save_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("", response_model=AppSettings)
def get_settings():
    return load_settings()

@router.put("", response_model=AppSettings)
def update_settings(settings: AppSettings):
    save_settings(settings)
    return load_settings()

@router.get("/validated-customers", response_model=List[ValidatedCustomer])
def get_validated_customers():
    settings = load_settings()
    return settings.validated_customers

@router.put("/validated-customers", response_model=AppSettings)
def update_validated_customers(customers: List[ValidatedCustomer]):
    settings = load_settings()
    settings.validated_customers = customers
    save_settings(settings)
    return load_settings()
