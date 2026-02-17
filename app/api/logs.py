"""Logs API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.schemas import RequestLogResponse
from app.auth.auth import api_login_required

router = APIRouter(prefix="/api", tags=["logs"])


@router.get("/logs", response_model=List[RequestLogResponse])
async def list_logs(
    gateway_id: Optional[int] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: str = Depends(api_login_required),
):
    return crud.get_request_logs(db, gateway_id=gateway_id, limit=limit, offset=offset)
