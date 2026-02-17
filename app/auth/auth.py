"""Login and session management for UI"""
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
import secrets
from app.config import settings

# In-memory session store: session_id -> username (use Redis/DB in production for multi-instance)
sessions: dict[str, str] = {}


def verify_login(username: str, password: str) -> bool:
    return (
        username == settings.admin_username
        and password == settings.admin_password
    )


def create_session(username: str) -> str:
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = username
    return session_id


def get_username_for_session(session_id: Optional[str]) -> Optional[str]:
    if not session_id:
        return None
    return sessions.get(session_id)


def destroy_session(session_id: str) -> None:
    sessions.pop(session_id, None)


async def get_current_user(request: Request) -> Optional[str]:
    """Get current username from cookie or return None."""
    session_id = request.cookies.get("session_id")
    return get_username_for_session(session_id)


async def login_required(request: Request):
    """Dependency: redirect to login if not authenticated (for UI routes)."""
    username = await get_current_user(request)
    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return username


async def api_login_required(request: Request):
    """Dependency: raise 401 if not authenticated (for API routes)."""
    username = await get_current_user(request)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return username
