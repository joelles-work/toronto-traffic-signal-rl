@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0.venv\Scripts\sumo-gui.exe" (
    echo SUMO-GUI was not found in the project environment.
    pause
    exit /b 1
)
start "" "%~dp0.venv\Scripts\sumo-gui.exe" -c "%~dp0Eglinton_Danforth.sumocfg"
