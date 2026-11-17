import sys
import time
import socket
import threading
import urllib.request
import uvicorn
import webview
from backend.app import app

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

PORT = 8000

def wait_for_server(port: int, timeout: float = 10.0):
    start = time.time()
    url = f"http://127.0.0.1:{port}/api/health"
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as res:
                if res.status == 200:
                    return True
        except Exception:
            time.sleep(0.1)
    return False

def start_backend(port: int):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

class DesktopApi:
    def choose_folder(self):
        window = webview.active_window()
        if window:
            res = window.create_file_dialog(webview.FOLDER_DIALOG)
            if res and len(res) > 0:
                return res[0]
        return None

def main():
    global PORT
    try:
        # Check if 8000 is open
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 8000))
    except Exception:
        PORT = find_free_port()

    # Start FastAPI backend in background thread
    server_thread = threading.Thread(target=start_backend, args=(PORT,), daemon=True)
    server_thread.start()

    # Wait for server to become ready
    wait_for_server(PORT)

    api = DesktopApi()
    window = webview.create_window(
        title="Docket — Local OCR & Document Router",
        url=f"http://127.0.0.1:{PORT}",
        width=1280,
        height=850,
        min_size=(960, 640),
        js_api=api,
        text_select=True,
    )

    webview.start()
    sys.exit(0)

if __name__ == "__main__":
    if "--ocr-worker" in sys.argv:
        # Watchdog worker mode (see backend/engine/ocr.py) — no GUI/server.
        from backend.engine.ocr_worker import main as _ocr_worker_main
        _ocr_worker_main()
        sys.exit(0)
    main()
