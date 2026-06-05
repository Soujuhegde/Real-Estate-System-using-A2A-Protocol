"""
Agent Discovery — Fetches Agent Cards from all registered specialist agents
"""
import logging
from typing import Dict, Optional
from shared.a2a_client import A2AClient
from shared.a2a_models import AgentCard
from shared import config

logger = logging.getLogger("concierge.discovery")


async def discover_all_agents() -> Dict[str, AgentCard]:
    """Discover all specialist agents from the registry"""
    client = A2AClient()
    discovered: Dict[str, AgentCard] = {}

    for agent_name, agent_url in config.AGENT_REGISTRY.items():
        card = await client.discover(agent_url)
        if card:
            discovered[agent_name] = card
            logger.info(f"✓ Discovered: {card.name} at {agent_url}")
        else:
            logger.warning(f"✗ Could not discover agent: {agent_name} at {agent_url}")

    return discovered


async def get_agent_health() -> Dict[str, bool]:
    """Health check all registered agents"""
    client = A2AClient()
    health = {}
    for name, url in config.AGENT_REGISTRY.items():
        health[name] = await client.health_check(url)
    return health
