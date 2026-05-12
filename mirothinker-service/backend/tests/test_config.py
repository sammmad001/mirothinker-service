"""MiroThinker - Configuration Tests"""

import pytest

from src.core.config import Settings, MODEL_MAP, CORE_SOURCES, DOMAIN_CONFIGS


class TestSettings:
    """Test Settings configuration."""

    def test_default_settings(self):
        """Test default settings are loaded correctly."""
        settings = Settings()
        assert settings.APP_NAME == "MiroThinker Online Service"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.WORKERS == 1

    def test_default_model_config(self):
        """Test default model configuration."""
        settings = Settings()
        assert settings.DEFAULT_MODEL == "qwen-plus"
        assert settings.DEFAULT_TEMPERATURE == 0.7
        assert settings.DEFAULT_MAX_TURNS == 200
        assert settings.DEFAULT_CONTEXT_KEEP == 5

    def test_validate_api_key_empty(self):
        """Test API key validation with empty key."""
        settings = Settings(DASHSCOPE_API_KEY="")
        assert settings.validate_api_key() is False

    def test_validate_api_key_whitespace(self):
        """Test API key validation with whitespace."""
        settings = Settings(DASHSCOPE_API_KEY="   ")
        assert settings.validate_api_key() is False

    def test_validate_api_key_valid(self):
        """Test API key validation with valid key."""
        settings = Settings(DASHSCOPE_API_KEY="sk-test-key-12345")
        assert settings.validate_api_key() is True

    def test_ensure_directories(self, tmp_path):
        """Test directory creation."""
        import os
        os.chdir(tmp_path)
        settings = Settings(
            DATA_DIR=tmp_path / "data",
            TRACES_DIR=tmp_path / "data" / "traces",
            LOGS_DIR=tmp_path / "data" / "logs",
            CACHE_DIR=tmp_path / "data" / "cache",
        )
        settings.ensure_directories()
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "traces").exists()
        assert (tmp_path / "data" / "logs").exists()
        assert (tmp_path / "data" / "cache").exists()


class TestConstants:
    """Test constant definitions."""

    def test_model_map(self):
        """Test MODEL_MAP contains expected models."""
        assert "qwen-turbo" in MODEL_MAP
        assert "qwen-flash" in MODEL_MAP
        assert "qwen-plus" in MODEL_MAP
        assert "qwen-max" in MODEL_MAP

    def test_core_sources(self):
        """Test CORE_SOURCES structure."""
        assert "academic" in CORE_SOURCES
        assert "tech" in CORE_SOURCES
        assert "news" in CORE_SOURCES
        assert "data" in CORE_SOURCES

        for source in CORE_SOURCES.values():
            assert "name" in source
            assert "search_template" in source
            assert "priority" in source

    def test_domain_configs(self):
        """Test DOMAIN_CONFIGS structure."""
        assert "tech" in DOMAIN_CONFIGS
        assert "finance" in DOMAIN_CONFIGS
        assert "health" in DOMAIN_CONFIGS
        assert "general" in DOMAIN_CONFIGS

        for domain in DOMAIN_CONFIGS.values():
            assert "name" in domain
            assert "keywords" in domain
            assert "core_sources" in domain
