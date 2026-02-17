"""Conversion logic between Anthropic and OpenAI API formats"""
from typing import List, Dict, Any, Optional, Iterator
import json


def convert_anthropic_to_openai_request(anthropic_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Anthropic API request format to OpenAI format
    
    Anthropic format:
    {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "system": "You are a helpful assistant",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "stop_sequences": ["\n\n"],
        "stream": true
    }
    
    OpenAI format:
    {
        "model": "anthropic-claude-4.5-sonnet",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"}
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.9,
        "stop": ["\n\n"],
        "stream": true
    }
    """
    openai_request: Dict[str, Any] = {
        "model": anthropic_request.get("model", ""),
        "messages": []
    }
    
    # Add system message if present
    if "system" in anthropic_request and anthropic_request["system"]:
        openai_request["messages"].append({
            "role": "system",
            "content": anthropic_request["system"]
        })
    
    # Convert messages array
    anthropic_messages = anthropic_request.get("messages", [])
    for msg in anthropic_messages:
        openai_msg = {
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        }
        openai_request["messages"].append(openai_msg)
    
    # Map parameters
    if "max_tokens" in anthropic_request:
        openai_request["max_tokens"] = anthropic_request["max_tokens"]
    
    if "temperature" in anthropic_request:
        openai_request["temperature"] = anthropic_request["temperature"]
    
    if "top_p" in anthropic_request:
        openai_request["top_p"] = anthropic_request["top_p"]
    
    # top_k is not supported in OpenAI, skip it
    if "top_k" in anthropic_request:
        # Log warning or silently drop
        pass
    
    # Convert stop_sequences to stop
    if "stop_sequences" in anthropic_request and anthropic_request["stop_sequences"]:
        openai_request["stop"] = anthropic_request["stop_sequences"]
    
    # Preserve stream parameter
    if "stream" in anthropic_request:
        openai_request["stream"] = anthropic_request["stream"]
    
    return openai_request


def convert_openai_to_anthropic_response(openai_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert OpenAI API response format to Anthropic format
    
    OpenAI format:
    {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "anthropic-claude-4.5-sonnet",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you?"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 9,
            "completion_tokens": 12,
            "total_tokens": 21
        }
    }
    
    Anthropic format:
    {
        "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "Hello! How can I help you?"
            }
        ],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "end_turn",
        "stop_sequence": null,
        "usage": {
            "input_tokens": 9,
            "output_tokens": 12
        }
    }
    """
    if not openai_response.get("choices") or len(openai_response["choices"]) == 0:
        raise ValueError("OpenAI response missing choices")
    
    choice = openai_response["choices"][0]
    message = choice.get("message", {})
    content = message.get("content", "")
    
    # Convert finish_reason
    finish_reason = choice.get("finish_reason", "stop")
    anthropic_stop_reason = "end_turn" if finish_reason == "stop" else finish_reason
    
    # Build Anthropic response
    anthropic_response = {
        "id": openai_response.get("id", ""),
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": content
            }
        ],
        "model": openai_response.get("model", ""),
        "stop_reason": anthropic_stop_reason,
        "stop_sequence": None
    }
    
    # Convert usage
    if "usage" in openai_response:
        usage = openai_response["usage"]
        anthropic_response["usage"] = {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0)
        }
    
    return anthropic_response


def convert_openai_stream_to_anthropic(openai_stream_line: str) -> Optional[str]:
    """
    Convert a single OpenAI streaming response line to Anthropic format
    
    OpenAI streaming format (SSE):
    data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0125","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}
    
    Anthropic streaming format (SSE):
    event: message_start
    data: {"type":"message_start","message":{"id":"msg_01XFDUDYJgAACzvnptvVoYEL","type":"message","role":"assistant","content":[],"model":"claude-3-5-sonnet-20241022","stop_reason":null,"stop_sequence":null,"usage":{"input_tokens":10,"output_tokens":0}}}
    
    event: content_block_start
    data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}
    
    event: content_block_delta
    data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Hello"}}
    
    event: content_block_stop
    data: {"type":"content_block_stop","index":0}
    
    event: message_delta
    data: {"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":null}}
    
    event: message_stop
    data: {"type":"message_stop"}
    """
    if not openai_stream_line.strip():
        return None
    
    # Skip non-data lines
    if not openai_stream_line.startswith("data: "):
        return None
    
    # Extract JSON data
    json_str = openai_stream_line[6:]  # Remove "data: " prefix
    
    if json_str.strip() == "[DONE]":
        return "event: message_stop\ndata: {\"type\":\"message_stop\"}\n\n"
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return None
    
    # Handle different OpenAI stream event types
    if data.get("object") == "chat.completion.chunk":
        choices = data.get("choices", [])
        if not choices:
            return None
        
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason = choice.get("finish_reason")
        
        # If there's content in delta, emit content_block_delta
        if "content" in delta and delta["content"]:
            content_delta = {
                "type": "content_block_delta",
                "index": 0,
                "delta": {
                    "type": "text_delta",
                    "text": delta["content"]
                }
            }
            return f"event: content_block_delta\ndata: {json.dumps(content_delta)}\n\n"
        
        # If finish_reason is set, emit message_delta and message_stop
        if finish_reason:
            message_delta = {
                "type": "message_delta",
                "delta": {
                    "stop_reason": "end_turn" if finish_reason == "stop" else finish_reason,
                    "stop_sequence": None
                }
            }
            return f"event: message_delta\ndata: {json.dumps(message_delta)}\n\nevent: message_stop\ndata: {{\"type\":\"message_stop\"}}\n\n"
    
    return None


def convert_openai_stream_chunk(chunk_data: Dict[str, Any]) -> List[str]:
    """
    Convert OpenAI streaming chunk to Anthropic streaming events
    Returns a list of SSE-formatted strings
    """
    events = []
    
    if chunk_data.get("object") == "chat.completion.chunk":
        choices = chunk_data.get("choices", [])
        if not choices:
            return events
        
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason = choice.get("finish_reason")
        
        # Emit content delta if present
        if "content" in delta and delta["content"]:
            content_delta = {
                "type": "content_block_delta",
                "index": 0,
                "delta": {
                    "type": "text_delta",
                    "text": delta["content"]
                }
            }
            events.append(f"event: content_block_delta\ndata: {json.dumps(content_delta)}\n\n")
        
        # Handle finish
        if finish_reason:
            message_delta = {
                "type": "message_delta",
                "delta": {
                    "stop_reason": "end_turn" if finish_reason == "stop" else finish_reason,
                    "stop_sequence": None
                }
            }
            events.append(f"event: message_delta\ndata: {json.dumps(message_delta)}\n\n")
            events.append("event: message_stop\ndata: {\"type\":\"message_stop\"}\n\n")
    
    return events
