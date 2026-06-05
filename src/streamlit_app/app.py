"""
Real Estate Multi-Agent System — Streamlit Frontend
Main App: System Dashboard
"""
import streamlit as st
import httpx
import asyncio
from datetime import datetime

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RE Multi-Agent System",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Config ────────────────────────────────────────────────────────────────────
CONCIERGE_URL = "http://localhost:8000"

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stApp { font-family: 'Inter', sans-serif; }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #2563eb;
        margin-bottom: 16px;
    }
    .agent-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }
    .status-dot-green { color: #22c55e; font-size: 12px; }
    .status-dot-red { color: #ef4444; font-size: 12px; }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.25rem;
    }
    .hero-sub { color: #64748b; font-size: 1.05rem; margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def sync_get(url: str, timeout: float = 4.0):
    try:
        r = httpx.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)


def check_agent_health(name: str, url: str) -> bool:
    data, err = sync_get(f"{url}/health", timeout=3.0)
    return data is not None and data.get("status") == "ok"


AGENTS = {
    "Concierge Orchestrator": ("http://localhost:8000", "🎯"),
    "Customer Onboarding": ("http://localhost:8001", "👤"),
    "Deal Onboarding": ("http://localhost:8002", "🏘️"),
    "Marketing Intelligence": ("http://localhost:8003", "📊"),
}

# ── Layout ────────────────────────────────────────────────────────────────────

st.markdown('<p class="hero-title">🏠 Real Estate Multi-Agent System</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Federated AI agents powered by A2A Protocol · LangGraph · Sarvam AI · Pinecone</p>',
    unsafe_allow_html=True,
)

# ── Agent Status ──────────────────────────────────────────────────────────────
st.subheader("🔌 Agent Network Status")
cols = st.columns(4)
all_healthy = True
for i, (name, (url, icon)) in enumerate(AGENTS.items()):
    healthy = check_agent_health(name, url)
    if not healthy:
        all_healthy = False
    with cols[i]:
        status_color = "#22c55e" if healthy else "#ef4444"
        status_label = "Online" if healthy else "Offline"
        st.markdown(f"""
        <div class="agent-card">
            <div style="font-size:1.8rem">{icon}</div>
            <div style="font-weight:600;color:#1e293b;margin:6px 0 2px">{name}</div>
            <div style="font-size:0.78rem;color:#64748b">{url}</div>
            <div style="margin-top:8px">
                <span style="background:{status_color}22;color:{status_color};
                             padding:2px 10px;border-radius:20px;font-size:0.8rem;font-weight:600">
                    ● {status_label}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

if all_healthy:
    st.success("✅ All agents are online and ready.")
else:
    st.warning("⚠️ Some agents are offline. Start all agents before using the system.")

st.divider()

# ── Architecture Diagram ──────────────────────────────────────────────────────
st.subheader("🗺️ System Architecture")
st.markdown("""
```
┌─────────────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend (Port 8501)                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│           Concierge Orchestrator Agent (Port 8000)                   │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  LangGraph StateGraph                                        │    │
│  │  classify_intent → route → specialist_agent → synthesize     │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────┬─────────────────┬──────────────────────┬────────────────┘
           │ A2A Protocol    │ A2A Protocol          │ A2A Protocol
           ▼                 ▼                        ▼
  ┌────────────────┐  ┌────────────────┐   ┌──────────────────────┐
  │ Customer Agent │  │  Deal Agent    │   │ Marketing Agent      │
  │  (Port 8001)   │  │  (Port 8002)   │   │  (Port 8003)         │
  └───────┬────────┘  └───────┬────────┘   └──────────┬───────────┘
          │                   │                        │
          ▼                   ▼                        ▼
  ┌────────────────────────────────┐         ┌────────────────────┐
  │     SQLite Database            │         │  Pinecone / FAISS  │
  │  (customers, properties, logs) │         │  Vector Store RAG  │
  └────────────────────────────────┘         └────────────────────┘
```
""")

st.divider()

# ── Quick Start Guide ─────────────────────────────────────────────────────────
st.subheader("🚀 Quick Start")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    **Step 1 — Register a Customer**
    Navigate to **Customer Onboarding** in the sidebar.
    Fill in buyer details and submit.
    """)
with col2:
    st.markdown("""
    **Step 2 — List a Property**
    Navigate to **Deal Onboarding**.
    Add property specs — this auto-triggers market analysis.
    """)
with col3:
    st.markdown("""
    **Step 3 — Chat with Concierge**
    Navigate to **Concierge Chat**.
    Ask anything in natural language — the AI routes to the right agent.
    """)

st.divider()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:#94a3b8;font-size:0.8rem;margin-top:2rem'>"
    "Real Estate MAS · A2A Protocol · LangGraph · Sarvam AI · Pinecone"
    "</div>",
    unsafe_allow_html=True,
)
