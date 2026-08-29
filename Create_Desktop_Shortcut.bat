@echo off
setlocal
cd /d "%~dp0"

echo Creating a shortcut on your Desktop and in your Start Menu...

set "EXE=%cd%\ElectronistGuide.exe"
set "DESKTOP_LNK=%USERPROFILE%\Desktop\The Electronist's Guide.lnk"
set "STARTMENU_LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\The Electronist's Guide.lnk"
set "PSFILE=%TEMP%\eg_make_shortcut.ps1"

> "%PSFILE%" (
    echo $ws = New-Object -ComObject WScript.Shell
    echo foreach ^($path in @^("%DESKTOP_LNK%", "%STARTMENU_LNK%"^)^) {
    echo     $sc = $ws.CreateShortcut^($path^)
    echo     $sc.TargetPath = "%EXE%"
    echo     $sc.WorkingDirectory = "%cd%"
    echo     $sc.IconLocation = "%EXE%"
    echo     $sc.Save^(^)
    echo }
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%PSFILE%"
del "%PSFILE%" >nul 2>nul

echo.
echo Done! "The Electronist's Guide" is now on your Desktop and in your
echo Start Menu. You can delete/ignore this .bat file now - just use the
echo shortcut from now on, or double-click ElectronistGuide.exe directly.
echo.
pause
