"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import anthropic_router
from app.api import gateways, logs, stats
from app.ui.routes import router as ui_router
from app.middleware.logging import request_logging_middleware
from app.config import settings
from app.db.database import init_db

try:
    settings.validate()
except ValueError as e:
    print(f"Configuration error: {e}")
    raise

app = FastAPI(
    title="LLM Gateway",
    description="Anthropic to OpenAI API Gateway",
    version="2.0.0",
)


@app.on_event("startup")
async def startup_event():
    init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_wrapper(request, call_next):
    return await request_logging_middleware(request, call_next)


app.include_router(anthropic_router.router)
app.include_router(gateways.router)
app.include_router(logs.router)
app.include_router(stats.router)
app.include_router(ui_router)

app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {
        "service": "LLM Gateway",
        "version": "2.0.0",
        "status": "running",
        "ui": "/dashboard",
    }
