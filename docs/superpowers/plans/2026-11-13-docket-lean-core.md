# Docket Lean Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Docket Lean Core, a standalone local drag-and-drop document classification and OCR routing application with a modern, friendly 3-screen React UI and high-throughput Python engine.

**Architecture:** A modular Python engine (PyMuPDF, python-docx, openpyxl, RapidOCR, RapidFuzz) runs local extraction and rule-based routing, managed by FastAPI with SQLite persistence and Server-Sent Events (SSE). A modern Vite + React + Tailwind CSS single-page desktop application provides a real-time, user-friendly 3-screen experience (Drop, Result, Settings).

**Tech Stack:** Python 3.14, FastAPI, Uvicorn, SQLite, PyMuPDF (fitz), python-docx, openpyxl, RapidOCR (ONNX CPU), OpenCV, RapidFuzz, React 19, TypeScript, Vite, Tailwind CSS, Lucide React.

**Spec:** `docs/superpowers/specs/2026-11-13-docket-lean-core-design.md`

## Global Constraints
- Target platform: Windows 64-bit (local offline execution on 127.0.0.1:8000).
- Zero cloud dependencies: direct file reads straight from local disk.
- CPU OCR only: RapidOCR ONNX with CPU execution provider.
- Safe Copy by default: original source files remain untouched unless explicitly configured to Move.
- Default Confidence Threshold: 70%. Below threshold routes to `Unsorted/{owner}/`.
- Preloaded rules: 15 Philippine document types stored in `backend/rules.json`.
- Simple 3 screens only: Drop Screen, Result Screen, Settings Screen.

## Review Focus
1. **Scanned PDF with no digital text:** PyMuPDF direct text yields empty string; must render page image and route through RapidOCR seamlessly without error.
2. **File name collisions in destination folder:** When copying `dl.pdf` and a `dl.pdf` already exists in target path, must safely rename to `dl_1.pdf` without overwriting.
3. **Deep nested subfolders with multiple candidate names:** Owner extraction must prioritize the closest folder name relative to root folder before falling back to document text.
4. **Corrupt or unreadable files:** Engine must not crash the batch job; record error in SQLite and route file to `Unsorted/{owner}/Corrupt/`.
5. **Special characters or whitespace in paths:** File paths containing spaces, commas, or Unicode must be handled without path traversal errors or URL-decoding failures.

---

### Task 1: Backend Foundation, Configuration & SQLite Storage

**Files:**
- Create: `backend/config.py`
- Create: `backend/database.py`
- Create: `backend/models.py`
- Create: `backend/rules.json`
- Test: `backend/tests/test_database.py`

**Interfaces:**
- Consumes: None (root task)
- Produces: `DatabaseManager` (`init_db()`, `create_job()`, `update_job_status()`, `add_job_file()`, `get_job()`, `get_job_files()`), `Settings` model, `RuleDefinition` model, `rules.json` catalog.

- [ ] **Step 1: Write failing database and model tests**
Test job creation, status updates, file logging, and retrieval of job summaries from SQLite.
- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_database.py -v` (fails: module not found)
- [ ] **Step 3: Implement `backend/models.py`, `backend/config.py`, `backend/database.py`, and `backend/rules.json`**
Define Pydantic schema for `Job`, `JobFile`, `RuleDefinition`, `AppSettings`. Implement SQLite schema in `database.py` with tables `jobs` and `job_files`. Populate `backend/rules.json` with the 15 Philippine document types.
- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_database.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add backend/config.py backend/database.py backend/models.py backend/rules.json backend/tests/test_database.py
git commit -m "feat(backend): add database, models, config, and 15 default rules"
```

---

### Task 2: Direct Text Extractor (Digital PDF, Word, Excel)

**Files:**
- Create: `backend/engine/extractor.py`
- Test: `backend/tests/test_extractor.py`

**Interfaces:**
- Consumes: `fitz` (PyMuPDF), `docx`, `openpyxl`
- Produces: `extract_direct_text(file_path: Path) -> tuple[str, bool]` where `bool` indicates whether digital text was successfully extracted (False if scanned/empty PDF).

- [ ] **Step 1: Write failing tests for direct text extraction**
Create test cases generating minimal in-memory/temp `.docx`, `.xlsx`, and digital `.pdf` files, verifying extracted string content.
- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_extractor.py -v` (fails: extractor not found)
- [ ] **Step 3: Implement `extract_direct_text` in `backend/engine/extractor.py`**
Read digital PDF using `fitz`, `.docx` using `python-docx`, and `.xlsx` using `openpyxl`. Return extracted text and a flag indicating if the text length $\ge 20$ chars.
- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_extractor.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add backend/engine/extractor.py backend/tests/test_extractor.py
git commit -m "feat(engine): add direct text extraction for pdf, docx, and xlsx"
```

