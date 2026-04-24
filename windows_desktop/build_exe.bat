@echo off
setlocal

py -m pip install --upgrade pyinstaller keyboard requests

if exist "dist\NufiWindowsKeyboard.exe" del /Q "dist\NufiWindowsKeyboard.exe"
if exist "share\NufiWindowsKeyboard" rmdir /S /Q "share\NufiWindowsKeyboard"
if exist "share\Clafrica Plus.zip" del /Q "share\Clafrica Plus.zip"

py -m PyInstaller --noconfirm NufiWindowsKeyboard.spec

if not exist share mkdir share
if not exist "share\Clafrica Plus" mkdir "share\Clafrica Plus"
copy /Y "dist\Clafrica Plus.exe" "share\Clafrica Plus\Clafrica Plus.exe" >nul

(
echo Clafrica Plus
echo.
echo Run:
echo - Double-click Clafrica Plus.exe
echo.
echo Controls:
echo - Double Shift: toggle ON/OFF
echo - 1..5: choose visible suggestion
echo - Ctrl+Shift+1..5: choose visible suggestion
echo - Ctrl+Alt+Q: quit
echo.
echo Notes:
echo - Packaged as a standard-user app with no UAC admin prompt.
echo - It can type into normal user-level apps without corporate admin rights.
echo - Windows will still block interaction with elevated apps unless this keyboard is also run elevated.
) > "share\Clafrica Plus\README.txt"

powershell -NoProfile -Command "Compress-Archive -Path 'share\Clafrica Plus\*' -DestinationPath 'share\Clafrica Plus.zip'"

endlocal
