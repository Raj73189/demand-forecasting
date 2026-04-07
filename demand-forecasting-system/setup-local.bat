@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_CMD="

if not exist ".venv\Scripts\python.exe" (
  echo [setup] Creating virtual environment...
  py -3 -m venv .venv 2>nul
  if errorlevel 1 (
    python -m venv .venv
  )
  if not exist ".venv\Scripts\python.exe" (
    echo [setup] Warning: Could not create .venv, falling back to system Python.
  )
)

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m pip --version >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
  ) else (
    echo [setup] Warning: .venv exists but pip is missing. Using system Python.
  )
)

if not defined PYTHON_CMD (
  py -3 --version >nul 2>&1
  if not errorlevel 1 set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
  python --version >nul 2>&1
  if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
  echo [setup] Python was not found on PATH. Install Python 3.11+ and try again.
  exit /b 1
)

if not exist ".env" (
  if exist ".env.example" (
    copy /Y ".env.example" ".env" >nul
    echo [setup] Created .env from .env.example
  ) else (
    echo [setup] Warning: .env.example not found. Continue without .env.
  )
)

echo [setup] Installing dependencies...
if "%PYTHON_CMD%"==".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
) else (
  %PYTHON_CMD% -m pip install -r requirements.txt
)
if errorlevel 1 (
  echo [setup] Dependency installation failed with %PYTHON_CMD%.
  exit /b 1
)

echo [setup] Completed successfully.
exit /b 0
