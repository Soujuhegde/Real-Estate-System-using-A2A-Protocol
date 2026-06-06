"""
Concierge Orchestrator — LangGraph StateGraph
Flow: classify_intent → route → specialist_agent → aggregate_response
"""
import logging
import json
import operator
from typing import Optional, TypedDict, Literal, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from shared.a2a_client import A2AClient
from shared import config
from shared.llm import chat_complete, chat_complete_history

logger = logging.getLogger("concierge.graph")


# ── State Schema ─────────────────────────────────────────────────────────────

class OrchestratorState(TypedDict):
    user_input: str
    chat_history: Annotated[list, operator.add]
    intent: str                          # "customer_onboarding" | "deal_onboarding" | "market_insights" | "unknown"
    extracted_payload: dict              # Structured data extracted from user input
    agent_response: Optional[str]        # Raw response from specialist agent
    agent_artifacts: Optional[list]      # Artifacts returned by specialist
    rag_context: Optional[str]           # Retrieved RAG context
    final_response: str                  # Final answer to user
    error: Optional[str]


# ── Nodes ─────────────────────────────────────────────────────────────────────

INTENT_SYSTEM = """You are an intent classifier for a real estate AI platform.
Classify the user's request into exactly one of:
- customer_onboarding  (user wants to register as buyer/investor)
- deal_onboarding      (user wants to list/add a property)
- market_insights      (user asks about property prices, market trends, ROI, risks, or any general real estate questions)
- unknown              (only if the request is completely unrelated to real estate)

Extract structured data from the input as JSON into the 'payload' object.
For customer_onboarding, you must extract: full_name, email, buyer_type (buyer|investor|both), budget_min (number), budget_max (number), phone (string), preferred_locations (array of strings).
For deal_onboarding, you must extract: title, location, property_type (apartment|villa|plot|commercial|office), price (number), area_sqft (number), bedrooms (number), bathrooms (number), owner_name, owner_contact.

CRITICAL: Respond ONLY with a valid JSON object. No markdown, no conversational text.
Format: {"intent": "<intent>", "payload": {<extracted fields>}}
"""


def classify_intent_node(state: OrchestratorState) -> OrchestratorState:
    logger.info("Node: classify_intent")
    user_input = state["user_input"]
    history = state.get("chat_history", [])
    
    # We construct a prompt with the user input at the end of the history
    # If there's history, we use chat_complete_history. Otherwise, regular.
    try:
        if len(history) > 1: # Greater than 1 because it includes the current user input
            raw = chat_complete_history(INTENT_SYSTEM, history, temperature=0.1, json_mode=True)
        else:
            raw = chat_complete(INTENT_SYSTEM, user_input, temperature=0.1, json_mode=True)
            
        raw = raw.strip()
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)
        parsed = json.loads(raw)
        intent = parsed.get("intent", "unknown")
        payload = parsed.get("payload", {})
    except Exception as e:
        logger.warning(f"Intent classification failed: {e}. Defaulting to 'unknown'.")
        intent = "unknown"
        payload = {}

    logger.info(f"Intent classified: {intent} | Payload keys: {list(payload.keys())}")
    return {"intent": intent, "extracted_payload": payload}


async def onboard_customer_node(state: OrchestratorState) -> OrchestratorState:
    logger.info("Node: onboard_customer")
    client = A2AClient()
    payload = state["extracted_payload"]
    try:
        resp = await client.send_task(
            config.CUSTOMER_AGENT_URL,
            json.dumps(payload),
        )
        msg = resp.status.message.text() if resp.status.message else ""
        artifacts = [a.model_dump() for a in (resp.artifacts or [])]
        if resp.status.state == "failed":
            return {"error": resp.status.error or msg, "agent_response": msg}
        return {"agent_response": msg, "agent_artifacts": artifacts}
    except Exception as e:
        return {"error": str(e)}


