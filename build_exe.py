import sys
import subprocess
from pathlib import Path
import rapidocr_onnxruntime

rapidocr_dir = Path(rapidocr_onnxruntime.__file__).parent

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name", "Docket",
    "--noconsole",
    "--onedir",
    "-y",
    "--clean",
    "--add-data", "backend/rules.json;backend",
    "--add-data", "backend/static;backend/static",
    "--add-data", f"{rapidocr_dir / 'models'};rapidocr_onnxruntime/models",
    "--add-data", f"{rapidocr_dir / 'config.yaml'};rapidocr_onnxruntime",
    "--exclude-module", "tensorflow",
    "--exclude-module", "keras",
    "--exclude-module", "tensorboard",
    "--exclude-module", "torch",
    "--exclude-module", "torchvision",
    "--exclude-module", "torchaudio",
    "--exclude-module", "scipy",
    "--exclude-module", "pandas",
    "--exclude-module", "pytest",
    "--exclude-module", "IPython",
    "--exclude-module", "jupyter",
    "--exclude-module", "matplotlib",
    "--exclude-module", "sympy",
    "--hidden-import", "uvicorn.logging",
    "--hidden-import", "uvicorn.loops",
    "--hidden-import", "uvicorn.loops.auto",
    "--hidden-import", "uvicorn.protocols",
    "--hidden-import", "uvicorn.protocols.http",
    "--hidden-import", "uvicorn.protocols.http.auto",
    "--hidden-import", "webview.platforms.winforms",
    "--hidden-import", "multipart",
    "--hidden-import", "google.genai",
    "desktop.py"
]

print("Executing PyInstaller command with exclusions:")
res = subprocess.run(cmd)
if res.returncode == 0:
    print("\nSUCCESS: Docket executable created at dist/Docket/Docket.exe")
else:
    print(f"\nFAILED with returncode {res.returncode}")
    sys.exit(res.returncode)
