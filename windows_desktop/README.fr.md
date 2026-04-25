# Clavier Windows Nufi

Cette application de bureau Windows est un agent de saisie inspire du depot `input-method` et relie au meme flux de transformation Nufi et de prediction que le clavier Android.

Ce qu'elle fait :

- fonctionne globalement dans les champs de texte Windows
- transforme les raccourcis Nufi pendant la saisie
- appelle la meme route API de prediction que sur Android : `/api/keyboard/suggest`
- affiche une petite barre de suggestions toujours au premier plan
- insere les suggestions avec `Ctrl+Shift+1` a `Ctrl+Shift+5`
- active ou desactive l'agent avec un double appui sur `Shift`
- quitte avec `Ctrl+Alt+Q`

Ce qu'elle n'est pas :

- ce n'est pas encore un IME TSF Windows natif
- ce n'est pas encore une fenetre de suggestion ancree exactement au curseur
- ce n'est pas encore une composition native Android complete dans toutes les applications

Ce compromis est volontaire. Il permet d'obtenir rapidement un agent de saisie fonctionnel a l'echelle de Windows. Si vous voulez un comportement 100 % natif dans Word, Excel, Chrome ou Google Docs, l'etape suivante sera un vrai IME Windows.

## Lancement local

Depuis la racine du depot :

```powershell
py -m pip install -r windows_desktop\requirements.txt
py windows_desktop\run_nufi_windows_keyboard.py
```

Version de bureau personnalisable :

```powershell
py windows_desktop\run_nufi_windows_keyboard_customizable.py
```

Version stable de secours :

```powershell
py windows_desktop\run_nufi_windows_keyboard_stable.py
```

Utiliser une autre URL API :

```powershell
py windows_desktop\run_nufi_windows_keyboard.py --api-base-url http://127.0.0.1:8010
```

## Notes

- L'application packagee s'execute comme un utilisateur standard et ne demande pas d'elevation UAC.
- Elle fonctionne dans les applications utilisateur normales sans droits administrateur.
- Windows peut toujours bloquer l'interaction clavier avec les applications lancees en mode eleve.
- L'interface du bureau demarre en francais et propose un bouton `English` pour basculer l'interface en anglais.
- La barre de suggestion revient sur la derniere fenetre de saisie active avant l'injection d'une suggestion.
- Le moteur de transformation charge les memes ressources que sur Android :
  - `android-keyboard/app/src/main/assets/clafrica.json`
  - `android-keyboard/app/src/main/assets/nufi_sms.json`
  - `android-keyboard/app/src/main/assets/nufi_calendar.json`
- La version personnalisable stocke les raccourcis utilisateur dans `%APPDATA%\Clafrica Plus Customizable\custom_shortcuts.tsv`.
- Dans la version personnalisable, appuyez sur `Ctrl+Alt+S` ou cliquez sur `Raccourcis` pour modifier et recharger les mappings personnalises apres installation.

## Raccourcis personnalises

La version personnalisable utilise deux couches de raccourcis :

- Les raccourcis integres a l'application sont toujours charges.
- Vos raccourcis personnalises sont ajoutes au-dessus de cette liste integree.
- Si votre fichier personnalise reutilise un raccourci deja present, votre valeur personnalisee remplace la valeur integree.
- Si votre fichier personnalise ajoute un nouveau raccourci, il est ajoute a la liste active.
- Si votre fichier personnalise contient `!raccourci`, ce raccourci est supprime de l'ensemble actif.

Le fichier de raccourcis personnalises se trouve ici :

```text
%APPDATA%\Clafrica Plus Customizable\custom_shortcuts.tsv
```

### Saisir des raccourcis directement dans l'interface

1. Lancez `Clafrica Plus Customizable`.
2. Appuyez sur `Ctrl+Alt+S` ou cliquez sur `Raccourcis`.
3. Saisissez un raccourci par ligne avec ce format :

```text
raccourci<TAB>remplacement
```

Pour supprimer un raccourci au lieu de le remplacer :

```text
!raccourci
```

Exemples :

```text
mba	mbe'
af 	ɑ
!mbk
```

4. Cliquez sur `Enregistrer et recharger`.

Notes :

- Les lignes qui commencent par `#` sont ignorees.
- Les raccourcis de phrase avec espaces sont acceptes.
- L'editeur enregistre seulement votre liste personnalisee, pas la liste integree.

### Importer depuis CSV, TSV ou texte

Le bouton `Importer un fichier` accepte les fichiers `.csv`, `.tsv` et `.txt`.

Formats pris en charge :

- CSV/TSV avec deux colonnes comme `shortcut,replacement`
- CSV/TSV avec ligne d'en-tete comme `shortcut,replacement`
- Fichiers texte au format `shortcut<TAB>replacement`
- Fichiers texte au format `shortcut=replacement`, `shortcut->replacement`, `shortcut=>replacement`, `shortcut;replacement` ou `shortcut,replacement`
- Lignes de suppression au format `!raccourci`

Comportement de l'import :

- Les raccourcis importes sont fusionnes dans la liste personnalisee actuellement visible dans l'editeur.
- Si un raccourci importe existe deja dans la liste personnalisee en cours, la valeur importee le remplace.
- Si une ligne importee est `!raccourci`, ce raccourci est marque pour suppression.
- Les raccourcis integres ne sont pas effaces par l'import sauf s'ils sont explicitement supprimes ou remplaces.
- Cliquez sur `Enregistrer et recharger` apres import pour appliquer le resultat final.

## Construire l'exe

```powershell
cd windows_desktop
.\build_exe.bat
```
