"""
Agent 2: Deal (Property) Onboarding Agent
A2A Server — Port 8002
Triggers Marketing Agent after successful onboarding
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import asyncio
import logging
import uuid
from fastapi import FastAPI
import uvicorn

from shared.a2a_models import (
    A2ATaskRequest, A2ATaskResponse, A2ATaskStatus,
    A2AMessage, A2AArtifact, A2APart, AgentCard, AgentSkill,
)
from shared.a2a_client import A2AClient
from shared.db import init_db, get_conn
from shared import config
from .handlers import onboard_property, validate_property_input

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("deal_agent")

app = FastAPI(title="Deal Onboarding Agent", version="1.0.0")

AGENT_CARD = AgentCard(
    name="Deal Onboarding Agent",
    description="Collects, validates, and persists real estate property listings. Automatically triggers market intelligence generation.",
    url="http://localhost:8002",
    skills=[
        AgentSkill(
            id="onboard_property",
            name="Onboard Property",
            description="Register a new property and trigger downstream market analysis",
            input_schema={
                "type": "object",
                "required": ["title", "location", "property_type", "price"],
                "properties": {
                    "title": {"type": "string"},
                    "location": {"type": "string"},
                    "property_type": {"type": "string"},
                    "price": {"type": "number"},
                    "area_sqft": {"type": "number"},
                    "bedrooms": {"type": "integer"},
                    "bathrooms": {"type": "integer"},
                    "amenities": {"type": "array", "items": {"type": "string"}},
                    "owner_name": {"type": "string"},
                    "owner_contact": {"type": "string"},
                },
            },
        )
    ],
)


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Deal Onboarding Agent started on port 8002")


@app.get("/.well-known/agent.json")
async def agent_card():
    return AGENT_CARD.model_dump()


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "deal_onboarding"}


from fastapi import FastAPI, HTTPException, Depends, Header

async def verify_token(x_internal_token: str = Header(None)):
    if x_internal_token != config.INTERNAL_API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid Internal API Token")

@app.post("/tasks/send", response_model=A2ATaskResponse, dependencies=[Depends(verify_token)])
async def handle_task(request: A2ATaskRequest):
    task_id = request.id
    user_text = request.message.parts[0].text if request.message.parts else ""
    logger.info(f"[Task {task_id}] Received deal onboarding request")

    try:
        try:
            payload = json.loads(user_text)
        except json.JSONDecodeError:
            payload = request.metadata or {}

        errors = validate_property_input(payload)
        if errors:
            _log_event("VALIDATION_FAILED", payload, "failed")
            return A2ATaskResponse(
                id=task_id,
                status=A2ATaskStatus(
                    state="failed",
                    message=A2AMessage.agent(f"Validation errors: {'; '.join(errors)}"),
                    error="; ".join(errors),
                ),
            )

        property_id = onboard_property(payload)
        _log_event("PROPERTY_ONBOARDED", {"property_id": property_id}, "success")
        logger.info(f"Property {property_id} onboarded. Triggering marketing agent...")

        # Async fire-and-forget to Marketing Agent and Matchmaking
        asyncio.create_task(_trigger_marketing(property_id, payload))
        asyncio.create_task(_trigger_match_async(payload))

        artifact_data = json.dumps({"property_id": property_id, "status": "onboarded"})
        return A2ATaskResponse(
            id=task_id,
            status=A2ATaskStatus(
                state="completed",
                message=A2AMessage.agent(
                    f"Property successfully onboarded. Property ID: {property_id}. "
                    f"Market intelligence analysis has been triggered."
                ),
            ),
            artifacts=[
                A2AArtifact(
                    name="property_listing",
                    parts=[A2APart(text=artifact_data)],
                    metadata={"property_id": property_id},
                )
            ],
        )

    except Exception as e:
        logger.exception(f"[Task {task_id}] Error")
        _log_event("ERROR", {"error": str(e)}, "failed")
        return A2ATaskResponse(
            id=task_id,
            status=A2ATaskStatus(
                state="failed",
                message=A2AMessage.agent(f"Internal error: {str(e)}"),
                error=str(e),
            ),
        )


async def _trigger_marketing(property_id: str, property_data: dict):
    """Fire-and-forget: notify marketing agent to analyze this property"""
    client = A2AClient()
    try:
        payload = json.dumps({"property_id": property_id, **property_data})
        resp = await client.send_task(config.MARKETING_AGENT_URL, payload)
        logger.info(f"Marketing agent triggered for {property_id}: {resp.status.state}")
        _log_event("MARKETING_TRIGGERED", {"property_id": property_id}, resp.status.state)
    except Exception as e:
        logger.warning(f"Failed to trigger marketing agent for {property_id}: {e}")
        _log_event("MARKETING_TRIGGER_FAILED", {"property_id": property_id, "error": str(e)}, "failed")

import httpx
async def _trigger_match_async(property_data: dict):
    """Fire-and-forget: notify customer agent to perform matchmaking"""
    try:
        from shared.config import CUSTOMER_AGENT_URL, INTERNAL_API_TOKEN
        headers = {"X-Internal-Token": INTERNAL_API_TOKEN}
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{CUSTOMER_AGENT_URL}/match", json=property_data, headers=headers, timeout=5.0)
            logger.info(f"Matchmaking triggered: {resp.json()}")
    except Exception as e:
        logger.error(f"Failed to trigger matchmaking: {e}")


def _log_event(event_type: str, payload: dict, status: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO agent_logs (agent_name, event_type, payload, status) VALUES (?,?,?,?)",
            ("deal_agent", event_type, json.dumps(payload), status),
        )


if __name__ == "__main__":
    uvicorn.run("deal_agent.main:app", host="0.0.0.0", port=8002, reload=True)
