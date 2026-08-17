@echo off
:: Archipelago — Missing Wiki URL Finder
:: Finds all games without a wiki url, checks the Miraheze wiki API
:: and opens a review interface to accept or set URLs manually.

cd /d "%~dp0.."

echo [Archipelago] Starting Missing Wiki URL Finder...
echo.

python scripts/find_missing_wiki_url.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Script failed. Make sure Python and 'requests' are installed.
    echo   Run: pip install requests
    pause
)
