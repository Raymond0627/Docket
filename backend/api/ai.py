from pathlib import Path
from typing import Optional, List, Dict
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from backend.engine.gemini_service import (
    test_gemini_connection,
    chat_with_gemini,
)
from backend.config import load_settings

router = APIRouter(prefix="/api/ai", tags=["ai"])

# ── Gemini ──────────────────────────────────────────────────────────────
class TestKeyRequest(BaseModel):
    api_key: str
    model_name: Optional[str] = "gemini-3.5-flash-lite"

class ChatDocRequest(BaseModel):
    file_path: str
    prompt: str
    chat_history: Optional[List[Dict[str, str]]] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None

# ── Glenn AI ────────────────────────────────────────────────────────────
# Glenn AI provider at https://ai.gmcdev.app
# Docs: GET / returns {"endpoints":["POST /v1/chat/completions","POST /v1/completions","GET /v1/models"],"message":"GMC Private AI Model"}
# Auth: Bearer token with key: sk-6qPerHrxi3RUFh8ZlwslCoHZdm26nZxa2nKPJdDQFbSOVYxH
# Note: /v1/models returns empty list; chat uses POST /v1/chat/completions

class GlennKeyRequest(BaseModel):
    api_key: str
    model_name: Optional[str] = "gmc"


def _glenn_chat(file_path: Path, prompt: str, api_key: str, model_name: Optional[str] = None) -> str:
    """Call Glenn AI chat completion endpoint."""
    key = api_key or load_settings().glenn_api_key
    if not key:
        raise ValueError("Glenn API key is required. Please configure it in Settings.")
    model = model_name or load_settings().glenn_model or "gmc"
    base_url = "https://ai.gmcdev.app"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096}
    try:
        resp = f"{base_url}/v1/chat/completions"
        r = requests.post(payload["messages"][0]["content"] if False else payload, headers=headers, json=payload, timeout=30)
        # The provider returned 400 "unknown provider for model gmc" in testing;
        # if we get a real answer, extract it.
        if r.status_code == 200:
            data = r.json()
            # OpenAI‑style response: choices[0].message.content
            choices = data.get("choices", [])
            if choices and choices[0].get("message"):
                return choices[0]["message"]["content"]
            # Fallback: return raw text
            return r.text
        # If provider returns 400 "unknown provider", fall back to Gemini error
        if "unknown provider" in r.text.lower():
            raise ValueError("Glenn provider model not recognised – check glenn_model setting.")
        raise ValueError(f"Glenn API error {r.status_code}: {r.text[:200]}")
    except Exception as exc:
        raise ValueError(f"Glenn chat failed: {exc}")


# ── New AI Provider ──────────────────────────────────────────────────────
# New AI provider at https://ai.gmcdev.app
# Docs: GET / returns {"endpoints":["POST /v1/chat/completions","POST /v1/completions","GET /v1/models"],"message":"GMC Private AI Model"}
# Auth: Bearer token with key: sk-gfIqeksZfQSHnVaZViPExnhQwsYYr2D7MWzH3EJnrG4itm2U
# Note: /v1/models returns empty list; chat uses POST /v1/chat/completions

class NewProviderKeyRequest(BaseModel):
    api_key: str
    model_name: Optional[str] = "gmc2"
    prompt: str


def _new_provider_chat(file_path: Path, prompt: str, api_key: str, model_name: Optional[str] = None) -> str:
    """Call New Provider AI chat completion endpoint."""
    key = api_key or load_settings().new_provider_api_key
    if not key:
        raise ValueError("New Provider API key is required. Please configure it in Settings.")
    model = model_name or load_settings().new_provider_model or "gmc2"
    base_url = "https://ai.gmcdev.app"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096}
    try:
        resp = f"{base_url}/v1/chat/completions"
        r = requests.post(payload["messages"][0]["content"] if False else payload, headers=headers, json=payload, timeout=30)
        # The provider returned 400 "unknown provider for model gmc2" in testing;
        # if we get a real answer, extract it.
        if r.status_code == 200:
            data = r.json()
            # OpenAI‑style response: choices[0].message.content
            choices = data.get("choices", [])
            if choices and choices[0].get("message"):
                return choices[0]["message"]["content"]
            # Fallback: return raw text
            return r.text
        # If provider returns 400 "unknown provider", fall back to Gemini error
        if "unknown provider" in r.text.lower():
            raise ValueError("New Provider model not recognised – check new_provider_model setting.")
        raise ValueError(f"New Provider API error {r.status_code}: {r.text[:200]}")
    except Exception as exc:
        raise ValueError(f"New Provider chat failed: {exc}")


# ── Gemini test‑key ─────────────────────────────────────────────────────
@router.post("/test-key")
def test_key(req: TestKeyRequest):
    if not req.api_key or not req.api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required")
    try:
        # Try Glenn first if key looks like Glenn's format (starts with sk-)
        if req.api_key.startswith("sk-"):
            # Quick connectivity test: hit the root endpoint
            import requests
            r = requests.get("https://ai.gmcdev.app/", headers={"Authorization": f"Bearer {req.api_key}"}, timeout=10)
            if r.status_code == 200:
                return {"success": True, "model": "glenn", "message": "Glenn AI connected successfully!"}
            # Otherwise fall back to Gemini test
        res = test_gemini_connection(api_key=req.api_key, model_name=req.model_name or "gemini-3.5-flash-lite")
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Glenn chat ──────────────────────────────────────────────────────────
@router.post("/chat")
def chat_document(req: ChatDocRequest):
    path = Path(req.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Document file not found")
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")
    try:
        # Use Glenn if key starts with sk- or if Glenn model is selected
        use_glenn = req.api_key and req.api_key.startswith("sk-") if req.api_key else False
        if use_glenn or (req.model_name and req.model_name.startswith("glenn")):
            answer = _glenn_chat(path, req.prompt, req.api_key, req.model_name)
        else:
            answer = chat_with_gemini(
                file_path=path,
                prompt=req.prompt,
                chat_history=req.chat_history,
                api_key=req.api_key,
                model_name=req.model_name,
            )
        return {"answer": answer}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI chat error: {str(e)}")


# ── New Provider chat ────────────────────────────────────────────────────
@router.post("/chat-new-provider")
def chat_new_provider(req: NewProviderKeyRequest):
    if not req.api_key or not req.api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required")
    try:
        answer = _new_provider_chat(Path("/tmp"), req.prompt, req.api_key, req.model_name)
        return {"answer": answer}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"New Provider chat error: {str(e)}")