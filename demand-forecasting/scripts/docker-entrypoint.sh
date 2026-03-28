#!/bin/sh
set -e
PORT="${PORT:-8501}"
exec streamlit run app/stremlit_app.py \
  --server.port="${PORT}" \
  --server.address=0.0.0.0 \
  --server.fileWatcherType=none
