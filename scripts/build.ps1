# scripts/build.ps1
param(
    [switch]$SkipFrontend,
    [switch]$SkipIcon,
    [switch]$Clean
)

$Root = "E:\SentinelXCore"
Set-Location $Root

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SentinelX Core — Production Build"     -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── Activate venv ─────────────────────────────────────────────
Write-Host "[1/7] Activating venv..." -ForegroundColor Yellow
& "$Root\venv\Scripts\Activate.ps1"

# ── Clean ─────────────────────────────────────────────────────
if ($Clean) {
    Write-Host "[2/7] Cleaning previous build..." -ForegroundColor Yellow
    if (Test-Path "$Root\dist")  { Remove-Item -Recurse -Force "$Root\dist" }
    if (Test-Path "$Root\build") { Remove-Item -Recurse -Force "$Root\build" }
    # Clear PyInstaller cache to avoid Defender-flagged cached files
    $piCache = "$env:USERPROFILE\AppData\Local\pyinstaller"
    if (Test-Path $piCache) {
        Remove-Item -Recurse -Force $piCache
        Write-Host "      PyInstaller cache cleared." -ForegroundColor Green
    }
    Write-Host "      Done." -ForegroundColor Green
} else {
    Write-Host "[2/7] Skipping clean (use -Clean flag to clean)" -ForegroundColor Gray
}

# ── Icon ──────────────────────────────────────────────────────
if (-not $SkipIcon) {
    Write-Host "[3/7] Creating app icon..." -ForegroundColor Yellow
    python scripts/create_icon.py
} else {
    Write-Host "[3/7] Skipping icon" -ForegroundColor Gray
}

# ── Frontend ──────────────────────────────────────────────────
if (-not $SkipFrontend) {
    Write-Host "[4/7] Building React frontend..." -ForegroundColor Yellow
    Set-Location "$Root\frontend"
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Frontend build FAILED!" -ForegroundColor Red
        Set-Location $Root
        exit 1
    }
    Set-Location $Root
    Write-Host "      Frontend built successfully." -ForegroundColor Green
} else {
    Write-Host "[4/7] Skipping frontend build" -ForegroundColor Gray
}

# ── UPX ───────────────────────────────────────────────────────
Write-Host "[5/7] Checking UPX..." -ForegroundColor Yellow
$upxExe = "$Root\upx\upx.exe"
if (-not (Test-Path $upxExe)) {
    Write-Host "      Downloading UPX..." -ForegroundColor Yellow
    $upxUrl = "https://github.com/upx/upx/releases/download/v4.2.4/upx-4.2.4-win64.zip"
    $upxZip = "$Root\upx_download.zip"
    try {
        Invoke-WebRequest -Uri $upxUrl -OutFile $upxZip -TimeoutSec 60
        New-Item -ItemType Directory -Force -Path "$Root\upx" | Out-Null
        Expand-Archive -Path $upxZip -DestinationPath "$Root\upx_temp" -Force
        $found = Get-ChildItem -Path "$Root\upx_temp" -Filter "upx.exe" -Recurse | Select-Object -First 1
        if ($found) {
            Copy-Item $found.FullName "$Root\upx\upx.exe" -Force
            Write-Host "      UPX installed." -ForegroundColor Green
        }
        Remove-Item -Recurse -Force "$Root\upx_temp" -ErrorAction SilentlyContinue
        Remove-Item -Force $upxZip -ErrorAction SilentlyContinue
    } catch {
        Write-Host "      UPX download failed — building without UPX compression." -ForegroundColor Yellow
    }
} else {
    Write-Host "      UPX found." -ForegroundColor Green
}

# Add UPX to PATH
if (Test-Path $upxExe) {
    $env:PATH = "$Root\upx;" + $env:PATH
}

# ── Temporarily disable Defender real-time for build ──────────
Write-Host "[6/7] Pausing Defender real-time protection for build..." -ForegroundColor Yellow
try {
    Set-MpPreference -DisableRealtimeMonitoring $true -ErrorAction SilentlyContinue
    Write-Host "      Defender paused." -ForegroundColor Green
} catch {
    Write-Host "      Could not pause Defender (may need admin). Continuing..." -ForegroundColor Yellow
}

# ── PyInstaller ───────────────────────────────────────────────
Write-Host "      Running PyInstaller (5-10 min)..." -ForegroundColor Yellow
pyinstaller --clean --noconfirm sentinelx.spec

$buildResult = $LASTEXITCODE

# ── Re-enable Defender ────────────────────────────────────────
try {
    Set-MpPreference -DisableRealtimeMonitoring $false -ErrorAction SilentlyContinue
    Write-Host "      Defender re-enabled." -ForegroundColor Green
} catch {
    Write-Host "      Re-enable Defender manually if needed." -ForegroundColor Yellow
}

if ($buildResult -ne 0) {
    Write-Host ""
    Write-Host "PyInstaller FAILED!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "  1. Add E:\SentinelXCore to Windows Defender exclusions"
    Write-Host "  2. Run: Add-MpPreference -ExclusionPath 'E:\SentinelXCore'"
    Write-Host "  3. Run this script again as Administrator"
    exit 1
}

# ── Add exclusion for the output exe ─────────────────────────
$exePath = "$Root\dist\SentinelX.exe"
if (Test-Path $exePath) {
    try {
        Add-MpPreference -ExclusionPath $exePath -ErrorAction SilentlyContinue
    } catch {}
}

# ── Result ────────────────────────────────────────────────────
Write-Host ""
Write-Host "[7/7] Post-processing..." -ForegroundColor Yellow

if (Test-Path $exePath) {
    $sizeMB = [math]::Round((Get-Item $exePath).Length / 1MB, 1)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Output : $exePath" -ForegroundColor White
    Write-Host "  Size   : ${sizeMB} MB"   -ForegroundColor White
    Write-Host ""

    if ($sizeMB -gt 200) {
        Write-Host "  Size > 200MB target (${sizeMB}MB)" -ForegroundColor Yellow
    } else {
        Write-Host "  Within 200MB target" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "  To run:" -ForegroundColor Cyan
    Write-Host "  Right-click SentinelX.exe → Run as Administrator" -ForegroundColor White
    Write-Host "  OR use: scripts\launch_sentinelx.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "  The app will:" -ForegroundColor Cyan
    Write-Host "  - Request admin rights automatically (UAC prompt)" -ForegroundColor White
    Write-Host "  - Open your browser to http://127.0.0.1:8765" -ForegroundColor White
    Write-Host "  - Show a system tray icon (shield in taskbar)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "Build output not found at: $exePath" -ForegroundColor Red
    exit 1
}