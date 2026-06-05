"""
LLM wrapper for Sarvam AI (OpenAI-compatible endpoint)
Falls back gracefully if API key is missing (returns mock response for dev)
"""
import logging
from typing import Optional
from openai import OpenAI
import json
import base64
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

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
            max_tokens=4096,
        )
        msg = response.choices[0].message
        content = msg.content or getattr(msg, 'reasoning_content', '') or ''
        return content.strip()
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
            max_tokens=4096,
        )
        msg = response.choices[0].message
        content = msg.content or getattr(msg, 'reasoning_content', '') or ''
        return content.strip()
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise


def analyze_property_image(image_base64: str) -> dict:
    """Analyze a property image using Gemini Vision API"""
    if not config.GEMINI_API_KEY or genai is None:
        logger.warning("GEMINI_API_KEY not set or google-genai not installed. Returning mock vision response.")
        return {
            "extracted_amenities": ["Hardwood Floors (Mock)", "Pool (Mock)", "Modern Kitchen (Mock)"],
            "marketing_description": "A stunning mockup property featuring luxurious modern finishes and beautiful natural lighting."
        }
    
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        image_bytes = base64.b64decode(image_base64)
        
        prompt = """
        Analyze this property image. 
        Extract any visible amenities (e.g. pool, hardwood floors, modern kitchen).
        Write a short, captivating marketing description (2-3 sentences).
        Return EXACTLY a JSON object with this format:
        {
          "extracted_amenities": ["amenity1", "amenity2"],
          "marketing_description": "..."
        }
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                prompt,
                types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Vision API call failed: {e}")
        return {
            "extracted_amenities": [],
            "marketing_description": f"Failed to analyze image automatically."
        }
