"""
Standalone Desktop Launcher for Zoho Deluge Scraper & AI Assistant
Wraps Streamlit execution for PyInstaller frozen executable packaging.
"""

import os
import sys
import time
import socket
import threading
import webbrowser

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Resolve application directories
if getattr(sys, "frozen", False):
    # Running inside PyInstaller bundle
    BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    # Running in standard Python development environment
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BUNDLE_DIR

# Set working directory and sys.path so views and local modules resolve properly
os.chdir(BUNDLE_DIR)
if BUNDLE_DIR not in sys.path:
    sys.path.insert(0, BUNDLE_DIR)


def find_free_port(start_port: int = 8501, max_tries: int = 50) -> int:
    """Find the first available TCP port on localhost starting from start_port."""
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


def open_browser_when_ready(port: int, max_wait: float = 25.0):
    """Wait until the Streamlit server begins accepting connections, then open the browser."""
    url = f"http://localhost:{port}"
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                time.sleep(0.6)
                webbrowser.open(url)
                return
        except (OSError, ConnectionRefusedError):
            time.sleep(0.3)
    # If connection loop times out, open as fallback
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    """Boot the Streamlit web application programmatically."""
    app_script = os.path.join(BUNDLE_DIR, "App.py")
    if not os.path.exists(app_script):
        print(f"Error: Application script not found at {app_script}")
        sys.exit(1)

    port = find_free_port(8501)
    print(f"🚀 Initializing Zoho Deluge AI Assistant on http://localhost:{port}...")

    # Start asynchronous thread to open browser once port is ready
    browser_thread = threading.Thread(
        target=open_browser_when_ready,
        args=(port,),
        daemon=True
    )
    browser_thread.start()

    # Import Streamlit CLI inside function to ensure early path initialization
    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        app_script,
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.serverAddress=localhost",
        "--global.developmentMode=false",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--runner.magicEnabled=false",
    ]

    try:
        sys.exit(stcli.main())
    except SystemExit:
        pass
    except Exception as e:
        print(f"Fatal error running application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
