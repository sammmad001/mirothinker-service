"""
MiroThinker - Centralized Configuration Management
Loads and validates environment variables, provides typed config access.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = Field(default="MiroThinker Online Service", alias="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", alias="APP_VERSION")
    DEBUG: bool = Field(default=False, alias="DEBUG")
    HOST: str = Field(default="0.0.0.0", alias="HOST")
    PORT: int = Field(default=8000, alias="PORT")
    WORKERS: int = Field(default=1, alias="WORKERS")

    # DashScope LLM
    DASHSCOPE_API_KEY: str = Field(default="", alias="DASHSCOPE_API_KEY")
    DASHSCOPE_BASE_URL: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="DASHSCOPE_BASE_URL"
    )

    # Legacy API Keys (optional, for backward compatibility)
    SERPER_API_KEY: str = Field(default="", alias="SERPER_API_KEY")
    JINA_API_KEY: str = Field(default="", alias="JINA_API_KEY")

    # Model Configuration
    DEFAULT_MODEL: str = Field(default="qwen-plus", alias="DEFAULT_MODEL")
    DEFAULT_TEMPERATURE: float = Field(default=0.7, alias="DEFAULT_TEMPERATURE")
    DEFAULT_MAX_TURNS: int = Field(default=200, alias="DEFAULT_MAX_TURNS")
    DEFAULT_CONTEXT_KEEP: int = Field(default=5, alias="DEFAULT_CONTEXT_KEEP")

    # Concurrency
    MAX_CONCURRENT_TASKS: int = Field(default=2, alias="MAX_CONCURRENT_TASKS")

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["*"], alias="CORS_ORIGINS")

    # Data Directories
    DATA_DIR: Path = Field(default=Path("data"), alias="DATA_DIR")
    TRACES_DIR: Path = Field(default=Path("data/traces"), alias="TRACES_DIR")
    LOGS_DIR: Path = Field(default=Path("data/logs"), alias="LOGS_DIR")
    CACHE_DIR: Path = Field(default=Path("data/cache"), alias="CACHE_DIR")

    # Frontend
    FRONTEND_DIR: Path = Field(default=Path("frontend"), alias="FRONTEND_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

    def validate_api_key(self) -> bool:
        """Validate that required API keys are configured."""
        return bool(self.DASHSCOPE_API_KEY and self.DASHSCOPE_API_KEY.strip())

    def ensure_directories(self) -> None:
        """Create data directories if they don't exist."""
        for directory in [self.DATA_DIR, self.TRACES_DIR, self.LOGS_DIR, self.CACHE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency injector for settings."""
    return settings


# === Constants (moved from original main.py) ===

MODEL_MAP = {
    "qwen-turbo": "qwen-turbo",
    "qwen-flash": "qwen-flash",
    "qwen-plus": "qwen-plus",
    "qwen-max": "qwen-max",
}

CORE_SOURCES = {
    "academic": {
        "name": "学术信源",
        "search_template": "site:scholar.google.com OR site:arxiv.org OR site:pubmed.ncbi.nlm.nih.gov {query}",
        "priority": "highest",
    },
    "tech": {
        "name": "技术信源",
        "search_template": "site:github.com OR site:stackoverflow.com OR site:docs.python.org {query}",
        "priority": "high",
    },
    "news": {
        "name": "新闻信源",
        "search_template": "site:reuters.com OR site:apnews.com OR site:bbc.com/news {query}",
        "priority": "high",
    },
    "data": {
        "name": "数据信源",
        "search_template": "site:data.worldbank.org OR site:imf.org OR site:data.stats.gov.cn {query}",
        "priority": "medium",
    },
}

DOMAIN_CONFIGS = {
    "tech": {
        "name": "技术/科技",
        "core_sources": ["github.com", "stackoverflow.com", "arxiv.org"],
        "keywords": ["AI", "机器学习", "深度学习", "Python", "软件", "算法", "区块链", "AI/ML", "software", "algorithm"],
        "prompt_variant": "technical",
    },
    "finance": {
        "name": "金融/经济",
        "core_sources": ["reuters.com", "bloomberg.com", "imf.org", "worldbank.org"],
        "keywords": ["经济", "金融", "GDP", "通胀", "投资", "股市", "市场", "economy", "finance", "investment", "market"],
        "prompt_variant": "data_driven",
    },
    "health": {
        "name": "医疗/健康",
        "core_sources": ["pubmed.ncbi.nlm.nih.gov", "nature.com", "who.int"],
        "keywords": ["医疗", "健康", "疾病", "药物", "治疗", "疫苗", "临床", "medical", "health", "disease", "treatment"],
        "prompt_variant": "evidence_based",
    },
    "general": {
        "name": "综合",
        "core_sources": [],
        "keywords": [],
        "prompt_variant": "general",
    },
}
