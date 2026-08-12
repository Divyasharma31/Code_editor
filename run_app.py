import os
import sys
import subprocess

def main():
    # 1. Ensure we are running using the Virtual Environment
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(base_dir, 'venv', 'Scripts', 'python.exe')
    
    if os.path.exists(venv_python) and sys.executable != venv_python:
        print("Relaunching using the virtual environment...")
        # Re-run this script using the venv's python executable
        sys.exit(subprocess.run([venv_python, __file__] + sys.argv[1:]).returncode)

    # 2. We are now running inside the venv (or system python if venv is missing)
    try:
        import uvicorn
        import webbrowser
        import threading
        import time
    except ImportError:
        print("Required packages are missing. Please ensure you ran the setup.")
        sys.exit(1)

    def open_browser():
        # Wait a moment for the server to start before opening the browser
        time.sleep(1.5)
        print("Opening browser to http://127.0.0.1:8000/index.html ...")
        webbrowser.open("http://127.0.0.1:8000/index.html")

    # Start the browser launcher in a background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 3. Start the FastAPI server
    print("Starting CodePlatform server...")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
