import logging
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Watchtower API"
    
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    GOOGLE_PAGESPEED_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    SCAN_INTERVAL_HOURS: int = 24
    MAX_CONCURRENT_SCANS: int = 5
    
    model_config = SettingsConfigDict(env_file=".env")

def setup_logging():
    """Setup logging configuration"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ]
    )

settings = Settings()