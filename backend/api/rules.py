from typing import List
from fastapi import APIRouter
from backend.models import RuleDefinition
from backend.config import load_rules, save_rules

router = APIRouter(prefix="/api/rules", tags=["rules"])

@router.get("", response_model=List[RuleDefinition])
def get_all_rules():
    return load_rules()

@router.put("", response_model=List[RuleDefinition])
def update_rules(rules: List[RuleDefinition]):
    save_rules(rules)
    return load_rules()
