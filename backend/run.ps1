# RAG Pipeline PowerShell Startup Script
Write-Host "RAG Pipeline Startup Script" -ForegroundColor Green
Write-Host "===========================" -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install/upgrade dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Check if GOOGLE_API_KEY is set
if (-not $env:GOOGLE_API_KEY) {
    Write-Host ""
    Write-Host "⚠ WARNING: GOOGLE_API_KEY environment variable is not set" -ForegroundColor Yellow
    Write-Host "Some features may not work properly" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To set it, run: `$env:GOOGLE_API_KEY = 'your_api_key_here'" -ForegroundColor Cyan
    Write-Host ""
}

# Run the startup check
Write-Host ""
Write-Host "Running startup check..." -ForegroundColor Yellow
python run.py

# Keep window open if there's an error
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Press Enter to exit..." -ForegroundColor Yellow
    Read-Host
}
