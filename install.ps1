# Installs BMC Console on this machine.
# Run from the repository root in an elevated (Administrator) PowerShell:
#   .\install.ps1
#
# What it does:
#   1. Creates .venv and installs requirements.txt
#   2. Builds the frontend (needs Node.js 20+; skipped with a warning if missing)
#   3. Creates the runtime folders (server\src\data, server\src\logs)
#
# LibreHardwareMonitor is not started as a separate program: the server loads
# LibreHardwareMonitorLib.dll itself (see server\src\services\sensor_service.py).

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
# The scheduled task needs elevated rights, so re-launch this script as Administrator (UAC prompt)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`""
    exit
}

Write-Output "== 1. Python environment"
$venvDir = Join-Path $root ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -m venv $venvDir
    } else {
        & python -m venv $venvDir
    }
    if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment. Install Python 3.12 first." }
}
& $venvPython -m pip install --upgrade pip | Out-Null
& $venvPython -m pip install -r (Join-Path $root "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "pip install failed." }

Write-Output "== 2. Frontend build"
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Push-Location (Join-Path $root "frontend")
    try {
        npm install
        if ($LASTEXITCODE -ne 0) { throw "npm install failed." }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
    } finally {
        Pop-Location
    }
} else {
    Write-Warning "Node.js not found - the frontend was not built. Install Node.js 20+ and run this script again."
}

Write-Output "== 3. Runtime folders"
New-Item -ItemType Directory -Force -Path (Join-Path $root "server\src\data"), (Join-Path $root "server\src\logs") | Out-Null

Write-Output ""
Write-Output "Installation finished."
Write-Output "Start the server manually (run as Administrator, sensor readings need elevated rights):"
Write-Output "  cd server\src"
Write-Output "  ..\..\.venv\Scripts\python.exe -m daphne -b 127.0.0.1 -p 8000 bmc_server.asgi:application"
Write-Output "Then open http://127.0.0.1:8000"
