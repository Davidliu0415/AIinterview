param(
    [switch]$CheckOnly,
    [switch]$SetupOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$VenvDir = Join-Path $Root ".venv"
$SitePackages = Join-Path $VenvDir "Lib\site-packages"
$Requirements = Join-Path $Root "requirements.txt"
$InstallMarker = Join-Path $Root ".venv\.requirements-installed"
$EnvPath = Join-Path $Root ".env"
$EnvExamplePath = Join-Path $Root ".env.example"

function Read-DotEnvValue {
    param(
        [string]$Path,
        [string]$Key,
        [string]$Default
    )

    if (-not (Test-Path $Path)) {
        return $Default
    }

    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if ($trimmed.Length -eq 0 -or $trimmed.StartsWith("#")) {
            continue
        }
        $parts = $trimmed.Split("=", 2)
        if ($parts.Length -eq 2 -and $parts[0].Trim() -eq $Key) {
            return $parts[1].Trim().Trim('"').Trim("'")
        }
    }
    return $Default
}

function Ensure-CommandSucceeded {
    param([string]$Message)
    if ($LASTEXITCODE -ne 0) {
        throw $Message
    }
}

function Test-VenvHealth {
    if (-not (Test-Path $VenvPython)) {
        return $false
    }

    & $VenvPython -c "import sys; print(sys.version)" *> $null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    $hasInstalledDeps = (Test-Path $InstallMarker) -or
        (Test-Path (Join-Path $SitePackages "fastapi")) -or
        (Test-Path (Join-Path $SitePackages "pydantic_core")) -or
        (Test-Path (Join-Path $SitePackages "sqlalchemy"))

    if ($hasInstalledDeps) {
        & $VenvPython -c "import fastapi, pydantic_core, sqlalchemy" *> $null
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
    }

    return $true
}

Set-Location -LiteralPath $Root

if (-not (Test-Path $EnvPath) -and (Test-Path $EnvExamplePath)) {
    Copy-Item -LiteralPath $EnvExamplePath -Destination $EnvPath
    Write-Host "Created .env from .env.example. Please edit .env if credentials differ." -ForegroundColor Yellow
}

$AppHost = Read-DotEnvValue -Path $EnvPath -Key "APP_HOST" -Default "127.0.0.1"
$AppPort = [int](Read-DotEnvValue -Path $EnvPath -Key "APP_PORT" -Default "8000")
$AppUrl = "http://${AppHost}:${AppPort}"

if ($CheckOnly) {
    Write-Host "Project root: $Root"
    Write-Host "Python: $VenvPython"
    Write-Host "App URL: $AppUrl"
    exit 0
}

Write-Host "AI Java Interview Agent" -ForegroundColor Cyan
Write-Host "Project: $Root"

if (-not $SetupOnly) {
    $existing = Get-NetTCPConnection -LocalPort $AppPort -State Listen -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "App already appears to be running on $AppUrl" -ForegroundColor Yellow
        Start-Process $AppUrl
        exit 0
    }
}

if ((Test-Path $VenvPython) -and -not (Test-VenvHealth)) {
    $resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
    $resolvedVenv = (Resolve-Path -LiteralPath $VenvDir).Path
    if (-not $resolvedVenv.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove virtual environment outside project root: $resolvedVenv"
    }
    Write-Host "Virtual environment is inconsistent. Rebuilding .venv..." -ForegroundColor Yellow
    Remove-Item -LiteralPath $resolvedVenv -Recurse -Force
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    Ensure-CommandSucceeded "Failed to create virtual environment."
}

$needsInstall = -not (Test-Path $InstallMarker)
if (-not $needsInstall -and (Test-Path $Requirements)) {
    $needsInstall = (Get-Item $Requirements).LastWriteTimeUtc -gt (Get-Item $InstallMarker).LastWriteTimeUtc
}

if ($needsInstall) {
    Write-Host "Installing Python dependencies..."
    & $VenvPython -m pip install -r requirements.txt
    Ensure-CommandSucceeded "Failed to install dependencies."
    if (-not (Test-VenvHealth)) {
        throw "Virtual environment failed validation after dependency install."
    }
    New-Item -ItemType File -Force -Path $InstallMarker | Out-Null
}

Write-Host "Initializing MySQL database..."
& $VenvPython scripts\init_db.py
Ensure-CommandSucceeded "Failed to initialize database. Check MySQL and .env credentials."

if ($SetupOnly) {
    Write-Host "Setup complete." -ForegroundColor Green
    exit 0
}

Write-Host "Opening $AppUrl"
Write-Host "Close this window or press Ctrl+C to stop the service." -ForegroundColor DarkGray
& $VenvPython run_app.py
