# Demand forecasting — Streamlit
# Build: docker build -t demand-forecast .
# Run:  docker run --rm -p 8502:8502 demand-forecast

FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    DEMAND_FORECAST_TRAIN_MAX_ROWS=150000

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src/ ./src/
COPY app/ ./app/
COPY streamlit_app.py ./streamlit_app.py
COPY .streamlit/ ./.streamlit/
COPY data/raw/train_cloud_sample.csv ./data/raw/
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8502

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import os,urllib.request; p=os.environ.get('PORT','8502'); urllib.request.urlopen('http://127.0.0.1:'+p+'/')" || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
