@echo off
setlocal
cd /d "%~dp0"
"%~dp0.venv\Scripts\python.exe" "%~dp0watch_trained_policy.py" --algorithm PPO --training-seed 101 --flow-seed 11
pause
