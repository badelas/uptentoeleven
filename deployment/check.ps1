$ErrorActionPreference = "Stop"

# ============================================================
# JiraUpgradeBaselineToolkit - Health Check
# ============================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot

$PythonPath = Join-Path `
    $ProjectRoot `
    ".venv\Scripts\python.exe"

$EnvPath = Join-Path `
    $ProjectRoot `
    ".env"

$RequirementsPath = Join-Path `
    $ProjectRoot `
    "requirements.txt"

$MainPath = Join-Path `
    $ProjectRoot `
    "main.py"

$Errors = 0


Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " JiraUpgradeBaselineToolkit - Health Check" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""


# ============================================================
# 1. ENVIRONNEMENT PYTHON
# ============================================================

if (Test-Path $PythonPath) {

    Write-Host "[OK] Environnement Python" -ForegroundColor Green

    & $PythonPath --version

    if ($LASTEXITCODE -ne 0) {

        Write-Host "[KO] Impossible d'executer Python" -ForegroundColor Red
        $Errors++
    }

} else {

    Write-Host "[KO] .venv absent" -ForegroundColor Red
    $Errors++
}


# ============================================================
# 2. FICHIER .ENV
# ============================================================

if (Test-Path $EnvPath) {

    Write-Host "[OK] Fichier .env present" -ForegroundColor Green

} else {

    Write-Host "[KO] Fichier .env absent" -ForegroundColor Red
    $Errors++
}


# ============================================================
# 3. REQUIREMENTS.TXT
# ============================================================

if (Test-Path $RequirementsPath) {

    Write-Host "[OK] requirements.txt present" -ForegroundColor Green

} else {

    Write-Host "[KO] requirements.txt absent" -ForegroundColor Red
    $Errors++
}


# ============================================================
# 4. MAIN.PY
# ============================================================

if (Test-Path $MainPath) {

    Write-Host "[OK] main.py present" -ForegroundColor Green

} else {

    Write-Host "[KO] main.py absent" -ForegroundColor Red
    $Errors++
}


# ============================================================
# 5. LECTURE DE LA CONFIGURATION
# ============================================================

if (
    (Test-Path $PythonPath) -and
    (Test-Path $EnvPath)
) {

    Write-Host ""
    Write-Host "Lecture de la configuration..."

    $PythonCode = @'
from config import Settings

s = Settings.from_env()

print("Instance           :", s.instance_name)
print("Jira URL           :", s.jira_url)
print("Target family      :", s.target_jira_family or "NON DEFINIE")
print("Target version     :", s.target_jira_version or "PATCH NON DEFINI")
print("SSL verification   :", s.verify_ssl)
'@

    Push-Location $ProjectRoot

    try {

        # Envoi du code Python via stdin
        # La sortie reste visible dans le terminal
        $PythonCode | & $PythonPath -

        $PythonExitCode = $LASTEXITCODE

        if ($PythonExitCode -eq 0) {

            Write-Host "[OK] Configuration Python valide" -ForegroundColor Green

        } else {

            Write-Host "[KO] Configuration Python invalide" -ForegroundColor Red
            $Errors++
        }

    } catch {

        Write-Host "[KO] Erreur pendant la lecture de la configuration" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red

        $Errors++

    } finally {

        Pop-Location
    }
}


# ============================================================
# 6. TEST DES IMPORTS PRINCIPAUX
# ============================================================

if (Test-Path $PythonPath) {

    Write-Host ""
    Write-Host "Verification des modules Python..."

    $ImportCode = @'
import config
import api_client
import baseline_collector
import baseline_analyzer
import readiness_analyzer
import baseline_comparator
import excel_report

print("Imports Python : OK")
'@

    Push-Location $ProjectRoot

    try {

        # Même principe : stdin vers Python
        $ImportCode | & $PythonPath -

        $PythonExitCode = $LASTEXITCODE

        if ($PythonExitCode -eq 0) {

            Write-Host "[OK] Modules Python disponibles" -ForegroundColor Green

        } else {

            Write-Host "[KO] Erreur d'import Python" -ForegroundColor Red
            $Errors++
        }

    } catch {

        Write-Host "[KO] Erreur d'import Python" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red

        $Errors++

    } finally {

        Pop-Location
    }
}


# ============================================================
# 7. DOSSIERS OUTPUT
# ============================================================

$OutputDirectories = @(
    "$ProjectRoot\output\json",
    "$ProjectRoot\output\excel",
    "$ProjectRoot\output\logs"
)

Write-Host ""
Write-Host "Verification des repertoires de sortie..."

foreach ($Directory in $OutputDirectories) {

    if (Test-Path $Directory) {

        Write-Host "[OK] $Directory" -ForegroundColor Green

    } else {

        Write-Host "[INFO] Creation : $Directory" -ForegroundColor Yellow

        New-Item `
            -ItemType Directory `
            -Path $Directory `
            -Force | Out-Null
    }
}


# ============================================================
# RESULTAT FINAL
# ============================================================

Write-Host ""
Write-Host "=================================================="


if ($Errors -eq 0) {

    Write-Host " Health Check : OK" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host ""

    exit 0

} else {

    Write-Host " Health Check : $Errors erreur(s)" -ForegroundColor Red
    Write-Host "==================================================" -ForegroundColor Red
    Write-Host ""

    exit 1
}