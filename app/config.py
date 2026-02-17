"""Configuration management"""
import os
import secrets
from typing import Dict, Optional


class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        self.upstream_base_url: str = os.getenv("UPSTREAM_BASE_URL", "")
        self.upstream_api_key: str = os.getenv("UPSTREAM_API_KEY", "")
        
        # Auto-generate AUTH_TOKEN if not provided
        self.auth_token: str = os.getenv("AUTH_TOKEN", "")
        if not self.auth_token:
            # Generate a secure random token (32 bytes = 64 hex characters)
            self.auth_token = secrets.token_urlsafe(32)
            self._auth_token_generated = True
        else:
            self._auth_token_generated = False
        
        # Model mapping from environment variables
        self.custom_model_name: str = os.getenv("CUSTOM_MODEL_NAME", "")
        self.upstream_model: str = os.getenv("UPSTREAM_MODEL", "")
        self._model_mapping: Optional[Dict[str, str]] = None
    
    def load_model_mapping(self) -> Dict[str, str]:
        """Load model name mapping from environment variables"""
        if self._model_mapping is not None:
            return self._model_mapping
        
        self._model_mapping = {}
        
        # If both custom and upstream model names are provided, create mapping
        if self.custom_model_name and self.upstream_model:
            self._model_mapping[self.custom_model_name] = self.upstream_model
        
        return self._model_mapping
    
    def get_provider_model(self, anthropic_model: str) -> str:
        """Get provider model name from Anthropic model name"""
        mapping = self.load_model_mapping()
        return mapping.get(anthropic_model, anthropic_model)
    
    def validate(self) -> bool:
        """Validate that required settings are present"""
        if not self.upstream_base_url:
            raise ValueError("UPSTREAM_BASE_URL environment variable is required")
        if not self.upstream_api_key:
            raise ValueError("UPSTREAM_API_KEY environment variable is required")
        return True


# Global settings instance
settings = Settings()
