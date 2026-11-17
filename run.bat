@echo off
title Docket - Local OCR Desktop App
if exist "dist\Docket\Docket.exe" (
    echo Launching Docket Executable...
    start "" "dist\Docket\Docket.exe"
) else (
    echo Starting Docket Desktop Application...
    python desktop.py
)
