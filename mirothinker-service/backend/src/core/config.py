"""
MiroThinker Online Service - Configuration
Manages all settings via environment variables and .env file.
"""

from pathlib import Path
from typing import List, Dict, Any

from pydantic_settings import BaseSettings
from pydantic import Field


# Model mapping
MODEL_MAP: Dict[str, str] = {
    "qwen-plus": "qwen-plus",
    "qwen-max": "qwen-max",
    "qwen-flash": "qwen-flash",
    "qwen-turbo": "qwen-turbo",
}

# Domain configurations for quality enhancement
DOMAIN_CONFIGS: Dict[str, Dict[str, Any]] = {
    "tech": {
        "keywords": ["AI", "machine learning", "technology", "software", "computer", "算法", "人工智能", "技术"],
        "max_turns": 200,
        "context_keep": 5,
    },
    "finance": {
        "keywords": ["finance", "stock", "investment", "market", "经济", "股票", "投资", "金融"],
        "max_turns": 200,
        "context_keep": 5,
    },
    "health": {
        "keywords": ["health", "medical", "disease", "treatment", "健康", "医疗", "疾病"],
        "max_turns": 200,
        "context_keep": 5,
    },
    "general": {
        "keywords": [],
        "max_turns": 200,
        "context_keep": 5,
    },
}


class Settings(BaseSettings):
    """Application settings loaded from environment and .env file."""
    
    # App
    APP_NAME: str = "MiroThinker"
    APP_VERSION: str = "1.8.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    WORKERS: int = 1
    
    # Alibaba Bailian LLM
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DASHSCOPE_MODEL: str = "qwen-plus"
    
    # Optional: Serper & Jina
    SERPER_API_KEY: str = ""
    JINA_API_KEY: str = ""
    
    # Feishu/Lark Configuration
    LARK_APP_ID: str = ""
    LARK_APP_SECRET: str = ""
    LARK_WEBHOOK_VERIFICATION_TOKEN: str = ""
    LARK_WEBHOOK_ENCRYPT_KEY: str = ""
    
    # Concurrency
    MAX_CONCURRENT_TASKS: int = 2
    
    # Data directories
    DATA_DIR: Path = Path("./data")
    LOGS_DIR: Path = Path("./data/logs")
    CACHE_DIR: Path = Path("./data/cache")
    TRACES_DIR: Path = Path("./data/traces")
    FRONTEND_DIR: Path = Path("./frontend")
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def validate_api_key(self) -> bool:
        """Check if DASHSCOPE_API_KEY is configured."""
        return bool(self.DASHSCOPE_API_KEY and self.DASHSCOPE_API_KEY != "your-api-key-here")
    
    def validate_feishu_config(self) -> bool:
        """Check if Feishu credentials are configured."""
        return bool(self.LARK_APP_ID and self.LARK_APP_SECRET)
    
    def ensure_directories(self):
        """Ensure all data directories exist."""
        for dir_path in [self.DATA_DIR, self.LOGS_DIR, self.CACHE_DIR, self.TRACES_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
