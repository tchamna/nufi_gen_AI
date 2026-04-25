@echo off
setlocal

py -m pip install --upgrade pyinstaller keyboard requests

if exist "dist\NufiWindowsKeyboard.exe" del /Q "dist\NufiWindowsKeyboard.exe"
if exist "share\NufiWindowsKeyboard" rmdir /S /Q "share\NufiWindowsKeyboard"
if exist "share\Clafrica Plus.zip" del /Q "share\Clafrica Plus.zip"
if exist "share\Clafrica Plus Customizable.zip" del /Q "share\Clafrica Plus Customizable.zip"
if exist "share\Clafrica Plus Customizable" rmdir /S /Q "share\Clafrica Plus Customizable"

py -m PyInstaller --noconfirm NufiWindowsKeyboard.spec
py -m PyInstaller --noconfirm NufiWindowsKeyboardCustomizable.spec

if not exist share mkdir share
if not exist "share\Clafrica Plus" mkdir "share\Clafrica Plus"
if not exist "share\Clafrica Plus Customizable" mkdir "share\Clafrica Plus Customizable"
copy /Y "dist\Clafrica Plus.exe" "share\Clafrica Plus\Clafrica Plus.exe" >nul
copy /Y "dist\Clafrica Plus Customizable.exe" "share\Clafrica Plus Customizable\Clafrica Plus Customizable.exe" >nul

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
) > "share\Clafrica Plus\README_EN.txt"

(
echo Clafrica Plus
echo.
echo Lancement :
echo - Double-cliquez sur Clafrica Plus.exe
echo.
echo Controles :
echo - Double Maj : active/desactive
echo - 1..5 : choisit une suggestion visible
echo - Ctrl+Shift+1..5 : choisit une suggestion visible
echo - Ctrl+Alt+Q : quitter
echo.
echo Notes :
echo - L'application est packagee en mode utilisateur standard, sans invite UAC.
echo - Elle fonctionne dans les applications utilisateur normales sans droits administrateur.
echo - Windows peut bloquer l'interaction avec les applications elevees si ce clavier n'est pas lui-meme lance en mode eleve.
) > "share\Clafrica Plus\README.txt"

(
echo Clafrica Plus Customizable
echo.
echo Lancement :
echo - Double-cliquez sur Clafrica Plus Customizable.exe
echo.
echo Controles :
echo - Double Maj : active/desactive
echo - 1..5 : choisit une suggestion visible
echo - Ctrl+Shift+1..5 : choisit une suggestion visible
echo - Ctrl+Alt+S : ouvre l'editeur de raccourcis
echo - Ctrl+Alt+Q : quitter
echo.
echo Notes :
echo - L'interface demarre en francais et le bouton English permet de basculer en anglais.
echo - Les raccourcis personnalises sont stockes dans %%APPDATA%%\Clafrica Plus Customizable\custom_shortcuts.tsv
echo - Appuyez sur Ctrl+Alt+S ou cliquez sur Raccourcis pour saisir les raccourcis dans l'interface.
echo - Importer un fichier accepte les formats .csv, .tsv et .txt avec paires raccourci/remplacement.
echo - Votre liste personnalisee s'ajoute a la liste integree.
echo - Si un raccourci personnalise correspond a un raccourci integre, la valeur personnalisee le remplace.
echo - Utilisez !raccourci pour supprimer un raccourci de l'ensemble actif.
echo - L'application reste packagee en mode utilisateur standard, sans invite UAC.
echo - Windows peut bloquer l'interaction avec les applications elevees si ce clavier n'est pas lui-meme lance en mode eleve.
) > "share\Clafrica Plus Customizable\README.txt"

(
echo Clafrica Plus Customizable
echo.
echo Run:
echo - Double-click Clafrica Plus Customizable.exe
echo.
echo Controls:
echo - Double Shift: toggle ON/OFF
echo - 1..5: choose visible suggestion
echo - Ctrl+Shift+1..5: choose visible suggestion
echo - Ctrl+Alt+S: open the shortcut editor
echo - Ctrl+Alt+Q: quit
echo.
echo Notes:
echo - The interface starts in French and the English button switches the UI to English.
echo - Custom shortcuts are stored in %%APPDATA%%\Clafrica Plus Customizable\custom_shortcuts.tsv
echo - Press Ctrl+Alt+S or click Shortcuts to enter shortcuts in the interface.
echo - Import File accepts .csv, .tsv, and .txt with shortcut/replacement pairs.
echo - Your custom list is added on top of the built-in list.
echo - If a custom shortcut matches a built-in shortcut, the custom value overrides it.
echo - Use !shortcut to remove a shortcut from the active set.
echo - The packaged app stays a standard-user app with no UAC admin prompt.
echo - Windows will still block interaction with elevated apps unless this keyboard is also run elevated.
) > "share\Clafrica Plus Customizable\README_EN.txt"

powershell -NoProfile -Command "Compress-Archive -Path 'share\Clafrica Plus\*' -DestinationPath 'share\Clafrica Plus.zip'"
powershell -NoProfile -Command "Compress-Archive -Path 'share\Clafrica Plus Customizable\*' -DestinationPath 'share\Clafrica Plus Customizable.zip'"

endlocal
