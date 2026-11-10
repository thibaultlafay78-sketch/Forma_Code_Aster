# Lance un calcul Code_Aster depuis le dossier de l'étape.
# Usage : powershell -File commun\lancer.ps1 Etape1\Modèle_brochette.export
# (run_aster.bat du conda n'active pas l'environnement : on appelle son Python.)
param([Parameter(Mandatory = $true)][string]$Export)
$env_aster = "F:\miniforge3\envs\aster"
$env:CONDA_PREFIX = $env_aster
$env:PATH = "$env_aster;$env_aster\Library\bin;$env_aster\Library\mingw-w64\bin;$env_aster\Scripts;$env:PATH"
# Dossier temporaire sur E: (C: presque plein ; run_aster y crée son répertoire de travail)
$tmp = Join-Path (Split-Path $PSScriptRoot) ".aster_tmp"
New-Item -ItemType Directory -Force $tmp | Out-Null
$env:TEMP = $tmp; $env:TMP = $tmp
$chemin = Resolve-Path $Export
Push-Location (Split-Path $chemin)
try {
    & "$env_aster\python.exe" -m run_aster.run_aster_main (Split-Path $chemin -Leaf)
    exit $LASTEXITCODE
} finally { Pop-Location }
