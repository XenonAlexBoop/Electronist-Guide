@echo off
REM Creates a "The Electronist's Guide" shortcut on the current user's Desktop.
setlocal
set "TARGET=%~dp0ElectronistGuide.exe"
set "SHORTCUT=%USERPROFILE%\Desktop\The Electronist's Guide.lnk"

powershell -NoProfile -Command ^
  "$s = (New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%');" ^
  "$s.TargetPath = '%TARGET%';" ^
  "$s.WorkingDirectory = '%~dp0';" ^
  "$s.IconLocation = '%TARGET%';" ^
  "$s.Save()"

echo.
echo Shortcut created on your Desktop: "The Electronist's Guide"
echo You can now launch the app from there.
pause
