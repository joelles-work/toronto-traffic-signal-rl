@echo off
cd /d "%~dp0"
echo Sign in to the GitHub account you want to use for your SUMO project.
echo GitHub will show a one-time code and open a browser for authorization.
echo.
"%~dp0tools\github-cli\gh.exe" auth login --hostname github.com --git-protocol https --web
echo.
echo Return to our chat when sign-in is complete. Do not share passwords or tokens.
pause
