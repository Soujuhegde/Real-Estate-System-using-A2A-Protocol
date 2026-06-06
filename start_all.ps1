# start_all.ps1 — Launch all agents and the Streamlit frontend on Windows
# Usage: .\start_all.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

# Ensure .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env not found. Copying .env.example → .env" -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "   Please fill in your API keys in .env before continuing." -ForegroundColor Yellow
}

New-Item -ItemType Directory -Force -Path "data/db", "logs" | Out-Null

Write-Host "──────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "🚀 Starting Real Estate Multi-Agent System" -ForegroundColor Cyan
Write-Host "──────────────────────────────────────────────" -ForegroundColor Cyan

# Define the environment variable for Python
$env:PYTHONPATH = "$ProjectRoot\src"

# Kill any existing python/uvicorn/streamlit processes running on the ports
# Note: This simply kills any python processes for a clean start
$pythonProcs = Get-Process -Name python, uvicorn, streamlit -ErrorAction SilentlyContinue
if ($pythonProcs) {
    Write-Host "⚡ Killing existing Python processes to free up ports..." -ForegroundColor Yellow
    Stop-Process -InputObject $pythonProcs -Force
    Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host "▶ Starting Customer Onboarding Agent (port 8001)..."
Start-Process -NoNewWindow -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn customer_agent.main:app --host 0.0.0.0 --port 8001" -RedirectStandardOutput "logs\customer_agent.log" -RedirectStandardError "logs\customer_agent.log"

Write-Host "▶ Starting Deal Onboarding Agent (port 8002)..."
Start-Process -NoNewWindow -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn deal_agent.main:app --host 0.0.0.0 --port 8002" -RedirectStandardOutput "logs\deal_agent.log" -RedirectStandardError "logs\deal_agent.log"

Write-Host "▶ Starting Marketing Intelligence Agent (port 8003)..."
Start-Process -NoNewWindow -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn marketing_agent.main:app --host 0.0.0.0 --port 8003" -RedirectStandardOutput "logs\marketing_agent.log" -RedirectStandardError "logs\marketing_agent.log"

Write-Host ""
Write-Host "⏳ Waiting for specialist agents to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "▶ Starting Concierge Orchestrator (port 8000)..."
Start-Process -NoNewWindow -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn concierge_agent.main:app --host 0.0.0.0 --port 8000" -RedirectStandardOutput "logs\concierge.log" -RedirectStandardError "logs\concierge.log"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "▶ Starting Streamlit Frontend (port 8501)..."
Start-Process -NoNewWindow -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m streamlit run src\streamlit_app\app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false" -RedirectStandardOutput "logs\streamlit.log" -RedirectStandardError "logs\streamlit.log"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "──────────────────────────────────────────────" -ForegroundColor Green
Write-Host "✅ All services started in the background!" -ForegroundColor Green
Write-Host ""
Write-Host "   Streamlit UI:     http://localhost:8501"
Write-Host "   Concierge API:    http://localhost:8000/docs"
Write-Host "   Customer Agent:   http://localhost:8001/docs"
Write-Host "   Deal Agent:       http://localhost:8002/docs"
Write-Host "   Marketing Agent:  http://localhost:8003/docs"
Write-Host ""
Write-Host "   Logs: .\logs\"
Write-Host "──────────────────────────────────────────────" -ForegroundColor Green
