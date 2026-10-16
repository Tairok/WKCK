# Starts BMC Console in this window (Daphne on http://127.0.0.1:8000).
# Runs as Administrator: sensor readings need elevated rights.
# Stop with Ctrl+C here, or from another window with .\stop.ps1
#   .\run.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$port = 8000

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`""
    exit
}

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) { throw "Virtual environment not found. Run install.ps1 first." }

if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
    throw "Port $port is already in use. BMC Console may already be running (use .\stop.ps1)."
}

Set-Location (Join-Path $root "server\src")
Write-Output "BMC Console: http://127.0.0.1:$port (Ctrl+C to stop)"
& $venvPython -m daphne -b 127.0.0.1 -p $port bmc_server.asgi:application
