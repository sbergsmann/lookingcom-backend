"""Application configuration management"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Metadata
    app_name: str = "CapCorn API Wrapper"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # CapCorn API Configuration
    capcorn_base_url: str = "https://mainframe.capcorn.net/RestService"
    capcorn_system: str
    capcorn_user: str
    capcorn_password: str
    capcorn_hotel_id: str
    capcorn_pin: str
    
    # CORS
    cors_origins: str = "*"
    
    # Logfire Configuration
    logfire_api_key: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
