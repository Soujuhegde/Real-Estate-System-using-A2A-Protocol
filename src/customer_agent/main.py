"""
Agent 1: Customer Onboarding Agent
A2A Server — Port 8001
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import logging
import uuid
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
import uvicorn

from shared.a2a_models import (
    A2ATaskRequest, A2ATaskResponse, A2ATaskStatus,
    A2AMessage, A2AArtifact, A2APart, AgentCard, AgentSkill,
)
from shared.db import init_db, get_conn
from .handlers import onboard_customer, validate_customer_input

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("customer_agent")

app = FastAPI(title="Customer Onboarding Agent", version="1.0.0")

AGENT_CARD = AgentCard(
    name="Customer Onboarding Agent",
    description="Collects, validates, and persists real estate buyer/investor profiles. Returns a unique Customer ID.",
    url="http://localhost:8001",
    skills=[
        AgentSkill(
            id="onboard_customer",
            name="Onboard Customer",
            description="Validate and register a new buyer or investor profile",
            input_schema={
                "type": "object",
                "required": ["full_name", "email", "buyer_type", "budget_min", "budget_max"],
                "properties": {
                    "full_name": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "phone": {"type": "string"},
                    "buyer_type": {"type": "string", "enum": ["buyer", "investor", "both"]},
                    "budget_min": {"type": "number"},
                    "budget_max": {"type": "number"},
                    "preferred_locations": {"type": "array", "items": {"type": "string"}},
                },
            },
        )
    ],
)


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Customer Onboarding Agent started on port 8001")


@app.get("/.well-known/agent.json")
async def agent_card():
    return AGENT_CARD.model_dump()


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "customer_onboarding"}


from shared import config

async def verify_token(x_internal_token: str = Header(None)):
    if x_internal_token != config.INTERNAL_API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid Internal API Token")

@app.post("/tasks/send", response_model=A2ATaskResponse, dependencies=[Depends(verify_token)])
async def handle_task(request: A2ATaskRequest):
    task_id = request.id
    user_text = request.message.parts[0].text if request.message.parts else ""
    logger.info(f"[Task {task_id}] Received: {user_text[:120]}")

    try:
        # Parse JSON payload from message text
        try:
            payload = json.loads(user_text)
        except json.JSONDecodeError:
            # Try to extract from metadata
            payload = request.metadata or {}

        errors = validate_customer_input(payload)
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

        customer_id = onboard_customer(payload)
        _log_event("CUSTOMER_ONBOARDED", {"customer_id": customer_id, **payload}, "success")

        artifact_data = json.dumps({"customer_id": customer_id, "status": "onboarded"})
        return A2ATaskResponse(
            id=task_id,
            status=A2ATaskStatus(
                state="completed",
                message=A2AMessage.agent(
                    f"Customer successfully onboarded. Customer ID: {customer_id}"
                ),
            ),
            artifacts=[
                A2AArtifact(
                    name="customer_profile",
                    parts=[A2APart(text=artifact_data)],
                    metadata={"customer_id": customer_id},
                )
            ],
        )

    except Exception as e:
        logger.exception(f"[Task {task_id}] Unexpected error")
        _log_event("ERROR", {"error": str(e)}, "failed")
        return A2ATaskResponse(
            id=task_id,
            status=A2ATaskStatus(
                state="failed",
                message=A2AMessage.agent(f"Internal error: {str(e)}"),
                error=str(e),
            ),
        )


def _log_event(event_type: str, payload: dict, status: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO agent_logs (agent_name, event_type, payload, status) VALUES (?,?,?,?)",
            ("customer_agent", event_type, json.dumps(payload), status),
        )


if __name__ == "__main__":
    uvicorn.run("customer_agent.main:app", host="0.0.0.0", port=8001, reload=True)
