"""Anthropic API router - path-based multi-gateway"""
import json
import logging
from typing import Dict, Any, Optional

import httpx
from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.client import UpstreamClient
from app.api.converter import (
    convert_anthropic_to_openai_request,
    convert_openai_to_anthropic_response,
    convert_openai_stream_to_anthropic,
)
from app.db.database import get_db
from app.db import crud

router = APIRouter()


def _get_request_auth_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if auth_header:
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        if auth_header.startswith("x-api-key "):
            return auth_header[10:]
        return auth_header
    return request.headers.get("x-api-key")


@router.post("/gateway/{gateway_id}/v1/messages")
async def messages(
    gateway_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Anthropic /v1/messages for a specific gateway."""
    token = _get_request_auth_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization or x-api-key header",
        )

    gateway = crud.get_gateway_by_id(db, gateway_id)
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    if gateway.auth_token != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    client = UpstreamClient(gateway.upstream_base_url, gateway.upstream_api_key)
    model_mapping = {gateway.custom_model_name: gateway.upstream_model}

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    anthropic_model = body.get("model", "")
    if not anthropic_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required parameter: model",
        )

    provider_model = model_mapping.get(anthropic_model, anthropic_model)
    openai_request = convert_anthropic_to_openai_request(body)
    openai_request["model"] = provider_model

    stream = body.get("stream", False)
    input_tokens = 0
    output_tokens = 0

    if stream:
        return StreamingResponse(
            stream_messages_with_logging(
                client, openai_request, anthropic_model, gateway_id, db
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    try:
        openai_response = await client.chat_completion(
            model=provider_model,
            messages=openai_request["messages"],
            max_tokens=openai_request.get("max_tokens"),
            temperature=openai_request.get("temperature"),
            top_p=openai_request.get("top_p"),
            stop=openai_request.get("stop"),
        )
    except httpx.HTTPStatusError as e:
        logging.warning(
            "Upstream error: %s %s -> %s",
            e.request.method,
            e.request.url,
            e.response.status_code,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "type": "upstream_error",
                "message": "Upstream provider returned an error",
                "upstream_status": e.response.status_code,
                "upstream_url": str(e.request.url),
            },
        )
    except httpx.RequestError as e:
        logging.warning("Upstream request failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "type": "upstream_error",
                "message": "Could not reach upstream provider",
                "error": str(e),
            },
        )

    anthropic_response = convert_openai_to_anthropic_response(openai_response)
    anthropic_response["model"] = anthropic_model

    usage = openai_response.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    crud.create_request_log(
        db,
        gateway_id=gateway_id,
        method="POST",
        path=f"/gateway/{gateway_id}/v1/messages",
        status_code=200,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    return anthropic_response


async def stream_messages_with_logging(
    client: UpstreamClient,
    openai_request: Dict[str, Any],
    anthropic_model: str,
    gateway_id: int,
    db: Session,
):
    """Stream and accumulate tokens for logging."""
    from app.db.database import SessionLocal
    # Use a new session for logging inside generator
    message_start = {
        "type": "message_start",
        "message": {
            "id": "msg_temp",
            "type": "message",
            "role": "assistant",
            "content": [],
            "model": anthropic_model,
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        },
    }
    yield f"event: message_start\ndata: {json.dumps(message_start)}\n\n"

    content_block_start = {
        "type": "content_block_start",
        "index": 0,
        "content_block": {"type": "text", "text": ""},
    }
    yield f"event: content_block_start\ndata: {json.dumps(content_block_start)}\n\n"

    input_tokens = 0
    output_tokens = 0
    status_code = 200

    try:
        async for line in client.stream_chat_completion(
            model=openai_request["model"],
            messages=openai_request["messages"],
            max_tokens=openai_request.get("max_tokens"),
            temperature=openai_request.get("temperature"),
            top_p=openai_request.get("top_p"),
            stop=openai_request.get("stop"),
        ):
            # Try to parse usage from OpenAI stream (first chunk often has usage)
            try:
                if line.startswith("data: ") and line != "data: [DONE]":
                    data = json.loads(line[6:])
                    choices = data.get("choices", [])
                    if choices and "usage" in data:
                        u = data["usage"]
                        input_tokens = u.get("prompt_tokens", 0)
                    if choices:
                        delta = choices[0].get("delta", {})
                        if "content" in delta:
                            output_tokens += len(delta["content"].split())  # approximate
            except (json.JSONDecodeError, KeyError):
                pass
            anthropic_line = convert_openai_stream_to_anthropic(line)
            if anthropic_line:
                yield anthropic_line
    except Exception as e:
        status_code = 500
        error_event = {
            "type": "error",
            "error": {"type": "server_error", "message": str(e)},
        }
        yield f"event: error\ndata: {json.dumps(error_event)}\n\n"

    content_block_stop = {"type": "content_block_stop", "index": 0}
    yield f"event: content_block_stop\ndata: {json.dumps(content_block_stop)}\n\n"
    yield 'event: message_stop\ndata: {"type":"message_stop"}\n\n'

    try:
        log_db = SessionLocal()
        crud.create_request_log(
            log_db,
            gateway_id=gateway_id,
            method="POST",
            path=f"/gateway/{gateway_id}/v1/messages",
            status_code=status_code,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        log_db.close()
    except Exception:
        pass
