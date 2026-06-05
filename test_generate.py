import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from dotenv import load_dotenv
load_dotenv()

from concierge_agent.graph import generate_response_node

state = {
    "chat_history": [{"role": "user", "content": "Tell me about market trends and demand for villas in Koramangala."}],
    "agent_response": "No relevant insights found for your query.",
    "rag_context": "No relevant insights found for your query.",
}
result = generate_response_node(state)
print("FINAL RESPONSE:", result)
