from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class RuleDefinition(BaseModel):
    id: str
    name: str
    category: str = "Identification"
    target_folder: str
    keywords: List[str] = Field(default_factory=list)
    regex_patterns: List[str] = Field(default_factory=list)
    min_confidence: float = 70.0
    enabled: bool = True

class ValidatedCustomer(BaseModel):
    name: str
    aliases: List[str] = Field(default_factory=list)

class AppSettings(BaseModel):
    output_path: str = "./Docket_Output"
    file_mode: str = "copy"  # "copy" or "move"
    confidence_threshold: float = 70.0
    folder_template: str = "{owner}/"
    auto_open_explorer: bool = False
    ai_fallback_enabled: bool = True
    validated_customers: List[ValidatedCustomer] = Field(default_factory=list)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-3.5-flash-lite"
    glenn_api_key: Optional[str] = None
    glenn_model: str = "gmc"
    new_provider_api_key: Optional[str] = None
    new_provider_model: str = "gmc2"
    ocr_dpi: int = 150

class JobCreate(BaseModel):
    source_path: str
    output_path: Optional[str] = None
    file_mode: Optional[str] = None
    confidence_threshold: Optional[float] = None
    folder_template: Optional[str] = None

class FileClassification(BaseModel):
    original_path: str
    file_name: str
    doc_type: str
    owner: str
    confidence: float
    destination_path: str
    # "queued" / "processing": waiting on background layers (no destination yet)
    # "sorted", "unsorted", "error": final state
    status: str = "sorted"
    is_unsorted: bool = False
    error_message: Optional[str] = None
    matched_keywords: List[str] = Field(default_factory=list)
    # Which pipeline layer produced the result: fast | ocr | ai | manual
    stage: str = "fast"

class Job(BaseModel):
    id: str
    source_path: str
    output_path: str
    file_mode: str = "copy"
    confidence_threshold: float = 70.0
    folder_template: str = "{owner}/"
    status: JobStatus = JobStatus.PENDING
    total_files: int = 0
    sorted_files: int = 0
    unsorted_files: int = 0
    queued_files: int = 0
    duration_seconds: float = 0.0
    created_at: str
    updated_at: str
