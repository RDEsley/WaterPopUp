@echo off
cd /d "%~dp0"
if exist "dist\hidratar_popup.exe" (
    start "" "dist\hidratar_popup.exe" --config
) else if exist "hidratar_popup.exe" (
    start "" "hidratar_popup.exe" --config
) else (
    python hidratar_popup.py --config
)
