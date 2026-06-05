"""
Shared configuration loaded from environment variables
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM (Sarvam AI) ──────────────────────────────────────────────────────────
SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
SARVAM_BASE_URL: str = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai/v1")
SARVAM_MODEL: str = os.getenv("SARVAM_MODEL", "sarvam-m")

# ── Vision API (Gemini) ──────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# ── Vector DB (Pinecone) ─────────────────────────────────────────────────────
PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "realestate-insights")
PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")

# ── Embedding Model ──────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "384"))

# ── Persistence ──────────────────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", "data/db/realestate.db")

# ── Agent Ports ──────────────────────────────────────────────────────────────
CUSTOMER_AGENT_URL: str = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:8001")
DEAL_AGENT_URL: str = os.getenv("DEAL_AGENT_URL", "http://localhost:8002")
MARKETING_AGENT_URL: str = os.getenv("MARKETING_AGENT_URL", "http://localhost:8003")
CONCIERGE_AGENT_URL: str = os.getenv("CONCIERGE_AGENT_URL", "http://localhost:8000")

# Registry for Concierge discovery
AGENT_REGISTRY = {
    "customer_onboarding": CUSTOMER_AGENT_URL,
    "deal_onboarding": DEAL_AGENT_URL,
    "marketing_intelligence": MARKETING_AGENT_URL,
}
