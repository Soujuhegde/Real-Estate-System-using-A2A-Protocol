# 🏠 Real Estate Federated Multi-Agent System
### A2A Protocol · LangGraph · Sarvam AI · Pinecone · FastAPI · Streamlit

---

## 1. Project Overview

A **federated multi-agent AI system** for real estate platforms. Four autonomous
AI agents communicate using the **A2A (Agent-to-Agent) Protocol** — each independently
deployable, each exposing a standardized Agent Card and task endpoint.

### What It Does

| Capability | Agent | How |
|---|---|---|
| Buyer/investor registration | Customer Onboarding | Validates & persists profiles to SQLite |
| Property listing | Deal Onboarding | Normalises data, auto-triggers analysis |
| Market intelligence | Marketing Intelligence | LLM-generated insights + RAG via Pinecone |
| Natural language interface | Concierge Orchestrator | LangGraph routes NL requests to right agent |

### Target Users
- Real estate platform operators (multi-tenant SaaS)
- Proptech engineers evaluating agent-based architectures
- Evaluators of A2A protocol + LangGraph orchestration patterns

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 Streamlit Frontend  :8501                     │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP REST
                         ▼
┌──────────────────────────────────────────────────────────────┐
│         Concierge Orchestrator Agent  :8000                   │
│                                                               │
│  ┌─────────────────── LangGraph StateGraph ─────────────┐    │
│  │  classify_intent                                       │    │
│  │       ↓ (conditional routing)                         │    │
│  │  onboard_customer | onboard_deal | query_insights      │    │
│  │       ↓                                               │    │
│  │  generate_response                                     │    │
│  └────────────────────────────────────────────────────── ┘    │
│                                                               │
│  Agent Discovery  →  /.well-known/agent.json  (per agent)    │
└──────┬──────────────────┬──────────────────────┬─────────────┘
       │ A2A              │ A2A                  │ A2A
       ▼                  ▼                       ▼
┌────────────┐  ┌──────────────┐  ┌────────────────────────┐
│ Customer   │  │ Deal         │  │ Marketing Intelligence  │
│ Agent :8001│  │ Agent :8002  │  │ Agent :8003             │
│            │  │              │  │                         │
│ Validates  │  │ Validates +  │  │ Sarvam LLM → Insights  │
│ Persists   │  │ Triggers     │  │ Sentence-Transformers  │
│ SQLite     │  │ Marketing ↗  │  │ Pinecone Vector DB     │
└────────────┘  └──────────────┘  └────────────────────────┘
      │                │                        │
      └────────────────┴──────── SQLite ─────── ┘
```

### A2A Communication Flow

```
User Request
    │
    ▼
Concierge.POST /chat
    │
    ├─── LangGraph: classify_intent  (Sarvam LLM)
    │
    ├─── Route: customer_onboarding
    │        └─→ CustomerAgent.POST /tasks/send
    │                └─→ Validate + SQLite insert
    │
    ├─── Route: deal_onboarding
    │        └─→ DealAgent.POST /tasks/send
    │                ├─→ Validate + SQLite insert
    │                └─→ [async] MarketingAgent.POST /tasks/send
    │                           ├─→ Sarvam LLM: generate insights
    │                           └─→ Pinecone: embed + upsert
    │
    └─── Route: market_insights
             └─→ MarketingAgent.POST /tasks/send
                     └─→ Pinecone: semantic search (RAG)
