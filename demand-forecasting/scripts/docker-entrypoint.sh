#!/bin/sh
set -e
PORT="${PORT:-8502}"
exec streamlit run streamlit_app.py \
  --server.headless=true \
  --server.port="${PORT}" \
  --server.address=0.0.0.0 \
  --server.fileWatcherType=none
