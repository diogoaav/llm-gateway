"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import anthropic_router
from app.middleware import auth_middleware
from app.config import settings

# Validate settings on startup
try:
    settings.validate()
except ValueError as e:
    print(f"Configuration error: {e}")
    raise

# Create FastAPI app
app = FastAPI(
    title="LLM Gateway",
    description="Anthropic to OpenAI API Gateway",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
@app.middleware("http")
async def auth_middleware_wrapper(request, call_next):
    return await auth_middleware(request, call_next)

# Include routers
app.include_router(anthropic_router.router)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LLM Gateway",
        "version": "1.0.0",
        "status": "running"
    }
