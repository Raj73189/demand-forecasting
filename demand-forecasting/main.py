import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent


def _resolve_app_path() -> Path:
    candidates = [
        ROOT_DIR / "streamlit_app.py",
        ROOT_DIR / "app" / "streamlit_app.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


APP_PATH = _resolve_app_path()


def main() -> int:
    if not APP_PATH.exists():
        print(f"Streamlit app not found: {APP_PATH}", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    port = os.environ.get("PORT", "8502")
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_PATH),
        "--server.headless",
        "true",
        "--server.address",
        "0.0.0.0",
        "--server.port",
        port,
        "--server.fileWatcherType",
        "none",
    ]
    return subprocess.call(command, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
