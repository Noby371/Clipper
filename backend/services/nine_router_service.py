import logging
import json
import re
from typing import List, Dict, Any, Optional
import httpx
from backend.schemas.analyze import VideoAnalysis

logger = logging.getLogger("cheatclip.nine_router")

# Default local endpoint - can be overridden by user
DEFAULT_NINE_ROUTER_BASE_URL = "http://localhost:8000/v1"


async def fetch_nine_router_models(
    api_key: str = "",
    base_url: str = DEFAULT_NINE_ROUTER_BASE_URL
) -> List[Dict[str, Any]]:
    """
    Fetch available models from a local 9router or OpenRouter-compatible endpoint.
    """
    models_url = f"{base_url.rstrip('/')}/models"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(models_url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                models_list = data.get("data", [])
                
                # Normalize model format
                normalized = []
                for m in models_list:
                    model_id = m.get("id", "")
                    model_name = m.get("name", model_id)
                    context_len = m.get("context_length", 0)
                    description = m.get("description", "")
                    
                    normalized.append({
                        "id": model_id,
                        "name": model_name,
                        "context_length": context_len,
                        "description": description[:120] if description else ""
                    })
                
                return normalized
            else:
                logger.warning(f"9router models endpoint returned status {resp.status_code}")
    except Exception as exc:
        logger.warning(f"Error fetching 9router models: {exc}")

    # Return empty list if connection fails
    return []


async def analyze_with_nine_router(
    api_key: str,
    model_name: str,
    prompt: str,
    base_url: str = DEFAULT_NINE_ROUTER_BASE_URL,
    timeout: float = 120.0
) -> VideoAnalysis:
    """
    Execute a structured JSON video analysis request against local 9router endpoint.
    Compatible with OpenAI/OpenRouter API format.
    """
    completions_url = f"{base_url.rstrip('/')}/chat/completions"
    
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key.strip()}"

    system_instruction = (
        "You are an expert viral video clipper and AI retention analyst. "
        "Analyze the provided video transcript and select the highest engagement clips. "
        "Strict rules:\n"
        "1. STRICT ZERO-TRANSLATION RULE: Output titles, key_quotes, and summary in the EXACT SAME LANGUAGE as the video transcript.\n"
        "2. ZERO FIRST-PERSON PRONOUNS: Never use 'I', 'me', 'my', 'aku', 'saya' in titles or suggestions. Attribute the quote or insight to the speaker/host by name or use third-person objective framing.\n"
        "3. You MUST respond ONLY with a valid JSON object matching this schema:\n"
        "{\n"
        '  "summary": "1-2 sentence video summary in the exact transcript language, followed by 2-4 hashtags",\n'
        '  "clips": [\n'
        "    {\n"
        '      "title": "Snappy title under 8 words attributing speaker",\n'
        '      "start_time": 10.0,\n'
        '      "end_time": 45.0,\n'
        '      "hook_time": 12.0,\n'
        '      "virality_score": 92,\n'
        '      "key_quotes": ["quote 1", "quote 2"],\n'
        '      "title_suggestion": "Alternative viral hook title",\n'
        '      "caption_suggestion": "Social media post caption",\n'
        '      "hashtag_suggestion": "#hashtag1 #hashtag2"\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    # Add response_format if the endpoint supports it
    try:
        payload["response_format"] = {"type": "json_object"}
    except Exception:
        pass

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(completions_url, headers=headers, json=payload)
        
        if resp.status_code != 200:
            err_text = resp.text
            try:
                err_json = resp.json()
                err_msg = err_json.get("error", {}).get("message", err_text)
            except Exception:
                err_msg = err_text
            raise RuntimeError(f"9router API Error ({resp.status_code}): {err_msg}")

        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("9router returned empty choices array.")

        content = choices[0].get("message", {}).get("content", "").strip()
        if not content:
            raise ValueError("9router returned empty message content.")

        # Robust JSON extraction
        parsed_dict = None
        try:
            parsed_dict = json.loads(content)
        except Exception:
            # Check for ```json ... ``` code fence
            fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if fence_match:
                parsed_dict = json.loads(fence_match.group(1))
            else:
                # Find outermost { ... }
                bracket_match = re.search(r'\{[\s\S]*\}', content)
                if bracket_match:
                    parsed_dict = json.loads(bracket_match.group(0))
                else:
                    raise ValueError(f"Could not parse valid JSON from 9router output: {content[:200]}...")

        # Coerce and validate through VideoAnalysis model
        return VideoAnalysis.model_validate(parsed_dict)
