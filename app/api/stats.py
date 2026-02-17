"""Statistics and token usage API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.schemas import TokenUsageResponse
from app.auth.auth import api_login_required

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats/usage", response_model=List[TokenUsageResponse])
async def token_usage(
    gateway_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: str = Depends(api_login_required),
):
    return crud.get_token_usage(db, gateway_id=gateway_id, days=days)


@router.get("/stats/gateway/{gateway_id}/totals")
async def gateway_totals(
    gateway_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(api_login_required),
):
    gateway = crud.get_gateway_by_id(db, gateway_id)
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return crud.get_gateway_totals(db, gateway_id)
