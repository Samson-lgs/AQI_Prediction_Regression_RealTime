# AQI Dashboard Restart Script
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   AQI Dashboard Restart Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# Stop any existing Flask process on port 5000
Write-Host "Stopping existing Flask server..." -ForegroundColor Yellow
$processes = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($processes) {
    foreach ($proc in $processes) {
        Stop-Process -Id $proc -Force -ErrorAction SilentlyContinue
        Write-Host "  Stopped process $proc" -ForegroundColor Green
    }
    Start-Sleep -Seconds 2
}

# Start Flask backend with frontend serving
Write-Host ""
Write-Host "Starting Flask backend with dashboard..." -ForegroundColor Green
Write-Host "Dashboard will be available at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "API Documentation at: http://localhost:5000/api/v1/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Run the Flask app
python backend/app.py
