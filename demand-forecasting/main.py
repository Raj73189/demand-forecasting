import os
import subprocess
import sys
from pathlib import Path


APP_PATH = Path(__file__).resolve().parent / "app" / "stremlit_app.py"


def main() -> int:
    if not APP_PATH.exists():
        print(f"Streamlit app not found: {APP_PATH}", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_PATH),
        "--server.headless",
        "true",
    ]
    return subprocess.call(command, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
