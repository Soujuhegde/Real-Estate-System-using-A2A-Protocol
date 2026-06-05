"""
Agent 3: Marketing Intelligence Agent
A2A Server — Port 8003
Generates LLM-powered insights and stores them in Pinecone (RAG)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import logging
from fastapi import FastAPI
import uvicorn

from shared.a2a_models import (
    A2ATaskRequest, A2ATaskResponse, A2ATaskStatus,
    A2AMessage, A2AArtifact, A2APart, AgentCard, AgentSkill,
)
from shared.db import init_db, get_conn
from .intelligence import generate_insights
from .embeddings import embed_and_store, is_already_processed

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("marketing_agent")

app = FastAPI(title="Marketing Intelligence Agent", version="1.0.0")

AGENT_CARD = AgentCard(
    name="Marketing Intelligence Agent",
    description=(
        "Generates AI-powered market intelligence for real estate properties. "
        "Produces trend analysis, risk signals, and ROI insights. Stores results in RAG pipeline."
    ),
    url="http://localhost:8003",
    skills=[
        AgentSkill(
            id="generate_market_insights",
            name="Generate Market Insights",
            description="Analyze a property and produce market trends, risk signals, and opportunity insights",
            input_schema={
                "type": "object",
                "required": ["property_id"],
                "properties": {
                    "property_id": {"type": "string"},
                    "location": {"type": "string"},
                    "property_type": {"type": "string"},
                    "price": {"type": "number"},
                },
            },
        ),
        AgentSkill(
            id="query_insights",
            name="Query Market Insights",
            description="Retrieve stored market insights for a property using RAG",
            input_schema={
                "type": "object",
                "required": ["query"],
                "properties": {"query": {"type": "string"}, "property_id": {"type": "string"}},
            },
        ),
    ],
)


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Marketing Intelligence Agent started on port 8003")


@app.get("/.well-known/agent.json")
async def agent_card():
    return AGENT_CARD.model_dump()


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "marketing_intelligence"}


@app.post("/tasks/send", response_model=A2ATaskResponse)
async def handle_task(request: A2ATaskRequest):
    task_id = request.id
    user_text = request.message.parts[0].text if request.message.parts else ""
    logger.info(f"[Task {task_id}] Received marketing request")

    try:
        try:
            payload = json.loads(user_text)
        except json.JSONDecodeError:
            payload = {"query": user_text, **(request.metadata or {})}

        # Route to insight generation or query
        if "property_id" in payload and "query" not in payload:
            return await _handle_generate(task_id, payload)
        elif "query" in payload:
            return await _handle_query(task_id, payload)
        else:
            return A2ATaskResponse(
                id=task_id,
                status=A2ATaskStatus(
                    state="failed",
                    message=A2AMessage.agent("Provide 'property_id' (generate) or 'query' (retrieve)"),
                ),
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


async def _handle_generate(task_id: str, payload: dict) -> A2ATaskResponse:
    property_id = payload["property_id"]

    if is_already_processed(property_id):
        logger.info(f"Property {property_id} already analyzed — skipping duplicate")
        _log_event("DUPLICATE_SKIP", {"property_id": property_id}, "skipped")
        return A2ATaskResponse(
            id=task_id,
            status=A2ATaskStatus(
                state="completed",
                message=A2AMessage.agent(
                    f"Insights for {property_id} already exist in the knowledge base."
                ),
            ),
        )

    logger.info(f"Generating insights for property {property_id}...")
    insights = generate_insights(payload)
    _log_event("INSIGHTS_GENERATED", {"property_id": property_id}, "success")

    # Store in SQLite + embed in Pinecone
    insight_ids = _persist_insights(property_id, insights)
    embed_and_store(property_id, insights)
    _log_event("EMBEDDINGS_STORED", {"property_id": property_id, "count": len(insights)}, "success")

    summary = "\n".join(
        f"• [{i['type'].upper()}] {i['content'][:120]}..." for i in insights
    )
    return A2ATaskResponse(
        id=task_id,
        status=A2ATaskStatus(
            state="completed",
            message=A2AMessage.agent(
                f"Generated {len(insights)} insights for property {property_id}:\n{summary}"
            ),
        ),
        artifacts=[
            A2AArtifact(
                name="market_insights",
                parts=[A2APart(text=json.dumps(insights))],
                metadata={"property_id": property_id, "insight_count": len(insights)},
            )
        ],
    )


async def _handle_query(task_id: str, payload: dict) -> A2ATaskResponse:
    from .embeddings import query_insights
    query = payload["query"]
    property_id = payload.get("property_id")
    logger.info(f"RAG query: '{query}' | property_id={property_id}")

    results = query_insights(query, property_id=property_id, top_k=5)
    if not results:
        return A2ATaskResponse(
            id=task_id,
            status=A2ATaskStatus(
                state="completed",
                message=A2AMessage.agent("No relevant insights found for your query."),
            ),
        )

    context = "\n".join(f"- {r['content']}" for r in results)
    return A2ATaskResponse(
        id=task_id,
        status=A2ATaskStatus(
            state="completed",
            message=A2AMessage.agent(context),
        ),
        artifacts=[
            A2AArtifact(
                name="retrieved_insights",
                parts=[A2APart(text=json.dumps(results))],
                metadata={"query": query, "result_count": len(results)},
            )
        ],
    )


def _persist_insights(property_id: str, insights: list) -> list:
    import uuid as _uuid
    ids = []
    with get_conn() as conn:
        for item in insights:
            iid = f"INS-{str(_uuid.uuid4())[:8].upper()}"
            conn.execute(
                "INSERT INTO market_insights (insight_id, property_id, insight_type, content) VALUES (?,?,?,?)",
                (iid, property_id, item["type"], item["content"]),
            )
            ids.append(iid)
    return ids


def _log_event(event_type: str, payload: dict, status: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO agent_logs (agent_name, event_type, payload, status) VALUES (?,?,?,?)",
            ("marketing_agent", event_type, json.dumps(payload), status),
        )


if __name__ == "__main__":
    uvicorn.run("marketing_agent.main:app", host="0.0.0.0", port=8003, reload=True)