```

---

## 3. Project Structure

```
real-estate-mas/
├── shared/                      # Shared utilities (A2A models, DB, LLM, config)
│   ├── __init__.py
│   ├── a2a_models.py            # Pydantic models for A2A protocol
│   ├── a2a_client.py            # Async HTTP client for A2A communication
│   ├── config.py                # All env-var configuration
│   ├── db.py                    # SQLite init + connection context manager
│   └── llm.py                   # Sarvam AI wrapper (OpenAI-compatible)
│
├── customer_agent/              # Agent 1 — Port 8001
│   ├── main.py                  # FastAPI + A2A server
│   └── handlers.py              # Validation + SQLite persistence
│
├── deal_agent/                  # Agent 2 — Port 8002
│   ├── main.py                  # FastAPI + A2A server + async trigger
│   └── handlers.py              # Validation + persistence
│
├── marketing_agent/             # Agent 3 — Port 8003
│   ├── main.py                  # FastAPI + A2A server (generate & query)
│   ├── intelligence.py          # Sarvam LLM insight generation + fallback
│   └── embeddings.py            # Pinecone upsert + FAISS fallback + RAG query
│
├── concierge_agent/             # Agent 4 — Port 8000
│   ├── main.py                  # FastAPI orchestrator + /chat endpoint
│   ├── graph.py                 # LangGraph StateGraph definition
│   └── discovery.py             # Agent Card discovery
│
├── streamlit_app/               # Frontend — Port 8501
│   ├── app.py                   # Dashboard + agent status
│   └── pages/
│       ├── 1_Customer_Onboarding.py
│       ├── 2_Deal_Onboarding.py
│       ├── 3_Market_Intelligence.py
│       └── 4_Concierge_Chat.py
│
├── data/db/                     # SQLite database (auto-created)
├── logs/                        # Agent logs (auto-created)
├── requirements.txt
├── .env.example                 # Config template
├── start_all.sh                 # One-command startup
└── README.md
```

---

## 4. Setup Instructions

### 4.1 Prerequisites

- Python 3.11+
- pip
- Sarvam AI API key → [https://dashboard.sarvam.ai](https://dashboard.sarvam.ai)
- Pinecone API key → [https://app.pinecone.io](https://app.pinecone.io)

### 4.2 Install

```bash
git clone <your-repo-url>
cd real-estate-mas

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

> **Note on torch:** If `torch` installation is slow, install CPU-only first:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> pip install -r requirements.txt
> ```

### 4.3 Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
SARVAM_API_KEY=your_actual_sarvam_key
SARVAM_BASE_URL=https://api.sarvam.ai/v1
SARVAM_MODEL=sarvam-m

PINECONE_API_KEY=your_actual_pinecone_key
PINECONE_INDEX_NAME=realestate-insights
PINECONE_ENVIRONMENT=us-east-1
```

> **No Pinecone key?** The system auto-falls back to in-memory FAISS — all RAG
> features work, but insights won't persist across restarts.

---

## 5. Running the System

### Option A — One-shot startup (recommended)

**For Linux / macOS:**
```bash
bash start_all.sh
```

**For Windows (PowerShell):**
```powershell
.\start_all.ps1
```

This starts all four agents + Streamlit in the background and prints URLs.

### Option B — Manual (separate terminals)

**For Linux / macOS:**
```bash
# Terminal 1 — Customer Agent
PYTHONPATH=src python -m uvicorn customer_agent.main:app --port 8001 --reload

# Terminal 2 — Deal Agent
PYTHONPATH=src python -m uvicorn deal_agent.main:app --port 8002 --reload

# Terminal 3 — Marketing Agent
PYTHONPATH=src python -m uvicorn marketing_agent.main:app --port 8003 --reload

# Terminal 4 — Concierge (start AFTER other agents)
PYTHONPATH=src python -m uvicorn concierge_agent.main:app --port 8000 --reload

# Terminal 5 — Streamlit
PYTHONPATH=src streamlit run src/streamlit_app/app.py
```

**For Windows (PowerShell):**
```powershell
# Terminal 1 — Customer Agent
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m uvicorn customer_agent.main:app --port 8001 --reload

# Terminal 2 — Deal Agent
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m uvicorn deal_agent.main:app --port 8002 --reload

# Terminal 3 — Marketing Agent
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m uvicorn marketing_agent.main:app --port 8003 --reload

# Terminal 4 — Concierge (start AFTER other agents)
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m uvicorn concierge_agent.main:app --port 8000 --reload

# Terminal 5 — Streamlit
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m streamlit run src/streamlit_app/app.py
```

### Verify

```bash
curl http://localhost:8000/health    # {"status":"ok","agent":"concierge",...}
curl http://localhost:8001/health    # {"status":"ok","agent":"customer_onboarding"}
curl http://localhost:8002/health    # {"status":"ok","agent":"deal_onboarding"}
curl http://localhost:8003/health    # {"status":"ok","agent":"marketing_intelligence"}
```

