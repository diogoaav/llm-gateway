"""Anthropic API router"""
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import json

from app.client import UpstreamClient
from app.api.converter import (
    convert_anthropic_to_openai_request,
    convert_openai_to_anthropic_response,
    convert_openai_stream_to_anthropic
)
from app.config import settings

router = APIRouter()
client = UpstreamClient()


@router.post("/v1/messages")
async def messages(request: Request):
    """
    Handle Anthropic /v1/messages endpoint
    
    Converts Anthropic request to OpenAI format, forwards to upstream provider,
    and converts response back to Anthropic format.
    """
    try:
        # Parse request body
        body = await request.json()
        
        # Get model name and map it to provider model
        anthropic_model = body.get("model", "")
        if not anthropic_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameter: model"
            )
        
        provider_model = settings.get_provider_model(anthropic_model)
        
        # Convert Anthropic request to OpenAI format
        openai_request = convert_anthropic_to_openai_request(body)
        openai_request["model"] = provider_model
        
        # Check if streaming is requested
        stream = body.get("stream", False)
        
        if stream:
            # Handle streaming response
            return StreamingResponse(
                stream_messages(openai_request, anthropic_model),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # Handle non-streaming response
            openai_response = await client.chat_completion(
                model=provider_model,
                messages=openai_request["messages"],
                stream=False,
                max_tokens=openai_request.get("max_tokens"),
                temperature=openai_request.get("temperature"),
                top_p=openai_request.get("top_p"),
                stop=openai_request.get("stop"),
            )
            
            # Convert OpenAI response to Anthropic format
            anthropic_response = convert_openai_to_anthropic_response(openai_response)
            # Override model name to return the original Anthropic model name
            anthropic_response["model"] = anthropic_model
            
            return anthropic_response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


async def stream_messages(openai_request: Dict[str, Any], anthropic_model: str):
    """
    Stream messages from upstream provider and convert to Anthropic format
    
    Args:
        openai_request: OpenAI-formatted request
        anthropic_model: Original Anthropic model name to return in response
    
    Yields:
        SSE-formatted lines in Anthropic format
    """
    # Send initial message_start event (Anthropic format)
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
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0
            }
        }
    }
    yield f"event: message_start\ndata: {json.dumps(message_start)}\n\n"
    
    # Send content_block_start event
    content_block_start = {
        "type": "content_block_start",
        "index": 0,
        "content_block": {
            "type": "text",
            "text": ""
        }
    }
    yield f"event: content_block_start\ndata: {json.dumps(content_block_start)}\n\n"
    
    # Stream from upstream provider
    try:
        async for line in client.stream_chat_completion(
            model=openai_request["model"],
            messages=openai_request["messages"],
            max_tokens=openai_request.get("max_tokens"),
            temperature=openai_request.get("temperature"),
            top_p=openai_request.get("top_p"),
            stop=openai_request.get("stop"),
        ):
            # Convert OpenAI stream line to Anthropic format
            anthropic_line = convert_openai_stream_to_anthropic(line)
            if anthropic_line:
                yield anthropic_line
        
        # Send content_block_stop event
        content_block_stop = {
            "type": "content_block_stop",
            "index": 0
        }
        yield f"event: content_block_stop\ndata: {json.dumps(content_block_stop)}\n\n"
        
        # Send message_stop event
        yield "event: message_stop\ndata: {\"type\":\"message_stop\"}\n\n"
    
    except Exception as e:
        # Send error event if streaming fails
        error_event = {
            "type": "error",
            "error": {
                "type": "server_error",
                "message": str(e)
            }
        }
        yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