async def onboard_deal_node(state: OrchestratorState) -> OrchestratorState:
    logger.info("Node: onboard_deal")
    client = A2AClient()
    payload = state["extracted_payload"]
    try:
        resp = await client.send_task(
            config.DEAL_AGENT_URL,
            json.dumps(payload),
        )
        msg = resp.status.message.text() if resp.status.message else ""
        artifacts = [a.model_dump() for a in (resp.artifacts or [])]
        if resp.status.state == "failed":
            return {"error": resp.status.error or msg, "agent_response": msg}
        return {"agent_response": msg, "agent_artifacts": artifacts}
    except Exception as e:
        return {"error": str(e)}


async def query_insights_node(state: OrchestratorState) -> OrchestratorState:
    logger.info("Node: query_insights (RAG)")
    client = A2AClient()
    payload = state["extracted_payload"]
    query = state["user_input"]
    try:
        request_payload = {"query": query, **payload}
        resp = await client.send_task(
            config.MARKETING_AGENT_URL,
            json.dumps(request_payload),
        )
        msg = resp.status.message.text() if resp.status.message else ""
        artifacts = [a.model_dump() for a in (resp.artifacts or [])]
        return {"agent_response": msg, "rag_context": msg, "agent_artifacts": artifacts}
    except Exception as e:
        return {"error": str(e)}


SYNTHESIS_SYSTEM = """You are a helpful real estate concierge AI.
Synthesize the agent's response into a clear, professional, friendly reply for the user.
Keep it concise (3-5 sentences). Highlight key facts (IDs, numbers, risks, opportunities).
Do NOT mention internal agent names or technical details."""


def generate_response_node(state: OrchestratorState) -> OrchestratorState:
    logger.info("Node: generate_response")
    history = state.get("chat_history", [])
    
    if state.get("error"):
        final = f"I encountered an issue processing your request: {state['error']}. Please check your input and try again."
        return {"final_response": final, "chat_history": [{"role": "assistant", "content": final}]}

    agent_resp = state.get("agent_response", "")
    rag_ctx = state.get("rag_context", "")
    context = rag_ctx or agent_resp

    user_prompt = f"Agent Backend Context/Response:\n{context}\n\nPlease generate a natural reply to the user."
    
    # We build a temporary history to pass to the LLM including the context
    temp_history = history.copy()
    temp_history.append({"role": "user", "content": user_prompt})

    try:
        final = chat_complete_history(SYNTHESIS_SYSTEM, temp_history, temperature=0.5)
    except Exception:
        final = agent_resp or "Your request has been processed."

    return {"final_response": final, "chat_history": [{"role": "assistant", "content": final}]}


def handle_unknown_node(state: OrchestratorState) -> OrchestratorState:
    logger.info("Node: handle_unknown")
    final = (
        "I'm your real estate concierge. I can help you with:\n"
        "• **Register as a buyer/investor** — tell me your name, email, budget, and location preferences\n"
        "• **List a property** — share title, location, type, price, and specs\n"
        "• **Market insights** — ask about trends, ROI, or risks for a specific property or area\n\n"
        "What would you like to do?"
    )
    return {"final_response": final, "chat_history": [{"role": "assistant", "content": final}]}


# ── Routing ───────────────────────────────────────────────────────────────────

def route_by_intent(state: OrchestratorState) -> str:
    intent = state.get("intent", "unknown")
    mapping = {
        "customer_onboarding": "onboard_customer",
        "deal_onboarding": "onboard_deal",
        "market_insights": "query_insights",
    }
    return mapping.get(intent, "handle_unknown")


# ── Build Graph ───────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(OrchestratorState)

    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("onboard_customer", onboard_customer_node)
    graph.add_node("onboard_deal", onboard_deal_node)
    graph.add_node("query_insights", query_insights_node)
    graph.add_node("generate_response", generate_response_node)
    graph.add_node("handle_unknown", handle_unknown_node)

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "onboard_customer": "onboard_customer",
            "onboard_deal": "onboard_deal",
            "query_insights": "query_insights",
            "handle_unknown": "handle_unknown",
        },
    )

    graph.add_edge("onboard_customer", "generate_response")
    graph.add_edge("onboard_deal", "generate_response")
    graph.add_edge("query_insights", "generate_response")
    graph.add_edge("generate_response", END)
    graph.add_edge("handle_unknown", END)

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)
