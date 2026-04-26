import httpx
from fastapi import APIRouter, HTTPException, Response

from backend.app.core.config import get_settings
from backend.app.core.dependencies import CurrentUser, RedisClient
from backend.app.schemas.chat import ChatCompletionsRequest

router = APIRouter(prefix="/chat", tags=["Chat"])

RATE_LIMIT = 5
RATE_WINDOW = 60


@router.post("/completions")
async def chat_completions(payload: ChatCompletionsRequest, current_user: CurrentUser, redis: RedisClient):
    # ── 限流 ─────────────────────────────────────────
    if redis is None:
        raise HTTPException(status_code=503, detail="Rate limiting unavailable: Redis not configured")

    rate_key = f"ratelimit:{current_user.id}"
    count = await redis.incr(rate_key)
    if count == 1:
        await redis.expire(rate_key, RATE_WINDOW)
    if count > RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: max {RATE_LIMIT} requests per {RATE_WINDOW}s",
        )

    # ── 转发给 LiteLLM（注意 /v1） ───────────────────
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{get_settings().litellm_base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {get_settings().litellm_master_key}"},
            json=payload.model_dump(),
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )