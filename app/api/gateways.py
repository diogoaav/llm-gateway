"""Gateway CRUD API"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.schemas import GatewayCreate, GatewayUpdate, GatewayResponse
from app.auth.auth import api_login_required

router = APIRouter(prefix="/api", tags=["gateways"])


@router.get("/gateways", response_model=List[GatewayResponse])
async def list_gateways(
    db: Session = Depends(get_db),
    _: str = Depends(api_login_required),
):
    return crud.get_all_gateways(db)


@router.post("/gateways", response_model=GatewayResponse)
async def create_gateway(
    body: GatewayCreate,
    db: Session = Depends(get_db),
    _: str = Depends(api_login_required),
):
    return crud.create_gateway(
        db,
        name=body.name,
        upstream_base_url=body.upstream_base_url,
        upstream_api_key=body.upstream_api_key,
        upstream_model=body.upstream_model,
        custom_model_name=body.custom_model_name,
    )


@router.get("/gateways/{gateway_id}", response_model=GatewayResponse)
async def get_gateway(
    gateway_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(api_login_required),
):
    gateway = crud.get_gateway_by_id(db, gateway_id)
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return gateway


@router.patch("/gateways/{gateway_id}", response_model=GatewayResponse)
async def update_gateway(
    gateway_id: int,
    body: GatewayUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(api_login_required),
):
    gateway = crud.update_gateway(
        db,
        gateway_id,
        name=body.name,
        upstream_base_url=body.upstream_base_url,
        upstream_api_key=body.upstream_api_key,
        upstream_model=body.upstream_model,
        custom_model_name=body.custom_model_name,
    )
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return gateway


@router.delete("/gateways/{gateway_id}")
async def delete_gateway(
    gateway_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(api_login_required),
):
    if not crud.delete_gateway(db, gateway_id):
        raise HTTPException(status_code=404, detail="Gateway not found")
    return {"ok": True}
