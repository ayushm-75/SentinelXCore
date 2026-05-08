# scripts/launch_sentinelx.ps1
# Right-click → Run as Administrator
# OR: create a shortcut with "Run as administrator" checked

$exe = "E:\SentinelXCore\dist\SentinelX.exe"

if (-not (Test-Path $exe)) {
    Write-Host "SentinelX.exe not found. Run build first." -ForegroundColor Red
    Write-Host "  cd E:\SentinelXCore"
    Write-Host "  powershell -File scripts/build.ps1"
    pause
    exit 1
}

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdmin) {
    Write-Host "Relaunching as Administrator..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host "Starting SentinelX Core..." -ForegroundColor Cyan
Start-Process $exe -Verb RunAs