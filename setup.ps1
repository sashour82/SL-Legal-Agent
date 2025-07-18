
# -------------------------------
# Enhanced Flask + Vue Project Setup Script
# For Windows (PowerShell)
# -------------------------------

Write-Host "🧪 Checking required tools..." -ForegroundColor Cyan

# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python is not installed. Please install Python before running this script." -ForegroundColor Red
    exit 1
}

# Check for Node.js and npm
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js (npm) is not installed. Please install Node.js before running this script." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Required tools found." -ForegroundColor Green

Write-Host "📁 Setting up Python virtual environment..." -ForegroundColor Cyan
python -m venv venv

Write-Host "✅ Virtual environment created." -ForegroundColor Green
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Cyan
.\\venv\\Scripts\\Activate.ps1

Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
pip install --upgrade pip
pip install -r backend\\requirements.txt
Write-Host "✅ Python dependencies installed." -ForegroundColor Green

Write-Host "🗃️ Running database setup..." -ForegroundColor Cyan
cd backend

# Run db init if migrations folder does not exist
if (-not (Test-Path "migrations")) {
    flask db init
    flask db migrate -m "Initial migration"
}

flask db upgrade
cd ..

Write-Host "📁 Installing frontend dependencies..." -ForegroundColor Cyan
cd frontend
npm install
cd ..

Write-Host "✅ Frontend dependencies installed." -ForegroundColor Green

Write-Host "`n🚀 Setup complete. You can now:" -ForegroundColor Yellow
Write-Host "👉 Run Flask backend:    python backend/main.py"
Write-Host "👉 Run Vue frontend:     cd frontend && npm run dev"
