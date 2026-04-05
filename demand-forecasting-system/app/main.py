import json
from pathlib import Path
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, func, inspect, text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app import auth, models
from app.config import get_settings
from app.database import Base, SessionLocal, engine, get_db
from app.exporters import (
    build_forecast_csv_bytes,
    build_forecast_pdf_bytes,
    make_safe_filename,
)
from app.forecasting import ForecastInputError, build_forecast, parse_history_csv

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie=settings.session_cookie_name,
    max_age=60 * 60 * 24 * 7,
    same_site="lax",
    https_only=False,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_role_column()
    _promote_configured_admin()


def _ensure_role_column() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    with engine.begin() as connection:
        if "role" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL"))
        connection.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''"))


def _promote_configured_admin() -> None:
    if not settings.admin_email:
        return
    db = SessionLocal()
    try:
        user = auth.get_user_by_email(db, settings.admin_email)
        if user is not None and user.role != "admin":
            user.role = "admin"
            db.commit()
    finally:
        db.close()


def _redirect(path: str, **query_params: str) -> RedirectResponse:
    filtered = {k: v for k, v in query_params.items() if v}
    qs = urlencode(filtered)
    url = f"{path}?{qs}" if qs else path
    return RedirectResponse(url=url, status_code=303)


def _require_user(request: Request, db: Session) -> models.User | None:
    return auth.get_current_user(request, db)


def _get_run_with_access(
    db: Session,
    current_user: models.User | None,
    run_id: int,
) -> models.ForecastRun | None:
    if not current_user:
        return None
    run = db.query(models.ForecastRun).filter(models.ForecastRun.id == run_id).first()
    if not run:
        return None
    if (run.user_id == current_user.id) is True or auth.is_admin(current_user):
        return run
    return None


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if user:
        return _redirect("/dashboard")
    return _redirect("/login")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    if _require_user(request, db):
        return _redirect("/dashboard")
    return templates.TemplateResponse(
        name="register.html",
        request=request,
        context={
            "error": request.query_params.get("error"),
            "message": request.query_params.get("message"),
            "user": None,
        },
    )


@app.post("/register")
def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if "@" not in email or "." not in email:
        return _redirect("/register", error="Please enter a valid email.")
    if len(password) < 6:
        return _redirect("/register", error="Password must be at least 6 characters.")
    if auth.get_user_by_email(db, email):
        return _redirect("/register", error="An account with this email already exists.")

    user = auth.create_user(db, email, password)
    request.session["user_id"] = user.id
    return _redirect("/dashboard", message="Account created successfully.")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    if _require_user(request, db):
        return _redirect("/dashboard")
    return templates.TemplateResponse(
        name="login.html",
        request=request,
        context={
            "error": request.query_params.get("error"),
            "message": request.query_params.get("message"),
            "user": None,
        },
    )


@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = auth.authenticate_user(db, email, password)
    if not user:
        return _redirect("/login", error="Invalid email or password.")
    request.session["user_id"] = user.id
    return _redirect("/dashboard", message="Welcome back.")


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return _redirect("/login", message="You have been logged out.")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, run_id: int | None = None, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if not user:
        return _redirect("/login", message="Please login first.")

    runs = (
        db.query(models.ForecastRun)
        .filter(models.ForecastRun.user_id == user.id)
        .order_by(desc(models.ForecastRun.created_at))
        .all()
    )

    active_run = None
    if run_id:
        active_run = (
            db.query(models.ForecastRun)
            .filter(models.ForecastRun.id == run_id, models.ForecastRun.user_id == user.id)
            .first()
        )
    if not active_run and runs:
        active_run = runs[0]

    context = {
        "user": user,
        "runs": runs,
        "active_run": active_run,
        "message": request.query_params.get("message"),
        "error": request.query_params.get("error"),
        "summary": None,
        "historical": [],
        "forecast": [],
        "chart_payload": "{}",
    }

    if active_run:
        summary = json.loads(str(active_run.summary_json))
        historical = json.loads(str(active_run.historical_json))
        forecast = json.loads(str(active_run.forecast_json))

        chart = {
            "labels": [item["date"] for item in historical + forecast],
            "historical_values": [item["demand"] for item in historical] + [None] * len(forecast),
            "forecast_values": [None] * len(historical) + [item["demand"] for item in forecast],
        }

        context.update(
            {
                "summary": summary,
                "historical": historical,
                "forecast": forecast,
                "chart_payload": json.dumps(chart),
            }
        )

    return templates.TemplateResponse(name="dashboard.html", request=request, context=context)


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    current_user = _require_user(request, db)
    if not current_user:
        return _redirect("/login", message="Please login first.")
    if not auth.is_admin(current_user):
        return _redirect("/dashboard", error="Admin access required.")

    total_users = db.query(func.count(models.User.id)).scalar() or 0
    total_forecasts = db.query(func.count(models.ForecastRun.id)).scalar() or 0
    total_admins = db.query(func.count(models.User.id)).filter(models.User.role == "admin").scalar() or 0

    users = (
        db.query(
            models.User.id,
            models.User.email,
            models.User.role,
            models.User.created_at,
            func.count(models.ForecastRun.id).label("forecast_count"),
        )
        .outerjoin(models.ForecastRun, models.ForecastRun.user_id == models.User.id)
        .group_by(models.User.id, models.User.email, models.User.role, models.User.created_at)
        .order_by(desc(models.User.created_at))
        .all()
    )

    recent_runs = (
        db.query(
            models.ForecastRun.id,
            models.ForecastRun.product_name,
            models.ForecastRun.input_points,
            models.ForecastRun.created_at,
            models.User.email.label("user_email"),
        )
        .join(models.User, models.User.id == models.ForecastRun.user_id)
        .order_by(desc(models.ForecastRun.created_at))
        .limit(20)
        .all()
    )

    return templates.TemplateResponse(
        name="admin.html",
        request=request,
        context={
            "user": current_user,
            "users": users,
            "recent_runs": recent_runs,
            "total_users": total_users,
            "total_forecasts": total_forecasts,
            "total_admins": total_admins,
            "message": request.query_params.get("message"),
            "error": request.query_params.get("error"),
        },
    )


