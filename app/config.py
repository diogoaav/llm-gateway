"""Configuration management"""
import os


class Settings:
    """Application settings loaded from environment variables"""

    def __init__(self):
        # Admin login (for UI)
        self.admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_password: str = os.getenv("ADMIN_PASSWORD", "")

    def validate(self) -> bool:
        """Validate that required settings are present (for UI mode)."""
        if not self.admin_password:
            raise ValueError(
                "ADMIN_PASSWORD environment variable is required for UI login"
            )
        return True


settings = Settings()