---

### Task 3: OCR Pipeline for Scans and Images

**Files:**
- Create: `backend/engine/ocr.py`
- Test: `backend/tests/test_ocr.py`

**Interfaces:**
- Consumes: `rapidocr_onnxruntime`, `cv2`, `fitz`
- Produces: `extract_ocr_text(file_path: Path) -> str` and `render_pdf_page_to_image(doc: fitz.Document, page_num: int) -> np.ndarray`

- [ ] **Step 1: Write failing tests for OCR extraction**
Generate a synthetic image containing clean text "REPUBLIKA NG PILIPINAS DRIVER LICENSE" via Pillow and assert OCR detects the text.
- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_ocr.py -v` (fails: ocr module not found)
- [ ] **Step 3: Implement `backend/engine/ocr.py`**
Initialize `RapidOCR` instance. Implement image pre-processing with OpenCV (grayscale, optional contrast adjustment) and run OCR on images (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`) or rendered PDF pages.
- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_ocr.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add backend/engine/ocr.py backend/tests/test_ocr.py
git commit -m "feat(engine): add CPU RapidOCR extraction pipeline"
```

---

### Task 4: Owner Detector & Path Hierarchy Parser

**Files:**
- Create: `backend/engine/owner_detector.py`
- Test: `backend/tests/test_owner_detector.py`

**Interfaces:**
- Consumes: File path relative to scan root, extracted document text
- Produces: `detect_owner(relative_path: Path, text: str) -> str`

- [ ] **Step 1: Write failing tests for owner detection**
Test relative path extraction (e.g. `Customers/Juan Dela Cruz/ID.pdf` $\to$ `Juan Dela Cruz`), subfolder variations, and regex fallback on document text (e.g. `Name: Maria Santos`).
- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_owner_detector.py -v`
- [ ] **Step 3: Implement `backend/engine/owner_detector.py`**
Inspect path parent components. Filter out generic terms like "ID", "Scans", "Documents", "Batch". Fallback to header regex in text. Default to "General" if neither matches.
- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_owner_detector.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add backend/engine/owner_detector.py backend/tests/test_owner_detector.py
git commit -m "feat(engine): add owner detection from folder path and text"
```

---

### Task 5: Document Classifier & Rule Matcher

**Files:**
- Create: `backend/engine/classifier.py`
- Test: `backend/tests/test_classifier.py`

**Interfaces:**
- Consumes: `RuleDefinition` list from `backend/rules.json`, extracted text
- Produces: `classify_document(text: str, rules: list[RuleDefinition], threshold: float) -> ClassificationResult(doc_type: str, confidence: float, matched_keywords: list[str], is_unsorted: bool)`

- [ ] **Step 1: Write failing classification tests**
Test text samples for Philippine Driver's License, PhilSys, Payslip, and an ambiguous text sample that must fall below 70% threshold into `Unsorted`.
- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_classifier.py -v`
- [ ] **Step 3: Implement `backend/engine/classifier.py`**
Use `rapidfuzz.fuzz.partial_ratio` for fuzzy keyword scoring and `re.search` for regex patterns. Compute composite score (0-100%). Return highest scoring match.
- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_classifier.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add backend/engine/classifier.py backend/tests/test_classifier.py
git commit -m "feat(engine): add rule-based and fuzzy document classifier"
```

---

### Task 6: Destination Router & Safe File Operations

**Files:**
- Create: `backend/engine/router.py`
- Test: `backend/tests/test_router.py`

**Interfaces:**
- Consumes: `source_file: Path`, `destination_root: Path`, `owner: str`, `doc_type: str`, `template: str`, `mode: str ("copy" | "move")`
- Produces: `route_file(...) -> Path` (the destination path on disk with collision avoidance).

- [ ] **Step 1: Write failing tests for file routing**
Test file copy to formatted destination, collision handling (e.g. creating `file_1.pdf`), and `Unsorted/{owner}/` fallback routing.
- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_router.py -v`
- [ ] **Step 3: Implement `backend/engine/router.py`**
Sanitize folder names. Format path using template (or `Unsorted/{owner}/` if unsorted). Check if destination exists; if so, append `_1`, `_2` before the extension. Copy or move based on mode.
- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_router.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add backend/engine/router.py backend/tests/test_router.py
git commit -m "feat(engine): add safe file router with collision avoidance"
```

---

### Task 7: Batch Job Processor & Real-Time Event Pipeline

**Files:**
- Create: `backend/engine/processor.py`
- Test: `backend/tests/test_processor.py`

**Interfaces:**
- Consumes: Scanner, Extractor, OCR, OwnerDetector, Classifier, Router, DatabaseManager
- Produces: `JobProcessor.run_job(job_id: str, source_folder: Path, output_folder: Path, ...)` with asynchronous event generator yielding live progress dicts.

- [ ] **Step 1: Write failing test for JobProcessor**
Process a mock directory tree with 3 files (1 digital pdf, 1 docx, 1 image). Verify file results and status events emitted.
- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_processor.py -v`
- [ ] **Step 3: Implement `backend/engine/processor.py`**
Traverse input folder recursively. For each file: direct extraction $\to$ OCR if needed $\to$ owner detection $\to$ classification $\to$ routing $\to$ SQLite record $\to$ broadcast event queue.
- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_processor.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add backend/engine/processor.py backend/tests/test_processor.py
git commit -m "feat(engine): add batch job processor with live event stream"
```

---

### Task 8: FastAPI Backend Endpoints & Native System Launcher

**Files:**
- Create: `backend/app.py`
- Create: `backend/api/jobs.py`
- Create: `backend/api/rules.py`
- Create: `backend/api/settings.py`
- Test: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `JobProcessor`, `DatabaseManager`, FastAPI
- Produces: REST endpoints: `POST /api/jobs`, `GET /api/jobs/{id}`, `GET /api/jobs/{id}/stream` (SSE), `GET /api/jobs/{id}/tree`, `GET /api/jobs/{id}/csv`, `GET/PUT /api/rules`, `GET/PUT /api/settings`, `POST /api/system/open-folder`.

- [ ] **Step 1: Write failing API endpoint tests using TestClient**
Test job trigger, job status fetch, SSE connection header, settings update, and rules fetch.
- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_api.py -v`
- [ ] **Step 3: Implement `backend/app.py` and routers in `backend/api/`**
Implement FastAPI app with CORS middleware. Add SSE endpoint using `StreamingResponse`. Add `POST /api/system/open-folder` using `os.startfile` on Windows.
- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_api.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add backend/app.py backend/api/ backend/tests/test_api.py
git commit -m "feat(backend): implement FastAPI endpoints and SSE live stream"
```

---

### Task 9: Frontend Initialization, Modern Theme & API Service

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/index.css`
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/types/index.ts`
- Test: `frontend/src/services/api.test.ts`

**Interfaces:**
- Consumes: Backend REST & SSE endpoints
- Produces: Typed API client (`startJob()`, `getJob()`, `subscribeJobEvents()`, `getRules()`, `updateRules()`, `getSettings()`, `updateSettings()`, `openFolder()`).

- [ ] **Step 1: Scaffold Vite + React + Tailwind + Lucide in `frontend/`**
Configure Tailwind CSS with modern neutral/slate palette and primary indigo/violet accents. Define TypeScript types for Job, JobFile, Rule, Settings.
- [ ] **Step 2: Implement typed API client in `frontend/src/services/api.ts`**
Create fetch wrapper and EventSource SSE subscriber helper.
- [ ] **Step 3: Test API service signatures with TypeScript check and mock tests**
Run: `npm run build` or `npm test`
- [ ] **Step 4: Commit**
```bash
git add frontend/
git commit -m "feat(frontend): scaffold Vite React app with Tailwind and API client"
```

---

### Task 10: Screen 1: Drop Screen & Real-Time Live Feed

**Files:**
- Create: `frontend/src/components/DropZone.tsx`
- Create: `frontend/src/components/ProgressBar.tsx`
- Create: `frontend/src/components/LiveFeed.tsx`
- Create: `frontend/src/screens/DropScreen.tsx`
- Test: Component rendering and state tests

**Interfaces:**
- Consumes: `api.startJob`, `api.subscribeJobEvents`
- Produces: Interactive drag-and-drop dropzone, Windows path input, animated progress bar, real-time file classification cards feed.

- [ ] **Step 1: Create `DropZone.tsx`**
Support folder drag-and-drop and a direct folder path text input with instant validation.
- [ ] **Step 2: Create `ProgressBar.tsx` and `LiveFeed.tsx`**
Animated percentage bar with files/sec rate. Real-time auto-scrolling feed of processed files showing document type badge, confidence score, owner badge, and destination.
- [ ] **Step 3: Wire `DropScreen.tsx` to launch job and navigate to Result Screen upon completion**
- [ ] **Step 4: Verify build and UI interactivity**
- [ ] **Step 5: Commit**
```bash
git add frontend/src/components/ frontend/src/screens/DropScreen.tsx
git commit -m "feat(frontend): implement Drop Screen with live progress and streaming feed"
```

---

### Task 11: Screen 2: Result Screen & Interactive File Tree

**Files:**
- Create: `frontend/src/components/TreeView.tsx`
- Create: `frontend/src/screens/ResultScreen.tsx`
- Test: Component tree expansion and metric display tests

**Interfaces:**
- Consumes: `api.getJob`, `api.getJobTree`, `api.openFolder`
- Produces: Result view with summary metric cards (Sorted, Unsorted, Total Duration), interactive collapsible folder tree, "Open Output Folder" button, and CSV download.

- [ ] **Step 1: Create `TreeView.tsx`**
Collapsible directory tree with document icons, file counts per folder, and metadata modal/popover when clicking any classified file.
- [ ] **Step 2: Implement `ResultScreen.tsx`**
Display hero statistic cards (Green sorted count, Amber unsorted count, duration). Add "Open in Explorer" button that invokes `api.openFolder`, and "Download CSV Report" button.
- [ ] **Step 3: Verify build and test interaction**
- [ ] **Step 4: Commit**
```bash
git add frontend/src/components/TreeView.tsx frontend/src/screens/ResultScreen.tsx
git commit -m "feat(frontend): implement Result Screen with interactive tree and explorer action"
```

---

### Task 12: Screen 3: Settings Screen & Rule Manager

**Files:**
- Create: `frontend/src/components/RuleModal.tsx`
- Create: `frontend/src/screens/SettingsScreen.tsx`
- Test: Settings mutation tests

**Interfaces:**
- Consumes: `api.getSettings`, `api.updateSettings`, `api.getRules`, `api.updateRules`
- Produces: Configuration screen for output directory, copy vs move toggle, confidence slider, folder template builder, and 15 Philippine document rule editors.

- [ ] **Step 1: Create `RuleModal.tsx`**
Modal to edit document type name, target subfolder, keyword tags, and regex pattern.
- [ ] **Step 2: Implement `SettingsScreen.tsx`**
Cards for destination path, copy/move mode switch, confidence slider with visual color threshold, template string preview, and rule list with enable/disable toggles.
- [ ] **Step 3: Verify build and save interaction**
- [ ] **Step 4: Commit**
```bash
git add frontend/src/components/RuleModal.tsx frontend/src/screens/SettingsScreen.tsx
git commit -m "feat(frontend): implement Settings Screen and Document Rule Manager"
```

---

### Task 13: App Shell, Production Packaging & One-Click Launcher

**Files:**
- Create: `frontend/src/App.tsx`
- Create: `run.bat`
- Create: `backend/seed_demo.py`
- Create: `README.md`
- Test: Full End-to-End Test suite

**Interfaces:**
- Consumes: All backend and frontend screens
- Produces: Complete working desktop application served on `http://127.0.0.1:8000`, `run.bat` one-click launcher, and demo sample documents generator for immediate testing.

- [ ] **Step 1: Wire `frontend/src/App.tsx` with top navigation bar**
Clean navigation tabs for Drop, Results, Settings, with system status badge and dark/light accents. Build frontend bundle to `backend/static/`.
- [ ] **Step 2: Update `backend/app.py` to serve static frontend**
Serve compiled React SPA directly from FastAPI when accessed in browser.
- [ ] **Step 3: Implement `backend/seed_demo.py`**
Generate sample Philippine documents (driver's license image, digital payslip PDF, COE docx) into a test folder to allow instant user verification.
- [ ] **Step 4: Create `run.bat` and `README.md`**
One-click Windows batch file that starts FastAPI and launches the user's default browser to `http://127.0.0.1:8000`.
- [ ] **Step 5: Run end-to-end test and verify whole pipeline**
Run full test suite: `pytest` passes, frontend builds with zero errors.
- [ ] **Step 6: Commit**
```bash
git add .
git commit -m "feat: complete Docket Lean Core system and one-click launcher"
```
