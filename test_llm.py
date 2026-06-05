import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
load_dotenv()

from shared.llm import chat_complete

try:
    response = chat_complete("You are a helpful assistant.", "Say hello world!")
    print("SUCCESS")
    print(response)
except Exception as e:
    print("ERROR")
    print(str(e))
