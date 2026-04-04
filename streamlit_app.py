from __future__ import annotations

import runpy
import sys
from pathlib import Path

# Compatibility launcher: repo root -> demand-forecasting app entrypoint.
ROOT_DIR = Path(__file__).resolve().parent
TARGET = ROOT_DIR / "demand-forecasting" / "streamlit_app.py"

if not TARGET.is_file():
    raise FileNotFoundError(f"Could not find app entrypoint: {TARGET}")

if str(TARGET.parent) not in sys.path:
    sys.path.insert(0, str(TARGET.parent))

runpy.run_path(str(TARGET), run_name="__main__")
