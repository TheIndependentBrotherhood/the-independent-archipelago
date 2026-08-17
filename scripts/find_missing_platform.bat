@echo off
:: Archipelago — Missing Platform Finder
:: Finds all games without a platform field, scrapes the Miraheze wiki
:: infobox for each game that has a wiki URL, and opens a review interface.

cd /d "%~dp0.."

echo [Archipelago] Starting Missing Platform Finder...
echo.

python scripts/find_missing_platform.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Script failed. Make sure Python and 'requests' are installed.
    echo   Run: pip install requests
    pause
)