@app.post("/admin/users/{user_id}/role")
def update_user_role(
    user_id: int,
    request: Request,
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    current_user = _require_user(request, db)
    if not current_user:
        return _redirect("/login", message="Please login first.")
    if not auth.is_admin(current_user):
        return _redirect("/dashboard", error="Admin access required.")

    normalized_role = role.strip().lower()
    if normalized_role not in {"user", "admin"}:
        return _redirect("/admin", error="Invalid role.")

    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not target_user:
        return _redirect("/admin", error="User not found.")

    if current_user.id == target_user.id and normalized_role != "admin":
        return _redirect("/admin", error="You cannot remove your own admin role.")

    if normalized_role == "user" and target_user.role == "admin":
        total_admins = db.query(func.count(models.User.id)).filter(models.User.role == "admin").scalar() or 0
        if total_admins <= 1:
            return _redirect("/admin", error="At least one admin account is required.")

    target_user.role = normalized_role
    db.commit()
    return _redirect("/admin", message=f"Role updated for {target_user.email}.")


@app.post("/forecast")
async def create_forecast(
    request: Request,
    product_name: str = Form(...),
    history_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = _require_user(request, db)
    if not user:
        return _redirect("/login", message="Please login first.")

    if not product_name.strip():
        return _redirect("/dashboard", error="Product name is required.")

    try:
        file_content = await history_file.read()
        monthly = parse_history_csv(file_content)
        result = build_forecast(monthly, horizon_months=60)
    except ForecastInputError as exc:
        return _redirect("/dashboard", error=str(exc))
    except Exception:
        return _redirect("/dashboard", error="Forecasting failed. Please review your data and try again.")

    run = models.ForecastRun(
        user_id=user.id,
        product_name=product_name.strip(),
        input_points=len(result["historical"]),
        historical_json=json.dumps(result["historical"]),
        forecast_json=json.dumps(result["forecast"]),
        summary_json=json.dumps(result["summary"]),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    return _redirect("/dashboard", run_id=str(run.id), message=f"Forecast generated for {product_name.strip()}.")


@app.get("/api/forecast/{run_id}")
def forecast_api(run_id: int, request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Authentication required."})

    run = _get_run_with_access(db, user, run_id)
    if not run:
        return JSONResponse(status_code=404, content={"error": "Forecast run not found."})

    return {
        "id": run.id,
        "product_name": run.product_name,
        "input_points": run.input_points,
        "summary": json.loads(run.summary_json),
        "historical": json.loads(run.historical_json),
        "forecast": json.loads(run.forecast_json),
        "created_at": run.created_at.isoformat() if run.created_at is not None else None,
    }


@app.get("/export/forecast/{run_id}.csv")
def export_forecast_csv(run_id: int, request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if not user:
        return _redirect("/login", message="Please login first.")

    run = _get_run_with_access(db, user, run_id)
    if not run:
        return _redirect("/dashboard", error="Forecast run not found.")

    historical = json.loads(str(run.historical_json))
    forecast = json.loads(str(run.forecast_json))
    summary = json.loads(str(run.summary_json))
    created_at = run.created_at.isoformat() if run.created_at is not None else None

    csv_bytes = build_forecast_csv_bytes(
        product_name=run.product_name,
        historical=historical,
        forecast=forecast,
        summary=summary,
        created_at=created_at,
    )
    filename = make_safe_filename(f"{run.product_name}_forecast_{run.id}.csv")

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/export/forecast/{run_id}.pdf")
def export_forecast_pdf(run_id: int, request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if not user:
        return _redirect("/login", message="Please login first.")

    run = _get_run_with_access(db, user, run_id)
    if not run:
        return _redirect("/dashboard", error="Forecast run not found.")

    historical = json.loads(str(run.historical_json))
    forecast = json.loads(str(run.forecast_json))
    summary = json.loads(str(run.summary_json))
    created_at = run.created_at.isoformat() if run.created_at else None

    pdf_bytes = build_forecast_pdf_bytes(
        product_name=run.product_name,
        historical=historical,
        forecast=forecast,
        summary=summary,
        created_at=created_at,
    )
    filename = make_safe_filename(f"{run.product_name}_forecast_{run.id}.pdf")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
