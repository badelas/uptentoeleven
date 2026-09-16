param(
    [ValidateSet("pre", "post", "compare", "test", "check")]
    [string]$Mode
)

$ErrorActionPreference = "Stop"

# ============================================================
# JiraUpgradeBaselineToolkit - Launcher
# ============================================================

$ProjectRoot = $PSScriptRoot

$PythonPath = Join-Path `
    $ProjectRoot `
    ".venv\Scripts\python.exe"

$InstallScript = Join-Path `
    $ProjectRoot `
    "deployment\install.ps1"

$CheckScript = Join-Path `
    $ProjectRoot `
    "deployment\check.ps1"

$EnvPath = Join-Path `
    $ProjectRoot `
    ".env"

$JsonOutputPath = Join-Path `
    $ProjectRoot `
    "output\json"


# ============================================================
# MENU
# ============================================================

function Show-Menu {

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host " JiraUpgradeBaselineToolkit" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1 - Collecte PRE Upgrade"
    Write-Host "2 - Collecte POST Upgrade"
    Write-Host "3 - Comparaison PRE / POST"
    Write-Host "4 - Tests Python"
    Write-Host "5 - Verification installation"
    Write-Host "0 - Quitter"
    Write-Host ""

    $Choice = Read-Host "Votre choix"

    switch ($Choice) {

        "1" {
            return "pre"
        }

        "2" {
            return "post"
        }

        "3" {
            return "compare"
        }

        "4" {
            return "test"
        }

        "5" {
            return "check"
        }

        "0" {
            exit 0
        }

        default {

            Write-Host ""
            Write-Host "Choix invalide." -ForegroundColor Red

            return $null
        }
    }
}


# ============================================================
# VERIFICATION INSTALLATION
# ============================================================

if (-not (Test-Path $PythonPath)) {

    Write-Host ""
    Write-Host "Environnement Python absent." -ForegroundColor Yellow
    Write-Host ""

    $Install = Read-Host `
        "Voulez-vous lancer l'installation ? (O/N)"

    if ($Install -match "^[OoYy]$") {

        & $InstallScript

        if ($LASTEXITCODE -ne 0) {

            Write-Host ""
            Write-Host "Echec de l'installation." -ForegroundColor Red

            exit 1
        }

    } else {

        exit 1
    }
}


# ============================================================
# VERIFICATION .ENV
# ============================================================

if (-not (Test-Path $EnvPath)) {

    Write-Host ""
    Write-Host "Fichier .env absent." -ForegroundColor Red
    Write-Host ""
    Write-Host "Lancez :"
    Write-Host ""
    Write-Host "   .\deployment\install.ps1" -ForegroundColor Cyan
    Write-Host ""

    exit 1
}


# ============================================================
# MENU SI AUCUN MODE FOURNI
# ============================================================

if (-not $Mode) {

    do {

        $Mode = Show-Menu

    } while (-not $Mode)
}


# ============================================================
# VERIFICATION PRE / POST AVANT COMPARE
# ============================================================

if ($Mode -eq "compare") {

    Write-Host ""
    Write-Host "Verification des baselines PRE / POST..."

    if (-not (Test-Path $JsonOutputPath)) {

        Write-Host ""
        Write-Host "[KO] Repertoire output\json absent." -ForegroundColor Red
        Write-Host ""
        Write-Host "Effectuez d'abord une collecte PRE puis POST."
        Write-Host ""

        exit 1
    }


    $PreFiles = Get-ChildItem `
        -Path $JsonOutputPath `
        -Filter "*_PRE_*.json" `
        -File `
        -ErrorAction SilentlyContinue


    $PostFiles = Get-ChildItem `
        -Path $JsonOutputPath `
        -Filter "*_POST_*.json" `
        -File `
        -ErrorAction SilentlyContinue


    if (-not $PreFiles) {

        Write-Host ""
        Write-Host "[KO] Aucune baseline PRE trouvee." -ForegroundColor Red
        Write-Host ""
        Write-Host "Lancez d'abord :"
        Write-Host ""
        Write-Host "   .\run.ps1 -Mode pre" -ForegroundColor Cyan
        Write-Host ""

        exit 1
    }


    if (-not $PostFiles) {

        Write-Host ""
        Write-Host "[KO] Aucune baseline POST trouvee." -ForegroundColor Red
        Write-Host ""
        Write-Host "La comparaison necessite :" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   PRE  -> avant upgrade"
        Write-Host "   POST -> apres upgrade"
        Write-Host ""
        Write-Host "Apres l'upgrade, lancez :" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   .\run.ps1 -Mode post" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Puis relancez la comparaison."
        Write-Host ""

        exit 1
    }


    Write-Host "[OK] Baseline PRE trouvee" -ForegroundColor Green
    Write-Host "[OK] Baseline POST trouvee" -ForegroundColor Green
}


# ============================================================
# EXECUTION
# ============================================================

Push-Location $ProjectRoot

try {

    switch ($Mode) {

        # ----------------------------------------------------
        # PRE
        # ----------------------------------------------------

        "pre" {

            Write-Host ""
            Write-Host "Collecte PRE Upgrade..." -ForegroundColor Cyan
            Write-Host ""

            & $PythonPath `
                main.py `
                --mode pre

            if ($LASTEXITCODE -ne 0) {

                Write-Host ""
                Write-Host "Collecte PRE en erreur." -ForegroundColor Red

                exit $LASTEXITCODE
            }
        }


        # ----------------------------------------------------
        # POST
        # ----------------------------------------------------

        "post" {

            Write-Host ""
            Write-Host "Collecte POST Upgrade..." -ForegroundColor Cyan
            Write-Host ""

            & $PythonPath `
                main.py `
                --mode post

            if ($LASTEXITCODE -ne 0) {

                Write-Host ""
                Write-Host "Collecte POST en erreur." -ForegroundColor Red

                exit $LASTEXITCODE
            }
        }


        # ----------------------------------------------------
        # COMPARE
        # ----------------------------------------------------

        "compare" {

            Write-Host ""
            Write-Host "Comparaison PRE / POST..." -ForegroundColor Cyan
            Write-Host ""

            & $PythonPath `
                main.py `
                --mode compare

            if ($LASTEXITCODE -ne 0) {

                Write-Host ""
                Write-Host "Comparaison en erreur." -ForegroundColor Red

                exit $LASTEXITCODE
            }
        }


        # ----------------------------------------------------
        # TESTS
        # ----------------------------------------------------

        "test" {

            Write-Host ""
            Write-Host "Tests Python..." -ForegroundColor Cyan
            Write-Host ""

            & $PythonPath `
                -m pytest

            if ($LASTEXITCODE -ne 0) {

                Write-Host ""
                Write-Host "Tests Python en erreur." -ForegroundColor Red

                exit $LASTEXITCODE
            }
        }


        # ----------------------------------------------------
        # CHECK
        # ----------------------------------------------------

        "check" {

            & $CheckScript

            if ($LASTEXITCODE -ne 0) {

                exit $LASTEXITCODE
            }
        }
    }

} finally {

    Pop-Location
}


# ============================================================
# FIN
# ============================================================

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " Operation terminee avec succes" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""