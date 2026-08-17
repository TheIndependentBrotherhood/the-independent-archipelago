@echo off
:: Archipelago — Missing Twitch ID Finder
:: Finds all games without a twitchId, queries the Twitch API for suggestions,
:: and opens a review interface to validate or set them manually.

cd /d "%~dp0.."

echo [Archipelago] Starting Missing Twitch ID Finder...
echo.

python scripts/find_missing_twitch.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Script failed. Make sure Python and 'requests' are installed.
    echo   Run: pip install requests
    pause
)
