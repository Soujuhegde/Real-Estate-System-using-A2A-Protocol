#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# start_all.sh — Launch all agents and the Streamlit frontend
# Usage: bash start_all.sh
# ──────────────────────────────────────────────────────────────────────────────

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Force UTF-8 encoding for Python to prevent charmap errors on Windows with LLM emojis
export PYTHONIOENCODING=utf-8

# Ensure .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env not found. Copying .env.example → .env"
    cp .env.example .env
    echo "   Please fill in your API keys in .env before continuing."
fi

mkdir -p data/db logs

echo "──────────────────────────────────────────────"
echo "🚀 Starting Real Estate Multi-Agent System"
echo "──────────────────────────────────────────────"

# Kill any existing processes on our ports
for port in 8000 8001 8002 8003 8501; do
    pid=$(lsof -ti tcp:$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo "⚡ Killing existing process on port $port (PID $pid)"
        kill -9 $pid 2>/dev/null || true
    fi
done

sleep 1

# Start specialist agents first
echo ""
echo "▶ Starting Customer Onboarding Agent (port 8001)..."
PYTHONPATH="$PROJECT_ROOT/src" python -m uvicorn customer_agent.main:app --host 0.0.0.0 --port 8001 \
    --log-config /dev/null > logs/customer_agent.log 2>&1 &
echo "  PID: $!"

echo "▶ Starting Deal Onboarding Agent (port 8002)..."
PYTHONPATH="$PROJECT_ROOT/src" python -m uvicorn deal_agent.main:app --host 0.0.0.0 --port 8002 \
    --log-config /dev/null > logs/deal_agent.log 2>&1 &
echo "  PID: $!"

echo "▶ Starting Marketing Intelligence Agent (port 8003)..."
PYTHONPATH="$PROJECT_ROOT/src" python -m uvicorn marketing_agent.main:app --host 0.0.0.0 --port 8003 \
    --log-config /dev/null > logs/marketing_agent.log 2>&1 &
echo "  PID: $!"

# Wait for specialist agents to start
echo ""
echo "⏳ Waiting for specialist agents to be ready..."
sleep 4

# Check they are up
for port in 8001 8002 8003; do
    if curl -s "http://localhost:$port/health" > /dev/null; then
        echo "  ✅ Agent on port $port is up"
    else
        echo "  ❌ Agent on port $port did NOT start — check logs/"
    fi
done

# Start Concierge last (it discovers agents on startup)
echo ""
echo "▶ Starting Concierge Orchestrator (port 8000)..."
PYTHONPATH="$PROJECT_ROOT/src" python -m uvicorn concierge_agent.main:app --host 0.0.0.0 --port 8000 \
    --log-config /dev/null > logs/concierge.log 2>&1 &
echo "  PID: $!"

sleep 3

if curl -s "http://localhost:8000/health" > /dev/null; then
    echo "  ✅ Concierge is up"
else
    echo "  ❌ Concierge did NOT start — check logs/concierge.log"
fi

# Start Streamlit
echo ""
echo "▶ Starting Streamlit Frontend (port 8501)..."
PYTHONPATH="$PROJECT_ROOT/src" streamlit run src/streamlit_app/app.py \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false \
    > logs/streamlit.log 2>&1 &
echo "  PID: $!"

sleep 3

echo ""
echo "──────────────────────────────────────────────"
echo "✅ All services started!"
echo ""
echo "   Streamlit UI:     http://localhost:8501"
echo "   Concierge API:    http://localhost:8000/docs"
echo "   Customer Agent:   http://localhost:8001/docs"
echo "   Deal Agent:       http://localhost:8002/docs"
echo "   Marketing Agent:  http://localhost:8003/docs"
echo ""
echo "   Logs: ./logs/"
echo "──────────────────────────────────────────────"
