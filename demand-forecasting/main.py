import os
import subprocess
import sys
from pathlib import Path


APP_PATH = Path(__file__).resolve().parent / "app" / "streamlit_app.py"


def main() -> int:
    if not APP_PATH.exists():
        print(f"Streamlit app not found: {"C:\\Users\\dusma\\my codes\\demand-forecasting\\app\\stremlit_app.py"}", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    port = os.environ.get("PORT", "8501")
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str("C:\\Users\\dusma\\my codes\\demand-forecasting\\app\\streamlit_app.py"),
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
