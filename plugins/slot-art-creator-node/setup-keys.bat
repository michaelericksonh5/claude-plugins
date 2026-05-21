@echo off
setlocal EnableExtensions

title slot-art-creator-node - API key setup

:: Windows key setup launcher.
:: Keys are written to %USERPROFILE%\.h5g-slot-art-creator\.env, which survives
:: plugin reinstalls and is read by the MCP server at startup.

cd /d "%~dp0"
set "PS=%~dp0setup-keys.ps1"
if not exist "%PS%" set "PS=%~dp0H5G-Slot-Art-Key-Setup.ps1"
if not exist "%PS%" (
    echo.
    echo  ERROR: setup-keys.ps1 was not found next to this launcher.
    echo  You are likely on an old cached install.
    echo  Update/reinstall slot-art-creator-node v1.7.19+ from the H5G marketplace.
    echo.
    pause
    exit /b 1
)

pwsh -NoProfile -ExecutionPolicy Bypass -File "%PS%" 2>nul
if errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%PS%"
)
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
    echo  Setup complete. You can close this window and return to Claude.
) else (
    echo  Setup did not complete. Review messages above and try again.
)
echo.
pause
endlocal
exit /b %RC%
