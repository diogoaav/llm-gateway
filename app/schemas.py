"""Pydantic schemas for API"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class GatewayCreate(BaseModel):
    name: str
    upstream_base_url: str
    upstream_api_key: str
    upstream_model: str
    custom_model_name: str


class GatewayUpdate(BaseModel):
    name: Optional[str] = None
    upstream_base_url: Optional[str] = None
    upstream_api_key: Optional[str] = None
    upstream_model: Optional[str] = None
    custom_model_name: Optional[str] = None


class GatewayResponse(BaseModel):
    id: int
    name: str
    upstream_base_url: str
    upstream_model: str
    custom_model_name: str
    auth_token: str
    created_at: datetime

    class Config:
        from_attributes = True


class RequestLogResponse(BaseModel):
    id: int
    gateway_id: int
    method: str
    path: str
    status_code: Optional[int]
    input_tokens: int
    output_tokens: int
    total_tokens: int
    created_at: datetime

    class Config:
        from_attributes = True


class TokenUsageResponse(BaseModel):
    id: int
    gateway_id: int
    date: date
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_count: int

    class Config:
        from_attributes = True


class LoginForm(BaseModel):
    username: str
    password: str
