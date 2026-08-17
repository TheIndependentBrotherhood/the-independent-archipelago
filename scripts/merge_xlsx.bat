@echo off
:: Archipelago XLSX Import Review Tool
:: Compares the latest XLSX file with games.json and opens a review interface.
::
:: Usage:
::   Double-click this file, OR
::   run from command line: merge_xlsx.bat [path\to\file.xlsx]

cd /d "%~dp0.."

echo [Archipelago] Starting XLSX Import Review...
echo.

if "%~1"=="" (
    python scripts/merge_xlsx.py
) else (
    python scripts/merge_xlsx.py "%~1"
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Script failed. Make sure Python is installed and openpyxl is available.
    echo   Run: pip install openpyxl
    pause
)
