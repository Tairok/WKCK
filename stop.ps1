# Stops BMC Console (whatever is listening on port 8000).
# Use it from another window when run.ps1 is running in a different one.
# Runs as Administrator, because the server process runs elevated.
#   .\stop.ps1

$ErrorActionPreference = "Stop"
$port = 8000

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`""
    exit
}

$listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if (-not $listeners) {
    Write-Output "BMC Console is not running (nothing listening on port $port)."
    exit 0
}

$pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($procId in $pids) {
    $name = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
    Stop-Process -Id $procId -Force
    Write-Output "Stopped process $name (PID $procId)."
}

Write-Output "BMC Console stopped."
