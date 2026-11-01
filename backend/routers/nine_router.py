import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header

from backend.services.nine_router_service import (
    fetch_nine_router_models,
    analyze_with_nine_router,
)
from backend.schemas.analyze import VideoAnalysis

logger = logging.getLogger("cheatclip.nine_router_router")
router = APIRouter(tags=["NineRouter"])

DEFAULT_NINE_ROUTER_BASE_URL = "http://localhost:8000/v1"


@router.get("/api/nine-router-models")
async def get_nine_router_models(
    api_key: str = "",
    x_ninerouter_api_key: Optional[str] = Header(None, alias="X-NineRouter-API-Key"),
    x_ninerouter_endpoint: Optional[str] = Header(None, alias="X-NineRouter-Endpoint"),
):
    """
    Fetch list of available models from local 9router or OpenRouter-compatible endpoint.
    Accepts API key via X-NineRouter-API-Key header or query param.
    """
    token_from_header = x_ninerouter_api_key or api_key or ""
    base_url = x_ninerouter_endpoint or DEFAULT_NINE_ROUTER_BASE_URL
    
    try:
        models = await fetch_nine_router_models(token_from_header, base_url)
        return {"models": models}
    except Exception as e:
        logger.error(f"Failed to fetch 9router models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


@router.post("/api/nine-router-analyze")
async def analyze_with_nine_router_endpoint(
    prompt: str,
    model: str = "default-model",
    api_key: str = "",
    x_ninerouter_api_key: Optional[str] = Header(None, alias="X-NineRouter-API-Key"),
    x_ninerouter_endpoint: Optional[str] = Header(None, alias="X-NineRouter-Endpoint"),
):
    """
    Execute video analysis via local 9router endpoint.
    Compatible with OpenAI/OpenRouter chat completions format.
    """
    token_from_header = x_ninerouter_api_key or api_key or ""
    base_url = x_ninerouter_endpoint or DEFAULT_NINE_ROUTER_BASE_URL

    if not prompt or not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")

    try:
        result = await analyze_with_nine_router(
            api_key=token_from_header,
            model_name=model,
            prompt=prompt,
            base_url=base_url,
            timeout=120.0
        )
        return {
            "summary": result.summary,
            "clips": [clip.model_dump() for clip in result.clips],
            "models_used": model,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"9router analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
