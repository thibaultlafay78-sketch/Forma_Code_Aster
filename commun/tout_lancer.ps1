# Enchaîne les 5 calculs Code_Aster, les post-traitements et le contrôle.
# Usage (depuis la racine du projet) :
#   powershell -ExecutionPolicy Bypass -File commun\tout_lancer.ps1            # tout
#   powershell -ExecutionPolicy Bypass -File commun\tout_lancer.ps1 -Depuis 4  # étapes 4 et 5 seulement
# Durée indicative : E1 30 s, E2 10 s, E3 2 min, E4 3 min, E5 11 min.
param([int]$Depuis = 1, [int]$Jusqua = 5)

$racine = Split-Path $PSScriptRoot
$py = "F:\miniforge3\envs\aster\python.exe"
$env:OPENBLAS_NUM_THREADS = "1"   # évite "OpenBLAS error: Memory allocation failed"
$env:PYTHONIOENCODING = "utf-8"
$etapes = @(
    @{n = 1; exp = "Etape1\Modèle_brochette.export";      post = @()},
    @{n = 2; exp = "Etape2\E2_modal_rayleigh.export";     post = @("Etape2\E2_post.py")},
    @{n = 3; exp = "Etape3\E3_accelerogrammes.export";    post = @("Etape3\E3_post.py")},
    @{n = 4; exp = "Etape4\E4_spectres_plancher.export";  post = @("Etape4\E4_post.py")},
    @{n = 5; exp = "Etape5\E5_colonne_1D.export";         post = @("Etape5\E5_reference_python.py", "Etape5\E5_post.py")}
)
& $py -c "import matplotlib" 2>$null
$avecFigures = ($LASTEXITCODE -eq 0)
if (-not $avecFigures) { Write-Host "matplotlib absent : calculs et contrôle seulement, pas de figures." -ForegroundColor Yellow }

Push-Location $racine
try {
    foreach ($e in $etapes) {
        if ($e.n -lt $Depuis -or $e.n -gt $Jusqua) { continue }
        $t0 = Get-Date
        Write-Host "=== Étape $($e.n) : $($e.exp)" -ForegroundColor Cyan
        & powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\lancer.ps1" $e.exp *> ".aster_tmp_E$($e.n).log"
        $mess = Get-ChildItem (Join-Path (Split-Path $e.exp) "resultats\*.mess") | Sort-Object LastWriteTime | Select-Object -Last 1
        $diag = (Select-String -Path $mess.FullName -Pattern "DIAGNOSTIC JOB : (\S+)").Matches.Groups[1].Value
        Write-Host ("    diagnostic {0}  ({1:mm\:ss})" -f $diag, ((Get-Date) - $t0))
        Remove-Item ".aster_tmp_E$($e.n).log" -ErrorAction SilentlyContinue
        if ($diag -notin @("OK", "<A>_ALARM")) {
            Write-Host "    ÉCHEC : voir $($mess.FullName)" -ForegroundColor Red
            exit 1
        }
        foreach ($s in $e.post) {
            if ($s -like "*reference_python*" -or $avecFigures) { & $py $s }
        }
    }
    Write-Host "=== Contrôle des résultats" -ForegroundColor Cyan
    & $py "commun\controle.py"
    exit $LASTEXITCODE
} finally { Pop-Location }
