from __future__ import annotations

import runpy
import sys
from pathlib import Path

# Compatibility entrypoint for deployments configured with app/streamlit_app.py.
ROOT_DIR = Path(__file__).resolve().parents[1]
TARGET = ROOT_DIR / "streamlit_app.py"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

runpy.run_path(str(TARGET), run_name="__main__")
