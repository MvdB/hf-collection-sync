@echo off
chcp 65001 > nul
setlocal

if defined HF_SYNC_PYTHON (
    set "PYEXE=%HF_SYNC_PYTHON%"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYEXE=%~dp0.venv\Scripts\python.exe"
) else (
    where python >nul 2>&1 && set "PYEXE=python"
)

if not defined PYEXE (
    echo No Python found. Create a venv with 'python -m venv .venv' next to this script,
    echo or set HF_SYNC_PYTHON to a python.exe path.
    pause
    exit /b 1
)

"%PYEXE%" "%~dp0hf_sync.py" %*
pause