Open **http://localhost:8501** in your browser.

---

## 6. API Reference

### Agent Cards (A2A Discovery)

```
GET /<agent_url>/.well-known/agent.json
```

Example:
```bash
curl http://localhost:8001/.well-known/agent.json
```

### Concierge — Natural Language Chat

```
POST http://localhost:8000/chat
Content-Type: application/json

{
  "message": "Register me as an investor. Name: Priya, email: priya@co.in, budget ₹50L-₹2Cr, Whitefield",
  "session_id": "session-001"
}
```

### Direct Agent Tasks (A2A)

```
POST http://localhost:<port>/tasks/send
Content-Type: application/json

{
  "id": "task-uuid",
  "message": {
    "role": "user",
    "parts": [{"text": "<JSON payload as string>"}]
  }
}
```

---

## 7. Sample Test Cases

### TC-01: Customer Onboarding

```bash
curl -X POST http://localhost:8000/agents/customer/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "full_name": "Ananya Krishnan",
      "email": "ananya@example.com",
      "phone": "9876543210",
      "buyer_type": "investor",
      "budget_min": 5000000,
      "budget_max": 20000000,
      "preferred_locations": ["Whitefield", "HSR Layout"]
    }
  }'
```

Expected: `{"status": {"state": "completed"}, "artifacts": [{"metadata": {"customer_id": "CUST-XXXXXXXX"}}]}`

### TC-02: Deal Onboarding + Marketing Trigger

```bash
curl -X POST http://localhost:8000/agents/deal/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "title": "3BHK Premium Apartment Whitefield",
      "location": "Whitefield, Bengaluru",
      "property_type": "apartment",
      "price": 9500000,
      "area_sqft": 1650,
      "bedrooms": 3,
      "bathrooms": 2,
      "amenities": ["Gym", "Pool", "Security"],
      "owner_name": "Suresh Kumar",
      "owner_contact": "9123456789"
    }
  }'
```

Expected: `{"status": {"state": "completed"}, "artifacts": [{"metadata": {"property_id": "PROP-XXXXXXXX"}}]}`
Also: Marketing Agent auto-triggered in background (check logs).

### TC-03: RAG Market Insights Query

```bash
curl -X POST http://localhost:8000/agents/marketing/insights \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "query": "What are the rental yield prospects for Whitefield apartments?"
    }
  }'
```

### TC-04: Natural Language via Concierge Chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What market risks should I know about apartments in Electronic City?",
    "session_id": "test-001"
  }'
```

### TC-05: Validation Error Handling

```bash
# Missing required field
curl -X POST http://localhost:8000/agents/customer/onboard \
  -H "Content-Type: application/json" \
  -d '{"payload": {"full_name": "Test", "buyer_type": "buyer"}}'
# Expected: state=failed, error lists missing email, budget fields
```

### TC-06: Agent Card Discovery

```bash
for port in 8000 8001 8002 8003; do
  echo "=== Port $port ===" && curl -s http://localhost:$port/.well-known/agent.json | python3 -m json.tool
done
```

---



---

## 8. LangGraph Workflow Detail

```python
# State flows through these nodes:
classify_intent          # Sarvam LLM classifies intent + extracts payload
    ↓ (conditional)
onboard_customer         # Calls Customer Agent via A2A
onboard_deal             # Calls Deal Agent via A2A
query_insights           # Calls Marketing Agent via A2A (RAG retrieval)
handle_unknown           # Returns help menu
    ↓
generate_response        # Sarvam LLM synthesises final user-facing reply
```

The graph uses `asyncio`-compatible `ainvoke()` so the entire pipeline
is non-blocking.

---

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: shared` | Run with `PYTHONPATH=.` prefix |
| Marketing agent slow on first call | Sentence-transformer model downloads on first run (~90MB) |
| Pinecone index not found | Check `PINECONE_INDEX_NAME` and region match your Pinecone console |
| Sarvam API 401 | Verify `SARVAM_API_KEY` is correct |
| Port already in use | Run `start_all.sh` — it kills existing processes on those ports |
| LangGraph import error | Ensure `langgraph>=0.2.0` is installed (`pip show langgraph`) |
