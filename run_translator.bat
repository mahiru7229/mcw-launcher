@echo off
setlocal
chcp 65001 >nul
title MCW Launcher - Translation Studio

echo ========================================================
echo         MCW LAUNCHER - TRANSLATION STUDIO
echo ========================================================
echo Dang khoi dong bo cong cu dich thuat MCW Launcher...
echo.

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%~dp0tools\translator\translator_server.py" %*
    goto :end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" "%~dp0tools\translator\translator_server.py" %*
    goto :end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%~dp0tools\translator\translator_server.py" %*
    goto :end
)

echo [LOI] Khong tim thay Python tren he thong!
echo Vui long cai dat Python (>= 3.10) hoac lien he quan tri vien.
echo.
pause

:end
endlocal
