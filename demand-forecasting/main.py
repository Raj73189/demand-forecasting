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


def _run_streamlit_with_library(app_path: Path, port: str) -> int:
    try:
        from streamlit.web import cli as stcli
    except Exception:
        return -1

    argv_backup = sys.argv[:]
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
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
        stcli.main()
        return 0
    except SystemExit as exc:
        code = exc.code
        if isinstance(code, int):
            return code
        return 0
    finally:
        sys.argv = argv_backup


def main() -> int:
    if not APP_PATH.exists():
        print(f"Streamlit app not found: {APP_PATH}", file=sys.stderr)
        return 1

    # If this file is selected as the Streamlit "Main file path", render
    # the real app in the current process instead of spawning another server.
    if _running_inside_streamlit():
        runpy.run_path(str(APP_PATH), run_name="__main__")
        return 0

    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    port = os.environ.get("PORT", "8502")
    try:
        # Prefer Streamlit's library entrypoint, fallback to subprocess if unavailable.
        lib_exit = _run_streamlit_with_library(APP_PATH, port)
        if lib_exit != -1:
            return lib_exit

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
        return subprocess.call(command, env=os.environ.copy())
    except KeyboardInterrupt:
        # Allow Ctrl+C shutdown without printing a traceback.
        print("\nStreamlit server stopped by user.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
