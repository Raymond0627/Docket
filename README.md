# Docket — Local OCR Desktop Application

> **Docket Lean Core** is a standalone, 100% offline local Windows desktop application for automated document classification and OCR routing.

---

## How to Run as a Local Desktop Application

### Option 1: Direct Standalone Executable (No Terminal, No Browser)
You can directly run the compiled Windows binary:
```
dist\Docket\Docket.exe
```
This launches Docket in its own dedicated, native desktop application window with no browser tabs, no address bars, and no web feel.

### Option 2: One-Click Desktop Launcher
Double-click:
```bat
run.bat
```
This automatically starts the native desktop executable or native application window.

### Option 3: Rebuilding the Executable
To recompile `Docket.exe` after making custom changes:
```bash
python build_exe.py
```

---

## Native Desktop Features

- 🖥️ **Standalone Desktop Window:** Runs in an isolated desktop window (powered by Microsoft Edge WebView2 via PyWebView). No browser chrome, no bookmarks bar, no URL bar.
- 📂 **Native Windows File & Folder Dialogs:** Click the **"Browse..."** button in the Organize or Settings screens to open the standard Windows Folder Browser picker directly.
- ⚡ **Local & Offline First:** Direct disk reads without cloud upload. Runs 100% on CPU using PyMuPDF, python-docx, openpyxl, RapidOCR (ONNX), OpenCV, and RapidFuzz.
- 🇵🇭 **15 Preloaded Philippine Document Rules:**
  - PhilSys National ID, Driver's License, UMID / SSS ID, Passport, Postal ID
  - TIN ID, PhilHealth, PRC ID, Voter's ID / Certification
  - Payslips, Certificate of Employment (COE), BIR Form 2316 / ITR
  - Utility Bills (Meralco, Maynilad, Water District), Barangay Clearance, NBI Clearance
- 🎯 **Intelligent Owner Detection:** Automatically detects document owners from recursive folder names (e.g. `Customers/Juan Dela Cruz/`) with regex fallback to document headers.
- 🛡️ **Safe Routing & Collision Avoidance:** Safe Copy mode by default (never alters your original files), with optional Move mode. Automatically resolves file name collisions by appending `_1`, `_2`.
- 📦 **Unsorted Fallback:** Files below the confidence threshold (default: 70%) are cleanly routed to `Unsorted/{owner}/` without manual queue bottlenecks.
- ✨ **Friendly 3-Screen Modern UI:**
  - **Screen 1 (Organize):** Drag-and-drop zone, Windows folder picker, live progress bar, and real-time streaming feed.
  - **Screen 2 (Results):** Interactive directory tree, summary statistics, one-click *"Open in Explorer"*, and CSV audit report download.
  - **Screen 3 (Settings):** Output folder picker, Copy vs. Move toggle, sensitivity slider, folder template builder, and rule editor modal.

---

## Testing with Demo Documents

To generate a sample batch with mixed Philippine IDs, payslips, utility bills, and scans:
```bash
python backend/seed_demo.py
```
Then click **Browse...** in the Docket desktop app, select `sample_documents`, and click **"Start Organizing"**!
