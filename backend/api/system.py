import os
import sys
import subprocess
from pathlib import Path
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/system", tags=["system"])

class OpenFolderRequest(BaseModel):
    folder_path: str

@router.post("/open-folder")
def open_folder(req: OpenFolderRequest):
    try:
        path = Path(req.folder_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Folder does not exist")
        resolved = path.resolve()
    except (OSError, ValueError):
        raise HTTPException(status_code=404, detail="Folder does not exist")

    try:
        if sys.platform == "win32":
            os.startfile(str(resolved))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(resolved)])
        else:
            subprocess.run(["xdg-open", str(resolved)])
        return {"success": True, "path": str(resolved)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/select-folder")
def select_folder():
    """Opens a native OS folder selection dialog and returns the selected path."""
    selected_path = ""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        selected_path = filedialog.askdirectory(title="Select Documents Folder")
        root.destroy()
    except Exception as e:
        # Fallback to PowerShell FolderBrowserDialog on Windows
        if sys.platform == "win32":
            cmd = (
                "[System.Reflection.Assembly]::LoadWithPartialName('System.windows.forms') | Out-Null; "
                "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
                "$dialog.Description = 'Select Documents Folder'; "
                "if ($dialog.ShowDialog() -eq 'OK') { Write-Output $dialog.SelectedPath }"
            )
            res = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
            selected_path = res.stdout.strip()

    return {"selected_path": selected_path}
