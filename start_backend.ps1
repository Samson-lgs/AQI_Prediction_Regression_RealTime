# Start AQI Backend Server
# This script starts the Flask backend server

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AQI Prediction System - Backend" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to project directory
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

# Activate virtual environment
Write-Host "[1/4] Activating virtual environment..." -ForegroundColor Yellow
try {
    & ".\.venv\Scripts\Activate.ps1"
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[ERROR] Failed to activate virtual environment" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Set Flask environment variables
$env:FLASK_DEBUG = "0"
$env:FLASK_APP = "backend/app.py"

# Kill any existing process on port 5000
Write-Host "[2/4] Checking for existing processes on port 5000..." -ForegroundColor Yellow
$procs = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($procs) {
    foreach ($p in $procs) {
        Write-Host "  -> Stopping process $p..." -ForegroundColor Yellow
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "[OK] Cleaned up old processes" -ForegroundColor Green
} else {
    Write-Host "[OK] No existing processes found" -ForegroundColor Green
}
Write-Host ""

# Start Flask server
Write-Host "[3/4] Starting Flask server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Server URLs:" -ForegroundColor Green
Write-Host "  -> http://localhost:5000" -ForegroundColor White
Write-Host "  -> http://127.0.0.1:5000" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[4/4] Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python backend/app.py
