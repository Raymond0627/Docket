# Docket Lean Core - System Design Specification

**Date:** 2026-11-13  
**Status:** Approved  
**Topic:** Local drag-and-drop OCR router with modern web/desktop interface  
**Origin:** Docket Lean Core Plan (`Docket Lean Core Plan.docx`)

---

## 1. Executive Summary & Intent

Docket Lean Core is a blazingly fast, standalone local document routing and OCR application. It allows users to drag-and-drop or select any local folder, recursively reads all files from disk without uploading to the cloud, extracts text directly or runs CPU-based OCR on scans/images, classifies documents into specific categories (with preloaded Philippine identity and corporate document rules), detects owner names, and safely organizes files into a clean directory hierarchy on disk.

### Guiding Principles
- **Lean & Focused:** Stripped of unnecessary cloud bloat, user logins, enterprise dashboards, and multi-tenant review queues.
- **CPU & Offline First:** Runs 100% locally on standard PC hardware using PyMuPDF, python-docx, openpyxl, and RapidOCR (CPU ONNX).
- **Friendly & Modern UX:** A streamlined 3-screen interface (Drop, Result, Settings) built with React, Tailwind CSS, Lucide icons, and real-time live streaming progress.
- **Phased Priority:** Focus heavily on Phase 1 (Core Local Engine + High Quality 3-Screen UI). The local REST API serves the UI now and is kept ready for Phase 2/3 ECMS integration without complicating Phase 1.

---

## 2. System Architecture

```
Docket Local/
├── backend/
│   ├── app.py                 # FastAPI backend & static file server
│   ├── config.py              # Configuration & system settings model
│   ├── database.py            # SQLite database for job history & file logs
│   ├── rules.json             # 15+ preloaded Philippine document rules
│   ├── engine/
│   │   ├── scanner.py         # Recursive disk traversal & file metadata reader
│   │   ├── extractor.py       # Direct text extraction (PDF, docx, xlsx)
│   │   ├── ocr.py             # RapidOCR CPU onnxruntime & OpenCV image pre-processing
│   │   ├── owner_detector.py  # Path hierarchy & document body owner extraction
│   │   ├── classifier.py      # Regex + RapidFuzz rule scoring engine
│   │   └── router.py          # Destination resolver & safe file copy/move operations
│   └── api/
│       ├── jobs.py            # Job trigger & status endpoints + SSE live stream
│       ├── rules.py           # Rules configuration endpoints
│       └── settings.py        # Application settings endpoints
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DropZone.tsx   # Drag & drop area + folder input picker
│   │   │   ├── LiveFeed.tsx   # Real-time streaming classification items
│   │   │   ├── ProgressBar.tsx# Animated progress bar & live performance stats
│   │   │   ├── TreeView.tsx   # Interactive folder tree preview
│   │   │   └── RuleModal.tsx  # Document rule editor modal
│   │   ├── screens/
│   │   │   ├── DropScreen.tsx # Screen 1: Drop & live sorting progress
│   │   │   ├── ResultScreen.tsx# Screen 2: Folder tree, summary metrics, actions
│   │   │   └── SettingsScreen.tsx# Screen 3: Output path, template, rule manager
│   │   ├── services/api.ts    # REST & SSE communication layer
│   │   ├── App.tsx            # Navigation & screen manager
│   │   └── main.tsx           # Entry point
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── run.bat                    # One-click Windows launcher (FastAPI + browser launch)
└── README.md
```

---

## 3. Engine Pipeline & Processing Flow

### 3.1 Ingestion & File Discovery
- Scans target folder recursively using `os.scandir` or `pathlib.Path.rglob`.
- Recognizes:
  - **Digital PDF:** `.pdf`
  - **Documents:** `.docx`, `.doc`
  - **Spreadsheets:** `.xlsx`, `.xls`
  - **Images / Scans:** `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.webp`
- Extracts relative folder hierarchy to preserve initial owner hints (e.g. `Customers/Raymond Gudito/DL.pdf` yields owner hint `Raymond Gudito`).

### 3.2 Text Extraction Strategy
1. **Digital PDF (`PyMuPDF` / `fitz`):** Extracts digital text layer directly. If page contains fewer than 20 characters of extractable text, falls back to rendering page as image (150-200 DPI) and passing to OCR.
2. **Word (`python-docx`):** Extracts text from paragraphs, tables, and headers.
3. **Excel (`openpyxl`):** Extracts string values across active sheets.
4. **Images / Scans (`RapidOCR`):**
   - Pre-processing with OpenCV (grayscale conversion, adaptive thresholding / contrast enhancement).
   - RapidOCR ONNX model runs purely on CPU for fast, highly accurate multilingual character recognition.

### 3.3 Owner Detection
- **Primary Source:** Subfolder naming conventions (e.g., immediate parent folder name or first subfolder under root).
- **Secondary Source:** Fallback to document text scanning using regex patterns for names (e.g., `Name:\s*([A-Z\s,]+)` or `Employee Name:\s*([A-Z\s,]+)`).
- **Default:** If no owner can be inferred, assigns `General` or `Unknown`.

