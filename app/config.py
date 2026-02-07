"""
Application configuration from environment variables.
"""
import os
from typing import Optional


class Config:
    """Application configuration."""
    
    # Database
    DB_URL: str = os.environ.get("PVAPP_DB_URL", "sqlite:///./db.sqlite3")
    
    # XML Parser Microservice
    XML_PARSER_URL: Optional[str] = os.environ.get("XML_PARSER_URL")
    XML_PARSER_TOKEN: Optional[str] = os.environ.get("XML_PARSER_TOKEN")
    
    # Parser timeout (seconds)
    XML_PARSER_TIMEOUT: int = int(os.environ.get("XML_PARSER_TIMEOUT", "30"))


config = Config()
