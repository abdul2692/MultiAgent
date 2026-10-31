"""
Ollama Lifecycle Manager.
Ensures the local Ollama server is active and reachable before any agent executes.
Automatically starts the local server in detached mode on Windows if not already running.
"""
import os
import sys
import time
import logging
import subprocess
import requests

logger = logging.getLogger("multi_agent.utils.ollama_manager")

def ensure_ollama_running(base_url: str = "http://127.0.0.1:11434", timeout_seconds: int = 15) -> bool:
    """
    Checks if Ollama server is running at base_url.
    If not running, attempts to start it in the background as a detached process.
    """
    # 1. Quick ping
    try:
        resp = requests.get(base_url, timeout=1.5)
        if resp.status_code == 200:
            return True
    except Exception:
        pass

    logger.info("Ollama server not active. Attempting to start in background...")

    # 2. Locate ollama executable on Windows
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
        r"C:\Program Files\Ollama\ollama.exe",
        "ollama"
    ]
    
    ollama_bin = None
    for c in candidates:
        if os.path.exists(c) or c == "ollama":
            ollama_bin = c
            break

    if not ollama_bin:
        logger.error("Could not find Ollama executable on the system.")
        return False

    try:
        creationflags = 0
        if sys.platform == "win32":
            # DETACHED_PROCESS (0x00000008) and CREATE_NO_WINDOW (0x08000000)
            creationflags = 0x00000008 | 0x08000000

        subprocess.Popen(
            [ollama_bin, "serve"],
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )

        # 3. Wait and poll until server responds
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            time.sleep(0.8)
            try:
                resp = requests.get(base_url, timeout=1.5)
                if resp.status_code == 200:
                    logger.info("Ollama server successfully started and responsive.")
                    return True
            except Exception:
                continue

    except Exception as e:
        logger.error(f"Failed to auto-start Ollama server: {e}")

    return False

if __name__ == "__main__":
    is_active = ensure_ollama_running()
    print("Ollama Server Active:", is_active)

