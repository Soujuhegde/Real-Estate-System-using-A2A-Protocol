"""
Agent 4: Concierge (Orchestrator) Agent
Discovers specialist agents, routes requests, runs LangGraph workflow
A2A Client + FastAPI — Port 8000
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

from shared.a2a_models import AgentCard, AgentSkill
from shared.a2a_client import A2AClient
from shared.db import init_db
from shared import config
from .graph import build_graph, OrchestratorState
from .discovery import discover_all_agents

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("concierge")

app = FastAPI(title="Concierge Orchestrator Agent", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_graph = None
_discovered_agents: dict = {}


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


AGENT_CARD = AgentCard(
    name="Concierge Orchestrator",
    description="Central orchestrator for the real estate multi-agent system. Routes requests to Customer, Deal, and Marketing agents.",
    url="http://localhost:8000",
    skills=[
        AgentSkill(id="orchestrate", name="Orchestrate Request", description="Route and coordinate any real estate request"),
    ],
)


@app.on_event("startup")
async def startup():
    init_db()
    global _discovered_agents
    _discovered_agents = await discover_all_agents()
    logger.info(f"Concierge started. Discovered agents: {list(_discovered_agents.keys())}")


@app.get("/.well-known/agent.json")
async def agent_card():
    return AGENT_CARD.model_dump()


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "concierge", "discovered": list(_discovered_agents.keys())}


@app.get("/agents")
async def list_agents():
    """Return discovered agent cards"""
    return {
        "agents": {
            k: v.model_dump() if hasattr(v, "model_dump") else v
            for k, v in _discovered_agents.items()
        }
    }


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    intent: str
    artifacts: list = []
    error: str = None


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main endpoint: natural language → LangGraph → response"""
    logger.info(f"[Session {request.session_id}] User: {request.message[:120]}")

    initial_state: OrchestratorState = {
        "user_input": request.message,
        "intent": "",
        "extracted_payload": {},
        "agent_response": None,
        "agent_artifacts": None,
        "rag_context": None,
        "final_response": "",
        "error": None,
    }

    try:
        graph = get_graph()
        config = {"configurable": {"thread_id": request.session_id}}
        result = await graph.ainvoke(initial_state, config=config)
        return ChatResponse(
            response=result["final_response"],
            intent=result.get("intent", "unknown"),
            artifacts=result.get("agent_artifacts") or [],
            error=result.get("error"),
        )
    except Exception as e:
        logger.exception("Graph execution failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── Direct agent task endpoints (for Streamlit direct calls) ─────────────────

class DirectTaskRequest(BaseModel):
    payload: dict


@app.post("/agents/customer/onboard")
async def direct_customer_onboard(request: DirectTaskRequest):
    client = A2AClient()
    resp = await client.send_task(config.CUSTOMER_AGENT_URL, json.dumps(request.payload))
    return resp.model_dump()


@app.post("/agents/deal/onboard")
async def direct_deal_onboard(request: DirectTaskRequest):
    client = A2AClient()
    resp = await client.send_task(config.DEAL_AGENT_URL, json.dumps(request.payload))
    return resp.model_dump()


@app.post("/agents/marketing/insights")
async def direct_marketing_insights(request: DirectTaskRequest):
    client = A2AClient()
    resp = await client.send_task(config.MARKETING_AGENT_URL, json.dumps(request.payload))
    return resp.model_dump()


if __name__ == "__main__":
    uvicorn.run("concierge_agent.main:app", host="0.0.0.0", port=8000, reload=True)
