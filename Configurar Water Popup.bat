@echo off
cd /d "%~dp0"
if exist "dist\waterpopup.exe" (
    start "" "dist\waterpopup.exe" --config
) else if exist "waterpopup.exe" (
    start "" "waterpopup.exe" --config
) else (
    python waterpopup.py --config
)
