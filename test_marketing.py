import sys
import os
import json
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from shared.a2a_client import A2AClient
from shared import config

async def test():
    client = A2AClient()
    payload = {'property_type': 'villas', 'location': 'Koramangala', 'topic': 'market_trends_and_demand', 'query': 'Tell me about market trends and demand for villas in Koramangala.'}
    print("Sending payload:", payload)
    resp = await client.send_task(
        config.MARKETING_AGENT_URL,
        json.dumps(payload),
    )
    print("RESPONSE STATUS:", resp.status.state)
    print("RESPONSE MESSAGE:", resp.status.message.text() if resp.status.message else None)

if __name__ == "__main__":
    asyncio.run(test())
