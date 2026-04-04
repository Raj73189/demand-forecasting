import os
import runpy
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


def _running_inside_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return False
    # Avoid noisy "missing ScriptRunContext" warnings when launched via `python main.py`.
    return get_script_run_ctx(suppress_warning=True) is not None


def main() -> int:
    if not APP_PATH.exists():
        print(f"Streamlit app not found: {APP_PATH}", file=sys.stderr)
        return 1

    # If this file is selected as the Streamlit "Main file path", render
    # the real app in the current process instead of spawning another server.
    if _running_inside_streamlit():
        runpy.run_path(str(APP_PATH), run_name="__main__")
        return 0

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
    try:
        return subprocess.call(command, env=env)
    except KeyboardInterrupt:
        # Allow Ctrl+C shutdown without printing a traceback.
        print("\nStreamlit server stopped by user.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
