import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from dotenv import load_dotenv
load_dotenv()

from concierge_agent.graph import classify_intent_node

state = {"user_input": "Tell me about market trends and demand for villas in Koramangala.", "chat_history": [{"role": "user", "content": "Tell me about market trends and demand for villas in Koramangala."}]}
result = classify_intent_node(state)
print("INTENT RESULT:", result)
