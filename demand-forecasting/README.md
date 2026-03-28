# Demand forecasting

Streamlit app for demand history, trend/seasonality decomposition, backtests (SARIMAX / Prophet), and forward forecasts.

## Run locally

```bash
pip install -r requirements.txt
python main.py
```

Optional: load only the first N rows of `data/raw/train.csv` (faster iteration):

```bash
# PowerShell
$env:DEMAND_FORECAST_TRAIN_MAX_ROWS="100000"
python main.py
```

## Deploy with Docker

From the project root (`data/raw/` should include at least `train_cloud_sample.csv` or `train.csv`):

```bash
docker build -t demand-forecast .
docker run --rm -p 8501:8501 demand-forecast
```

Open `http://localhost:8501`.

- Default image env: `DEMAND_FORECAST_TRAIN_MAX_ROWS=150000` to limit memory use. Override: `-e DEMAND_FORECAST_TRAIN_MAX_ROWS=500000` or unset by passing `-e DEMAND_FORECAST_TRAIN_MAX_ROWS=` (empty may not clear — use a custom env file or rebuild without the default in `Dockerfile` if you need the full file).
- **Platforms that set `PORT` (Railway, Render, Fly):** the entrypoint reads `PORT` and binds Streamlit to it; map the platform’s HTTP port to that process port as usual.

Mount a different training CSV (same schema as Rossmann `train.csv`):

```bash
docker run --rm -p 8501:8501 -v C:/path/to/train.csv:/app/data/raw/train.csv:ro demand-forecast
```

## Streamlit Community Cloud

Deploy at [share.streamlit.io](https://share.streamlit.io) (sign in with GitHub).

### 1. Repo checklist

- **`requirements.txt`** at the repo root (used for `pip install`).
- **`packages.txt`** at the repo root: `build-essential` helps **Prophet** install. If the build still fails, remove the `prophet` line from `requirements.txt` and use **SARIMAX** only in the app.
- **Data:** commit **`data/raw/train_cloud_sample.csv`** (~50k rows, ~1.6 MB) so the app runs on Cloud without the full Rossmann file. If you also commit `data/raw/train.csv`, the app uses **`train.csv` first** unless you override (see Secrets). Regenerate the sample with: `python scripts/build_cloud_sample.py` (needs the full `train.csv` locally).
- **Main file path** (in the deploy dialog): **`app/stremlit_app.py`**

### 2. Secrets (recommended)

In the app on Cloud: **⚙️ Settings → Secrets**. Example:

```toml
DEMAND_FORECAST_DATA_FILE = "train_cloud_sample.csv"
DEMAND_FORECAST_TRAIN_MAX_ROWS = "50000"
```

Use `DEMAND_FORECAST_DATA_FILE` when both `train.csv` and `train_cloud_sample.csv` exist in the repo and you want Cloud to use the smaller file. `DEMAND_FORECAST_TRAIN_MAX_ROWS` caps how many rows are read from whichever file is chosen (omit it if the sample alone is small enough).

### 3. Deploy

1. Push this project to a **public** GitHub repo (or connect a private repo if your Streamlit plan allows it).
2. **Create app** → pick the repo, branch, and main file **`app/stremlit_app.py`**.
3. Save **Secrets** as above, then **Reboot** the app if it already ran once.

### 4. Troubleshooting

| Issue | What to try |
|--------|-------------|
| Install fails on `prophet` | Remove `prophet` from `requirements.txt`, redeploy, use SARIMAX. |
| App crashes / OOM | Lower `DEMAND_FORECAST_TRAIN_MAX_ROWS` in Secrets or commit a smaller `train.csv`. |
| “Data file not found” | Commit **`data/raw/train_cloud_sample.csv`** (or `train.csv`). |

## Environment variables

| Variable | Purpose |
|----------|---------|
| `DEMAND_FORECAST_DATA_FILE` | Filename under `data/raw/` (e.g. `train_cloud_sample.csv`). Overrides default resolution. |
| `DEMAND_FORECAST_TRAIN_MAX_ROWS` | Read only the first N rows of the chosen file (demos / memory limits). |
| `PORT` | Used by the Docker entrypoint on PaaS (defaults to `8501`). |
