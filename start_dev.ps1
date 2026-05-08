# start_dev.ps1 — SentinelX Core Development Launcher
# Run as Administrator for full features

$Root = "E:\SentinelXCore"

Write-Host ""
Write-Host "  ╔═══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║   SentinelX Core — Dev Launcher       ║" -ForegroundColor Cyan
Write-Host "  ╚═══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdmin) {
    Write-Host "  ⚠ Not running as Administrator!" -ForegroundColor Yellow
    Write-Host "    VPN and packet capture will be limited." -ForegroundColor Yellow
    Write-Host "    Restart as Admin for full features." -ForegroundColor Yellow
    Write-Host ""
}

# Start backend
Write-Host "  [1/2] Starting backend..." -ForegroundColor Green
$backendJob = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$Root'; .\venv\Scripts\Activate.ps1; python -m backend.main"
) -PassThru -WindowStyle Normal

Start-Sleep -Seconds 2

# Start frontend
Write-Host "  [2/2] Starting frontend..." -ForegroundColor Green
$frontendJob = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$Root\frontend'; npm run dev"
) -PassThru -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "  Backend  → http://127.0.0.1:8765"     -ForegroundColor Green
Write-Host "  Frontend → http://127.0.0.1:5173"     -ForegroundColor Green
Write-Host "  Docs     → http://127.0.0.1:8765/docs" -ForegroundColor Cyan
Write-Host "  WebSocket→ ws://127.0.0.1:8765/ws"    -ForegroundColor Yellow
Write-Host ""
Write-Host "  Press Ctrl+Shift+S in browser for overlay mode" -ForegroundColor Cyan
Write-Host ""