### 3.4 Document Classification
Each document type is evaluated against a scoring function:
- **Regex Patterns:** High-weight match (e.g. Philippine Driver's License format `[A-Z]\d{2}-\d{2}-\d{6}`).
- **Required / High-Value Keywords:** Scored using `rapidfuzz.fuzz.partial_ratio` to accommodate OCR noise and slight character variations.
- **Confidence Calculation:** Normalized 0% to 100%.
- If highest matching score $\ge$ configured threshold (default: 70%), classify as that document type.
- If highest matching score $<$ threshold, classify as `Unsorted`.

### 3.5 Preloaded Philippine Document Catalog (15 Rules)
1. **PhilSys / National ID:** `Philippine Identification Card`, `Republika ng Pilipinas`, `PhilSys`
2. **Driver's License:** `Land Transportation Office`, `Driver's License`, `LTO`, `Lic. No.`
3. **UMID / SSS ID:** `Unified Multi-Purpose ID`, `Social Security System`, `CRN`, `Republic of the Philippines`
4. **Passport:** `Republic of the Philippines`, `Department of Foreign Affairs`, `PASAPORTE`
5. **Postal ID:** `Philippine Postal Corporation`, `Postal Identity Card`
6. **TIN ID / BIR:** `Bureau of Internal Revenue`, `Taxpayer Identification Number`, `TIN`
7. **PhilHealth ID:** `Philippine Health Insurance Corporation`, `PhilHealth`, `PhilHealth Identification Number`
8. **PRC ID:** `Professional Regulation Commission`, `Registration Certificate`, `Board of`
9. **Voter's ID / Certification:** `Commission on Elections`, `COMELEC`, `Voter's Identification`
10. **Payslip:** `Earnings`, `Deductions`, `Net Pay`, `Gross Pay`, `Basic Salary`, `Pay Slip`
11. **Certificate of Employment (COE):** `Certificate of Employment`, `This is to certify that`, `Employment Period`
12. **BIR Form 2316 / ITR:** `Certificate of Compensation Payment`, `Form 2316`, `BIR Form No. 2316`
13. **Billing Statement / Utility Bill:** `Electric Bill`, `Meralco`, `Maynilad`, `Water District`, `Statement of Account`
14. **Barangay Clearance:** `Barangay Clearance`, `Office of the Punong Barangay`, `Certificate of Residency`
15. **NBI Clearance:** `National Bureau of Investigation`, `NBI Clearance`, `No Derogatory Record`

### 3.6 Routing & File Operations
- **Destination Template:** Configurable pattern defaulting to:  
  `{owner}/{doc_type}/`  
  (e.g., `Customers/Raymond Gudito/Driver's License/Raymond_DL.pdf`)
- **Unsorted Fallback:**  
  `Unsorted/{owner}/` or `Unsorted/General/`
- **File Operation:** Safe Copy by default (leaves original intact); Move option configurable in Settings.
- **Name Collision Avoidance:** If a file with the same name already exists in destination, appends counter suffix (`file_1.pdf`, `file_2.pdf`).

---

## 4. User Interface Specification (3 Screens)

### 4.1 Design Philosophy
- Clean, modern, distraction-free aesthetic with generous spacing and high contrast.
- Visual feedback on every action with smooth micro-interactions.
- Instant, non-blocking responsiveness using Server-Sent Events (SSE).

### 4.2 Screen 1: Drop Screen
- **Drop Zone:**
  - Drag-and-drop target accepting folder drops.
  - Windows directory path input box with browse button.
  - Large primary button: **"Start Organizing"**.
- **Live Processing Bar:**
  - Animated progress bar showing completed / total files, percentage, and processing rate (files/sec).
- **Streaming Live Feed:**
  - Real-time card list auto-scrolling with latest files.
  - File icon, file name, detected document type pill with match %, extracted owner pill, and destination path.

### 4.3 Screen 2: Result Screen
- **Hero Metrics:**
  - Total Files Processed
  - Successfully Sorted (Green)
  - Unsorted / Flagged for Review (Amber)
  - Processing Duration
- **Interactive Tree View:**
  - Folder-and-file tree representing output directory.
  - Expand/collapse folders, view classified file details.
- **Action Toolbar:**
  - 📂 **"Open Output Folder":** Launches Windows Explorer directly to the destination path.
  - 📊 **"Export CSV Report":** Generates downloadable audit CSV.
  - 🔄 **"Process Another Folder":** Clears session and returns to Drop Screen.

### 4.4 Screen 3: Settings Screen
- **General Configuration:**
  - Output Directory input with browse button.
  - Operation Mode: Toggle between **Copy** (Default) and **Move**.
  - Confidence Threshold Slider: 0% - 100% (Default 70%).
  - Destination Folder Template String (`{owner}/{doc_type}/`).
- **Rule Manager:**
  - List of 15 preloaded Philippine document types.
  - Enable/disable toggle for each rule.
  - Keyword and regex editor modal with live tag editing.
  - Add custom document type button.

---

## 5. Storage & Persistence

1. **SQLite Database (`docket.db`):**
   - `jobs`: `id`, `source_path`, `output_path`, `total_files`, `sorted_files`, `unsorted_files`, `status`, `created_at`, `duration`
   - `job_files`: `id`, `job_id`, `original_path`, `file_name`, `doc_type`, `owner`, `confidence`, `destination_path`, `status`, `error_message`
2. **Settings & Rules File (`rules.json` / `settings.json`):**
   - Editable JSON storing rule definitions, keywords, regex patterns, and default user preferences.

---

## 6. Testing & Quality Strategy
- **Unit Tests:**
  - Text extraction tests for digital PDF, DOCX, and XLSX sample files.
  - Classifier scoring tests with exact matches, fuzzy typos, and negative/unmatched samples.
  - Owner detection tests for folder path hierarchies and text headers.
  - Path builder and collision avoidance unit tests.
- **End-to-End Simulation:**
  - Process sample directory containing mixed valid and ambiguous test documents.
  - Validate output directory structure, counts, CSV export, and Explorer open trigger.
