"""
LLM wrapper for Sarvam AI (OpenAI-compatible endpoint)
Falls back gracefully if API key is missing (returns mock response for dev)
"""
import logging
from typing import Optional
from openai import OpenAI
from . import config

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def get_llm_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=config.SARVAM_API_KEY or "dummy-key",
            base_url=config.SARVAM_BASE_URL,
        )
    return _client


def chat_complete(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """Call Sarvam LLM and return text response"""
    if not config.SARVAM_API_KEY:
        logger.warning("SARVAM_API_KEY not set — returning mock LLM response")
        return f"[MOCK LLM] System: {system_prompt[:80]}... | User: {user_prompt[:80]}..."

    client = get_llm_client()
    try:
        response = client.chat.completions.create(
            model=config.SARVAM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise


def chat_complete_history(system_prompt: str, chat_history: list, temperature: float = 0.7) -> str:
    """Call Sarvam LLM with a full conversation history"""
    if not config.SARVAM_API_KEY:
        logger.warning("SARVAM_API_KEY not set — returning mock LLM response")
        return f"[MOCK LLM] System: {system_prompt[:80]}... | History Length: {len(chat_history)}"

    client = get_llm_client()
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)

    try:
        response = client.chat.completions.create(
            model=config.SARVAM_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise
