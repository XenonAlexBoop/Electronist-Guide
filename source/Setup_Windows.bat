@echo off
setlocal
cd /d "%~dp0"
title The Electronist's Guide - Setup

echo ================================================
echo   The Electronist's Guide - Windows Setup
echo ================================================
echo.
echo This will:
echo   1. Install what's needed (one time only)
echo   2. Build the app
echo   3. Put a shortcut on your Desktop and Start Menu
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on this computer.
    echo.
    echo Please install it first, then run this file again:
    echo   1. Go to https://www.python.org/downloads/
    echo   2. Run the installer
    echo   3. On the first screen, TICK "Add python.exe to PATH"
    echo   4. Finish the install, then double-click this file again
    echo.
    pause
    exit /b 1
)

echo [1/4] Installing required packages - this can take a few minutes...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo.
    echo [ERROR] Package install failed. Scroll up to see why, then try again.
    pause
    exit /b 1
)

echo.
echo [2/4] Building the app - this can take a minute or two...
python -m PyInstaller --noconfirm electronist_guide.spec
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Scroll up to see why, then try again.
    pause
    exit /b 1
)

set "EXE=%cd%\dist\ElectronistGuide\ElectronistGuide.exe"
if not exist "%EXE%" (
    echo.
    echo [ERROR] Build finished but the app wasn't found at:
    echo   %EXE%
    pause
    exit /b 1
)

echo.
echo [3/4] Creating shortcuts...
set "DESKTOP_LNK=%USERPROFILE%\Desktop\The Electronist's Guide.lnk"
set "STARTMENU_LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\The Electronist's Guide.lnk"
set "WORKDIR=%cd%\dist\ElectronistGuide"
set "ICON=%cd%\assets\icon.ico"
set "PSFILE=%TEMP%\eg_make_shortcut.ps1"

> "%PSFILE%" (
    echo $ws = New-Object -ComObject WScript.Shell
    echo foreach ^($path in @^("%DESKTOP_LNK%", "%STARTMENU_LNK%"^)^) {
    echo     $sc = $ws.CreateShortcut^($path^)
    echo     $sc.TargetPath = "%EXE%"
    echo     $sc.WorkingDirectory = "%WORKDIR%"
    echo     $sc.IconLocation = "%ICON%"
    echo     $sc.Save^(^)
    echo }
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%PSFILE%"
del "%PSFILE%" >nul 2>nul

echo.
echo [4/4] All done!
echo.
echo   - A shortcut called "The Electronist's Guide" is now on your
echo     Desktop and in your Start Menu (search "Electronist" to find it).
echo   - You will NOT need to run this setup file again - just use the
echo     shortcut from now on.
echo.
echo Launching the app now...
start "" "%EXE%"

timeout /t 5 >nul
