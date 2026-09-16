param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot ".venv"
$PythonPath = Join-Path $VenvPath "Scripts\python.exe"
$EnvPath = Join-Path $ProjectRoot ".env"
$EnvExamplePath = Join-Path $ProjectRoot ".env.example"
$RequirementsPath = Join-Path $ProjectRoot "requirements.txt"
$OutputPath = Join-Path $ProjectRoot "output"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " JiraUpgradeBaselineToolkit - Installation" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------
# Vérification Python
# ------------------------------------------------------------

$SystemPython = Get-Command python -ErrorAction SilentlyContinue

if (-not $SystemPython) {
    Write-Host "ERREUR : Python n'est pas installé ou absent du PATH." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Python détecté :" -ForegroundColor Green
python --version

# ------------------------------------------------------------
# Virtual Environment
# ------------------------------------------------------------

if ((Test-Path $VenvPath) -and $Force) {
    Write-Host "Suppression de l'ancien environnement virtuel..."
    Remove-Item $VenvPath -Recurse -Force
}

if (-not (Test-Path $VenvPath)) {

    Write-Host ""
    Write-Host "Création de .venv..."

    python -m venv $VenvPath

    Write-Host "[OK] .venv créé." -ForegroundColor Green

} else {

    Write-Host "[OK] .venv existe déjà." -ForegroundColor Green
}

# ------------------------------------------------------------
# Pip
# ------------------------------------------------------------

Write-Host ""
Write-Host "Mise à jour de pip..."

& $PythonPath -m pip install --upgrade pip

# ------------------------------------------------------------
# Dépendances
# ------------------------------------------------------------

if (-not (Test-Path $RequirementsPath)) {
    Write-Host "ERREUR : requirements.txt introuvable." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Installation des dépendances..."

& $PythonPath -m pip install -r $RequirementsPath

Write-Host "[OK] Dépendances installées." -ForegroundColor Green

# ------------------------------------------------------------
# .env
# ------------------------------------------------------------

if (-not (Test-Path $EnvPath)) {

    if (-not (Test-Path $EnvExamplePath)) {
        Write-Host "ERREUR : .env.example introuvable." -ForegroundColor Red
        exit 1
    }

    Copy-Item $EnvExamplePath $EnvPath

    Write-Host ""
    Write-Host "[ACTION REQUISE] Un fichier .env a été créé." -ForegroundColor Yellow
    Write-Host "Renseignez JIRA_URL, JIRA_PAT et INSTANCE_NAME avant le premier lancement." -ForegroundColor Yellow

} else {

    Write-Host "[OK] .env existe déjà." -ForegroundColor Green
}

# ------------------------------------------------------------
# Output
# ------------------------------------------------------------

$Directories = @(
    "$OutputPath\json",
    "$OutputPath\excel",
    "$OutputPath\logs"
)

foreach ($Directory in $Directories) {

    if (-not (Test-Path $Directory)) {
        New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    }
}

Write-Host "[OK] Répertoires output créés." -ForegroundColor Green

# ------------------------------------------------------------
# Test import Python
# ------------------------------------------------------------

Write-Host ""
Write-Host "Vérification du toolkit..."

Push-Location $ProjectRoot

try {

    & $PythonPath -c "from config import Settings; print('Imports Python OK')"

} finally {

    Pop-Location
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " Installation terminée" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "1. Vérifiez le fichier .env"
Write-Host "2. Lancez ensuite :"
Write-Host ""
Write-Host "   .\run.ps1" -ForegroundColor Cyan
Write-Host ""