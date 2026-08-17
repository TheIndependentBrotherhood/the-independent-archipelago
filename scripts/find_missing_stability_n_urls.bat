@echo off
:: Archipelago — Missing Stability and URLs Finder
:: Finds all games without a stability field or missing all URLs,
:: and opens a local web interface for review and updates.

cd /d "%~dp0.."

echo [Archipelago] Starting Missing Stability and URLs Finder...
echo.

python scripts/find_missing_stability_n_urls.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Script failed. Make sure Python is installed and added to your PATH.
    pause
)