@echo off
setlocal

cd /d "%~dp0"

set "USE_VENV="

if not exist ".venv\Scripts\python.exe" (
  echo [start] Virtual environment not found. Running setup-local.bat first...
  call "%~dp0setup-local.bat"
  if errorlevel 1 (
    echo [start] setup-local.bat failed.
    exit /b 1
  )
)

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m pip --version >nul 2>&1
  if not errorlevel 1 set "USE_VENV=1"
)

if not exist ".env" (
  if exist ".env.example" (
    copy /Y ".env.example" ".env" >nul
    echo [start] Created .env from .env.example
  )
)

echo [start] Launching app at http://127.0.0.1:8000
if defined USE_VENV (
  ".venv\Scripts\python.exe" -m flask --app app.main:app --env-file .env run --host 0.0.0.0 --port 8000
  exit /b
)

py -3 --version >nul 2>&1
if not errorlevel 1 (
  py -3 -m flask --app app.main:app --env-file .env run --host 0.0.0.0 --port 8000
  exit /b
)

python -m flask --app app.main:app --env-file .env run --host 0.0.0.0 --port 8000
