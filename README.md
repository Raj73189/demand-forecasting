# Demand Forecasting System

A deployable web app where users can:
- Create an account and log in
- Upload historical product demand CSV data
- Generate forecasts for:
  - next month
  - next 5 months
  - next 5 years (60 months)
- See whether high demand is likely in each horizon
- View results on a dashboard with saved runs and charts
- Download forecast reports as CSV and PDF
- Use a role-based admin dashboard to manage users and roles

## Tech Stack

- Backend: FastAPI
- Views: Jinja2 templates + Chart.js
- Forecasting: custom trend + seasonality model (pure Python)
- Auth: Session-based login with hashed passwords
- Database: SQLite by default (can switch via `DATABASE_URL`)
- Deployment: Docker-ready + `render.yaml`

## Project Structure

```text
app/
  main.py
  auth.py
  config.py
  database.py
  models.py
  forecasting.py
  exporters.py
  templates/
  static/
sample_data/
tests/
requirements.txt
Dockerfile
render.yaml
```

## Local Setup

### 1) Create virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Configure environment

```powershell
Copy-Item .env.example .env
```

Optional: edit `.env` and set a stronger `SECRET_KEY`.

### 4) Run app

```powershell
uvicorn app.main:app --reload
```

Open: `http://127.0.0.1:8000`

Recommended Python version: `3.11` to `3.13`.

## CSV Input Format

Minimum accepted columns:
- date column: `date` / `month` / `timestamp` / `ds`
- demand column: `demand` / `sales` / `quantity` / `y` / `value`

Example:

```csv
date,demand
2024-01-01,100
2024-02-01,120
2024-03-01,140
```

You can test with: `sample_data/sample_product_demand.csv`.

## Forecasting Logic

- Historical data is aggregated monthly.
- Forecast uses:
  - linear trend estimation
  - monthly seasonal adjustment (when enough historical data exists)
- High demand threshold is calculated from historical baseline and recent demand trend.
- Dashboard reports:
  - next month forecast + high-demand flag
  - next 5 months average + count of high-demand months
  - 5-year growth estimate

## Tests

```powershell
pytest
```

## Deploy

### Recommended (Free): Render + Supabase Postgres

1. Push this repo to GitHub (main branch).
2. Create a free Supabase project:
   - Open `Project Settings` -> `Database`
   - Copy the connection string and keep SSL enabled.
3. Convert DB URL for SQLAlchemy driver:
   - If Supabase gives `postgresql://...`, use `postgresql+psycopg://...`
4. In Render, create a `Web Service` from your GitHub repo:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Python version: `3.11.x`
5. Set these env vars in Render:
   - `SECRET_KEY` = long random string
   - `DATABASE_URL` = your converted Supabase URL
   - `ADMIN_EMAIL` = your login email (this account becomes admin automatically)
   - `SESSION_COOKIE_NAME` = `forecasting_session`
6. Deploy and open the Render URL.
7. Register/login using `ADMIN_EMAIL`, then open `/admin` to confirm admin access.

Why this combo:
- Render gives a free Python web service for FastAPI apps.
- Supabase free plan gives managed Postgres on a separate free tier.
- This avoids losing data from local SQLite files on free web services.

### Notes

- Free Render web services spin down on idle and can take time to wake up.
- Do not use SQLite (`sqlite:///...`) in production free hosting if you need persistent data.

### Option B: Any Docker-compatible host

```powershell
docker build -t demand-forecasting-system .
docker run -p 8000:8000 demand-forecasting-system
```
