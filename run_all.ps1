param(
    [switch]$InstallDependencies,
    [switch]$VerifyOnly,
    [string]$PythonPath = ""
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $PackageRoot ".venv"
$VenvPython = if ($PythonPath) {
    (Resolve-Path -LiteralPath $PythonPath).Path
}
else {
    Join-Path $VenvDir "Scripts\python.exe"
}
$Requirements = Join-Path $PackageRoot "requirements.txt"

function Invoke-PythonStep {
    param(
        [string]$Label,
        [string]$ScriptPath
    )
    Write-Host "`n=== $Label ===" -ForegroundColor Cyan
    & $VenvPython $ScriptPath
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

if (-not $PythonPath -and -not (Test-Path -LiteralPath $VenvPython)) {
    $Launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $Launcher) {
        Write-Host "Creating local virtual environment with py..." -ForegroundColor Cyan
        & $Launcher.Source -3 -m venv $VenvDir
    }
    else {
        $Launcher = Get-Command python -ErrorAction SilentlyContinue
        if ($null -eq $Launcher) {
            throw "Python was not found. Install 64-bit Python 3.11-3.13 and try again."
        }
        Write-Host "Creating local virtual environment with python..." -ForegroundColor Cyan
        & $Launcher.Source -m venv $VenvDir
    }
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $VenvPython)) {
        throw "Virtual-environment creation failed."
    }
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "The selected Python executable does not exist: $VenvPython"
}

if ($InstallDependencies) {
    Write-Host "`n=== Installing pinned dependencies ===" -ForegroundColor Cyan
    & $VenvPython -m pip install -r $Requirements
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency installation failed with exit code $LASTEXITCODE"
    }
}
else {
    & $VenvPython -c "import numpy, pandas, scipy, sklearn, joblib" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Dependencies are missing. Re-run with: .\run_all.ps1 -InstallDependencies"
    }
}

$env:PYTHONDONTWRITEBYTECODE = "1"
if ($VerifyOnly) {
    Invoke-PythonStep "Verifying existing generated outputs" (Join-Path $PackageRoot "src\verify_outputs.py")
    Write-Host "`nVerification completed successfully." -ForegroundColor Green
    exit 0
}

Invoke-PythonStep "1/4 Preparing and auditing FD001 data" (Join-Path $PackageRoot "src\prepare_fd001_data.py")
Invoke-PythonStep "2/4 Training and evaluating C-MAPSS RUL models" (Join-Path $PackageRoot "src\run_fd001_models.py")
Invoke-PythonStep "3/4 Running warehouse prioritisation simulation" (Join-Path $PackageRoot "src\run_warehouse_priority_simulation.py")
Invoke-PythonStep "4/4 Verifying generated outputs" (Join-Path $PackageRoot "src\verify_outputs.py")

Write-Host "`nCompleted successfully." -ForegroundColor Green
Write-Host "Model outputs:   $PackageRoot\outputs\model_outputs"
Write-Host "Ranking outputs: $PackageRoot\outputs\ranking_outputs"
