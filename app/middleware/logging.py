"""Request logging middleware - logs request method, path, and response status."""
import time
from fastapi import Request


async def request_logging_middleware(request: Request, call_next):
    """Log gateway API requests to stdout."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    if request.url.path.startswith("/gateway/"):
        print(f"{request.method} {request.url.path} {response.status_code} {duration:.2f}s")
    return response
