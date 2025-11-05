# AQI Prediction System - Start Script
# Run this script to start the enhanced Flask backend

Write-Host "=" -NoNewline; for ($i=0; $i -lt 69; $i++) { Write-Host "=" -NoNewline }; Write-Host ""
Write-Host "AQI Prediction System - Enhanced Backend"
Write-Host "=" -NoNewline; for ($i=0; $i -lt 69; $i++) { Write-Host "=" -NoNewline }; Write-Host ""
Write-Host ""

# Check if virtual environment is activated
if ($env:VIRTUAL_ENV) {
    Write-Host "[✓] Virtual environment active: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "[!] Virtual environment not active. Activating..." -ForegroundColor Yellow
    & ".\aqi_env\Scripts\Activate.ps1"
}

Write-Host ""
Write-Host "Starting enhanced Flask backend..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Features enabled:" -ForegroundColor White
Write-Host "  ✓ RESTful API with Swagger docs (/api/v1/docs)" -ForegroundColor Green
Write-Host "  ✓ WebSocket real-time updates (/socket.io)" -ForegroundColor Green
Write-Host "  ✓ Redis caching (if Redis running)" -ForegroundColor Green
Write-Host "  ✓ Rate limiting (200/day, 50/hour)" -ForegroundColor Green
Write-Host "  ✓ CORS enabled" -ForegroundColor Green
Write-Host ""
Write-Host "Access points:" -ForegroundColor White
Write-Host "  • Frontend:     http://localhost:5000" -ForegroundColor Cyan
Write-Host "  • API:          http://localhost:5000/api/v1" -ForegroundColor Cyan
Write-Host "  • Swagger UI:   http://localhost:5000/api/v1/docs" -ForegroundColor Cyan
Write-Host "  • WebSocket:    ws://localhost:5000/socket.io" -ForegroundColor Cyan
Write-Host ""
Write-Host "=" -NoNewline; for ($i=0; $i -lt 69; $i++) { Write-Host "=" -NoNewline }; Write-Host ""
Write-Host ""

# Start the Flask application
python backend/app.py
