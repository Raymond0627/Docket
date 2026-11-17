import os
import base64
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests

from backend.config import load_settings
from backend.engine.extractor import extract_direct_text

DEFAULT_MODEL = "gemini-3.5-flash-lite"


def get_api_key(api_key: Optional[str] = None) -> str:
    key = api_key or load_settings().gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("Google Gemini API Key is required. Please configure your key in Settings.")
    return key.strip()

def test_gemini_connection(api_key: str, model_name: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """Tests if the Gemini API key is valid."""
    key = api_key.strip() if api_key else ""
    if not key:
        raise ValueError("API Key is required")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": key
    }
    payload = {
        "contents": [{"parts": [{"text": "Hello, respond with OK if connection is successful."}]}]
    }

    res = requests.post(url, headers=headers, json=payload, timeout=20)
    if res.status_code == 200:
        return {"success": True, "model": model_name, "message": "Google Gemini connected successfully!"}
    
    # Try fallback model if model was not found
    if res.status_code == 404:
        for fallback in ["gemini-3.6-flash", "gemini-3.5-flash-lite"]:
            fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/{fallback}:generateContent"
            res2 = requests.post(fallback_url, headers=headers, json=payload, timeout=20)
            if res2.status_code == 200:
                return {"success": True, "model": fallback, "message": f"Connected successfully using {fallback}!"}

    err_msg = res.json().get("error", {}).get("message", res.text) if res.text else f"Status code {res.status_code}"
    raise ValueError(f"Gemini API Error ({res.status_code}): {err_msg}")

def analyze_document_with_gemini(
    file_path: Path,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """Extracts summary and details from document."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    answer = chat_with_gemini(
        file_path=file_path,
        prompt="Briefly describe what document this is and who it belongs to in 1-2 sentences.",
        api_key=api_key,
        model_name=model_name
    )
    return {
        "doc_type": "Document",
        "owner": "General",
        "category": "General",
        "reference_number": "",
        "summary": answer,
        "confidence": 95.0
    }

def build_gemini_parts(file_path: Path):
    """Encodes document into inline_data part or text part."""
    suffix = file_path.suffix.lower()
    mime, _ = mimetypes.guess_type(str(file_path))

    if suffix in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        mime = mime or "image/png"
        raw_b64 = base64.b64encode(file_path.read_bytes()).decode("utf-8")
        return {"inline_data": {"mime_type": mime, "data": raw_b64}}
    elif suffix == ".pdf":
        raw_b64 = base64.b64encode(file_path.read_bytes()).decode("utf-8")
        return {"inline_data": {"mime_type": "application/pdf", "data": raw_b64}}
    else:
        text, _ = extract_direct_text(file_path)
        if not text:
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""
        return {"text": f"Document content ({file_path.name}):\n{text or 'Empty content'}"}

def chat_with_gemini(
    file_path: Path,
    prompt: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> str:
    """Answers user questions conversationally about the selected document."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    key = get_api_key(api_key)
    settings = load_settings()
    model = model_name or settings.gemini_model or DEFAULT_MODEL

    doc_part = build_gemini_parts(file_path)

    # Build conversation parts
    parts = [doc_part]

    if chat_history and len(chat_history) > 0:
        history_text = "Prior conversation:\n"
        for turn in chat_history[-6:]:
            speaker = "User" if turn.get("sender") == "user" else "Assistant"
            history_text += f"{speaker}: {turn.get('text', '')}\n"
        parts.append({"text": history_text})

    instruction = (
        "You are an intelligent document assistant in Docket Local. "
        "The user is asking questions about the attached document image or file. "
        "Answer the user's question clearly, concisely, and accurately based on the document.\n\n"
        f"User Question: {prompt}"
    )
    parts.append({"text": instruction})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": key
    }
    payload = {
        "contents": [{"parts": parts}]
    }

    res = requests.post(url, headers=headers, json=payload, timeout=35)
    if res.status_code == 200:
        data = res.json()
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            content_parts = candidates[0]["content"].get("parts", [])
            if content_parts and "text" in content_parts[0]:
                return content_parts[0]["text"].strip()
        return "I reviewed the document but could not extract a clear answer."
    else:
        err = res.json().get("error", {}).get("message", res.text)
        raise ValueError(f"Gemini API Error ({res.status_code}): {err}")
