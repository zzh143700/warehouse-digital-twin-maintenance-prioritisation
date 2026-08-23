param(
    [switch]$InstallDependencies,
    [switch]$Headless,
    [int]$Port = 8501,
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
$DashboardApp = Join-Path $PackageRoot "dashboard\streamlit_app.py"

if (-not $PythonPath -and -not (Test-Path -LiteralPath $VenvPython)) {
    $Launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $Launcher) {
        & $Launcher.Source -3 -m venv $VenvDir
    }
    else {
        $Launcher = Get-Command python -ErrorAction SilentlyContinue
        if ($null -eq $Launcher) {
            throw "Python was not found. Install 64-bit Python 3.11-3.13 and try again."
        }
        & $Launcher.Source -m venv $VenvDir
    }
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $VenvPython)) {
        throw "Virtual-environment creation failed."
    }
}

if ($InstallDependencies) {
    Write-Host "Installing pinned dashboard dependencies..." -ForegroundColor Cyan
    & $VenvPython -m pip install -r $Requirements
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency installation failed with exit code $LASTEXITCODE"
    }
}
else {
    & $VenvPython -c "import numpy, pandas, streamlit" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Dashboard dependencies are missing. Re-run with: .\run_dashboard.ps1 -InstallDependencies"
    }
}

$HeadlessValue = if ($Headless) { "true" } else { "false" }
$env:PYTHONDONTWRITEBYTECODE = "1"
Write-Host "Opening the dashboard at http://localhost:$Port" -ForegroundColor Green
& $VenvPython -m streamlit run $DashboardApp `
    --server.port $Port `
    --server.headless $HeadlessValue `
    --browser.gatherUsageStats false
