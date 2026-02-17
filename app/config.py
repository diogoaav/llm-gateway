"""Configuration management"""
import os
from pathlib import Path
from typing import Dict, Optional
import json


class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        self.upstream_base_url: str = os.getenv("UPSTREAM_BASE_URL", "")
        self.upstream_api_key: str = os.getenv("UPSTREAM_API_KEY", "")
        self.auth_token: str = os.getenv("AUTH_TOKEN", "")
        self.model_mapping_file: str = os.getenv("MODEL_MAPPING_FILE", "models.json")
        self._model_mapping: Optional[Dict[str, str]] = None
    
    def load_model_mapping(self) -> Dict[str, str]:
        """Load model name mapping from JSON file"""
        if self._model_mapping is not None:
            return self._model_mapping
        
        mapping_path = Path(self.model_mapping_file)
        if not mapping_path.exists():
            # Return empty dict if file doesn't exist
            self._model_mapping = {}
            return self._model_mapping
        
        try:
            with open(mapping_path, 'r') as f:
                self._model_mapping = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # Log error and return empty dict
            print(f"Warning: Failed to load model mapping: {e}")
            self._model_mapping = {}
        
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
        if not self.auth_token:
            raise ValueError("AUTH_TOKEN environment variable is required")
        return True


# Global settings instance
settings = Settings()
