"""HTTP client for forwarding requests to upstream provider"""
import httpx
from typing import Dict, Any, AsyncIterator
from app.config import settings


class UpstreamClient:
    """Async HTTP client for communicating with upstream OpenAI-compatible provider"""
    
    def __init__(self):
        self.base_url = settings.upstream_base_url.rstrip('/')
        self.api_key = settings.upstream_api_key
        self.timeout = httpx.Timeout(60.0, connect=10.0)
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers for upstream API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(
        self,
        model: str,
        messages: list,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send non-streaming chat completion request to upstream provider
        
        Args:
            model: Model name
            messages: List of messages
            stream: Must be False for this method
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Response dict
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        
        headers = await self._get_headers()
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def stream_chat_completion(
        self,
        model: str,
        messages: list,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat completion from upstream provider
        
        Yields:
            SSE-formatted lines from the upstream provider
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            **kwargs
        }
        
        headers = await self._get_headers()
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                url,
                json=payload,
                headers=headers
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield line
