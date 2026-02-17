"""SQLAlchemy models"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base  # noqa: I001


class Gateway(Base):
    __tablename__ = "gateways"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    upstream_base_url = Column(String(500), nullable=False)
    upstream_api_key = Column(String(500), nullable=False)
    upstream_model = Column(String(255), nullable=False)
    custom_model_name = Column(String(255), nullable=False)
    auth_token = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    request_logs = relationship("RequestLog", back_populates="gateway")
    token_usage = relationship("TokenUsage", back_populates="gateway")


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    gateway_id = Column(Integer, ForeignKey("gateways.id"), nullable=False)
    method = Column(String(10))
    path = Column(String(500))
    status_code = Column(Integer)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    gateway = relationship("Gateway", back_populates="request_logs")


class TokenUsage(Base):
    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True, index=True)
    gateway_id = Column(Integer, ForeignKey("gateways.id"), nullable=False)
    date = Column(Date, nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    request_count = Column(Integer, default=0)

    gateway = relationship("Gateway", back_populates="token_usage")

    __table_args__ = (UniqueConstraint("gateway_id", "date", name="uq_token_usage_gateway_date"),)
