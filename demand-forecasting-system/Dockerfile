FROM python:3.11-slim

WORKDIR /app

COPY . .

ENV PORT=8000

RUN if [ -f requirements.txt ]; then \
      pip install --no-cache-dir -r requirements.txt; \
    elif [ -f demand-forecasting-system/requirements.txt ]; then \
      pip install --no-cache-dir -r demand-forecasting-system/requirements.txt; \
    else \
      echo "requirements.txt not found" && exit 1; \
    fi

CMD ["sh", "-c", "if [ -d demand-forecasting-system/app ]; then cd demand-forecasting-system; fi; gunicorn 'app.main:app' --bind 0.0.0.0:${PORT:-8000}"]
