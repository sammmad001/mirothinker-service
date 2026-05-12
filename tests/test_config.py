"""
配置模块测试
"""
import pytest
from pathlib import Path

from backend.src.core.config import get_settings


class TestConfig:
    """配置测试"""

    @pytest.fixture
    def settings(self):
        """获取配置"""
        return get_settings()

    def test_settings_loaded(self, settings):
        """测试配置加载"""
        assert settings.API_HOST is not None
        assert settings.API_PORT is not None
        assert settings.DATABASE_URL is not None

    def test_api_config(self, settings):
        """测试 API 配置"""
        assert isinstance(settings.API_HOST, str)
        assert isinstance(settings.API_PORT, int)
        assert settings.API_PORT > 0

    def test_database_config(self, settings):
        """测试数据库配置"""
        assert "sqlite" in settings.DATABASE_URL

    def test_ollama_config(self, settings):
        """测试 Ollama 配置"""
        assert settings.OLLAMA_BASE_URL is not None
        assert settings.OLLAMA_MODEL is not None

    def test_log_config(self, settings):
        """测试日志配置"""
        assert settings.LOG_DIR is not None
        assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_data_paths(self, settings):
        """测试数据路径"""
        data_dir = settings.get_data_dir()
        assert isinstance(data_dir, Path)

        raw_dir = settings.get_raw_dir()
        assert isinstance(raw_dir, Path)

        wiki_dir = settings.get_wiki_dir()
        assert isinstance(wiki_dir, Path)
