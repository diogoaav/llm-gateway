"""Authentication middleware"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings


security = HTTPBearer()


async def verify_auth_token(request: Request) -> bool:
    """
    Verify the Authorization token from request header
    
    Args:
        request: FastAPI request object
    
    Returns:
        True if token is valid
    
    Raises:
        HTTPException if token is invalid or missing
    """
    # Skip auth for health check and root endpoints
    if request.url.path in ["/health", "/"]:
        return True
    
    # Check for token in Authorization header or x-api-key header (Anthropic style)
    token = None
    
    # Try Authorization header first
    auth_header = request.headers.get("Authorization")
    if auth_header:
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        elif auth_header.startswith("x-api-key "):
            token = auth_header[10:]
        else:
            token = auth_header
    
    # Try x-api-key header if Authorization header didn't provide token
    if not token:
        token = request.headers.get("x-api-key")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header or x-api-key header"
        )
    
    # Verify token matches configured AUTH_TOKEN
    if token != settings.auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    return True


async def auth_middleware(request: Request, call_next):
    """Middleware to authenticate requests"""
    try:
        await verify_auth_token(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )
    
    response = await call_next(request)
    return response
