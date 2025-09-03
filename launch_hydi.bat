@echo off
setlocal

:: Paths
set ZIP_PATH="C:\Users\Owner\Downloads\Hydi_Core_With_Toggles.zip"
set DEST_PATH="C:\Users\Owner\Downloads\ballsdeepnit_full_bundle\ballsdeepnit\src"
set PYTHON_SCRIPT="%DEST_PATH%\hydi_toggle_scanner.py"

:: Expand the archive
powershell -Command "Expand-Archive -Path %ZIP_PATH% -DestinationPath %DEST_PATH% -Force"

:: Run the toggle scanner
python %PYTHON_SCRIPT%

:: If successful, create a shortcut on the Desktop
if %errorlevel%==0 (
    powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\Hydi Launcher.lnk'); $s.TargetPath='%SystemRoot%\System32\cmd.exe'; $s.Arguments='/c python %PYTHON_SCRIPT%'; $s.WorkingDirectory='%DEST_PATH%'; $s.IconLocation='%SystemRoot%\System32\shell32.dll,1'; $s.Save()"
    echo Shortcut created on Desktop: Hydi Launcher.lnk
)

pause
