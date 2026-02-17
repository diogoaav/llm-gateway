"""CRUD operations for gateways and logs"""
from datetime import date, datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import Gateway, RequestLog, TokenUsage


def get_gateway_by_id(db: Session, gateway_id: int) -> Optional[Gateway]:
    return db.query(Gateway).filter(Gateway.id == gateway_id).first()


def get_gateway_by_auth_token(db: Session, auth_token: str) -> Optional[Gateway]:
    return db.query(Gateway).filter(Gateway.auth_token == auth_token).first()


def get_all_gateways(db: Session) -> List[Gateway]:
    return db.query(Gateway).order_by(Gateway.created_at.desc()).all()


def create_gateway(
    db: Session,
    name: str,
    upstream_base_url: str,
    upstream_api_key: str,
    upstream_model: str,
    custom_model_name: str,
    auth_token: Optional[str] = None,
) -> Gateway:
    import secrets
    gateway = Gateway(
        name=name,
        upstream_base_url=upstream_base_url.rstrip("/"),
        upstream_api_key=upstream_api_key,
        upstream_model=upstream_model,
        custom_model_name=custom_model_name,
        auth_token=auth_token or secrets.token_urlsafe(32),
    )
    db.add(gateway)
    db.commit()
    db.refresh(gateway)
    return gateway


def update_gateway(
    db: Session,
    gateway_id: int,
    name: Optional[str] = None,
    upstream_base_url: Optional[str] = None,
    upstream_api_key: Optional[str] = None,
    upstream_model: Optional[str] = None,
    custom_model_name: Optional[str] = None,
) -> Optional[Gateway]:
    gateway = get_gateway_by_id(db, gateway_id)
    if not gateway:
        return None
    if name is not None:
        gateway.name = name
    if upstream_base_url is not None:
        gateway.upstream_base_url = upstream_base_url.rstrip("/")
    if upstream_api_key is not None:
        gateway.upstream_api_key = upstream_api_key
    if upstream_model is not None:
        gateway.upstream_model = upstream_model
    if custom_model_name is not None:
        gateway.custom_model_name = custom_model_name
    gateway.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(gateway)
    return gateway


def delete_gateway(db: Session, gateway_id: int) -> bool:
    gateway = get_gateway_by_id(db, gateway_id)
    if not gateway:
        return False
    db.delete(gateway)
    db.commit()
    return True


def create_request_log(
    db: Session,
    gateway_id: int,
    method: str,
    path: str,
    status_code: int,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> RequestLog:
    total = input_tokens + output_tokens
    log = RequestLog(
        gateway_id=gateway_id,
        method=method,
        path=path,
        status_code=status_code,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total,
    )
    db.add(log)
    today = date.today()
    usage = db.query(TokenUsage).filter(
        TokenUsage.gateway_id == gateway_id,
        TokenUsage.date == today,
    ).first()
    if not usage:
        usage = TokenUsage(
            gateway_id=gateway_id,
            date=today,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            request_count=0,
        )
        db.add(usage)
    usage.input_tokens += input_tokens
    usage.output_tokens += output_tokens
    usage.total_tokens += total
    usage.request_count += 1
    db.commit()
    db.refresh(log)
    return log


def get_request_logs(
    db: Session,
    gateway_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[RequestLog]:
    q = db.query(RequestLog).order_by(RequestLog.created_at.desc())
    if gateway_id is not None:
        q = q.filter(RequestLog.gateway_id == gateway_id)
    return q.offset(offset).limit(limit).all()


def get_token_usage(
    db: Session,
    gateway_id: Optional[int] = None,
    days: int = 30,
) -> List[TokenUsage]:
    since = date.today() - timedelta(days=days)
    q = db.query(TokenUsage).filter(TokenUsage.date >= since).order_by(TokenUsage.date.desc())
    if gateway_id is not None:
        q = q.filter(TokenUsage.gateway_id == gateway_id)
    return q.all()


def get_gateway_totals(db: Session, gateway_id: int) -> dict:
    """Get total tokens and request count for a gateway (all time)."""
    row = db.query(
        func.sum(RequestLog.input_tokens).label("input_tokens"),
        func.sum(RequestLog.output_tokens).label("output_tokens"),
        func.sum(RequestLog.total_tokens).label("total_tokens"),
        func.count(RequestLog.id).label("request_count"),
    ).filter(RequestLog.gateway_id == gateway_id).first()
    return {
        "input_tokens": row.input_tokens or 0,
        "output_tokens": row.output_tokens or 0,
        "total_tokens": row.total_tokens or 0,
        "request_count": row.request_count or 0,
    }
