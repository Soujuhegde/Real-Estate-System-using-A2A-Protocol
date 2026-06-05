"""
A2A Protocol HTTP Client
Used by the Concierge to communicate with specialist agents
"""
import httpx
import logging
from typing import Optional, Dict, Any
from .a2a_models import A2ATaskRequest, A2ATaskResponse, A2AMessage, AgentCard

logger = logging.getLogger(__name__)


class A2AClient:
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def discover(self, agent_url: str) -> Optional[AgentCard]:
        """Fetch an agent's Agent Card from /.well-known/agent.json"""
        url = f"{agent_url.rstrip('/')}/.well-known/agent.json"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                return AgentCard(**resp.json())
            except Exception as e:
                logger.error(f"Agent discovery failed for {agent_url}: {e}")
                return None

    async def send_task(
        self,
        agent_url: str,
        message_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> A2ATaskResponse:
        """Send a task to a specialist agent and return response"""
        endpoint = f"{agent_url.rstrip('/')}/tasks/send"
        request = A2ATaskRequest(
            message=A2AMessage.user(message_text),
            metadata=metadata or {},
        )
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(endpoint, json=request.model_dump())
                resp.raise_for_status()
                return A2ATaskResponse(**resp.json())
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error from agent {agent_url}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Task send failed to {agent_url}: {e}")
                raise

    async def health_check(self, agent_url: str) -> bool:
        """Check if an agent is reachable"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.get(f"{agent_url.rstrip('/')}/health")
                return resp.status_code == 200
            except Exception:
                return False
