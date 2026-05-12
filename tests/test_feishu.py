"""
飞书适配器测试
"""
import pytest
from unittest.mock import Mock, patch

from backend.src.input import get_feishu_adapter
from backend.src.input.adapters.feishu import FeishuMessage, FeishuCommand


class TestFeishuAdapter:
    """飞书适配器测试"""

    @pytest.fixture
    def adapter(self):
        """获取飞书适配器"""
        return get_feishu_adapter()

    def test_parse_text_message(self, adapter):
        """测试解析文本消息"""
        event = {
            "message": {
                "message_id": "om_test_123",
                "chat_id": "oc_test_chat",
                "message_type": "text",
                "content": '{"text":"测试消息"}',
                "create_time": "1234567890",
            },
            "sender": {
                "sender_id": {"open_id": "ou_test_user"},
                "sender_type": "user",
            },
        }

        message = adapter.parse_message(event)
        assert message is not None
        assert message.content == "测试消息"
        assert message.message_type == "text"

    def test_parse_command_note(self, adapter):
        """测试解析 #note 指令"""
        command = adapter.parse_command("#note 这是一条笔记")
        assert command is not None
        assert command.command == "#note"
        assert "这是一条笔记" in command.raw_content

    def test_parse_command_search(self, adapter):
        """测试解析 #search 指令"""
        command = adapter.parse_command("#search Python异步")
        assert command is not None
        assert command.command == "#search"

    def test_parse_command_status(self, adapter):
        """测试解析 #status 指令"""
        command = adapter.parse_command("#status")
        assert command is not None
        assert command.command == "#status"

    def test_parse_command_help(self, adapter):
        """测试解析 #help 指令"""
        command = adapter.parse_command("#help")
        assert command is not None
        assert command.command == "#help"

    def test_parse_non_command(self, adapter):
        """测试非指令内容"""
        command = adapter.parse_command("普通文本")
        assert command is None

    def test_format_response(self, adapter):
        """测试格式化响应"""
        response = adapter.format_response(
            success=True,
            message="测试成功",
            data={"summary": "测试摘要"}
        )
        assert isinstance(response, str)
        assert "测试成功" in response

    def test_format_help(self, adapter):
        """测试格式化帮助"""
        help_text = adapter.format_help()
        assert isinstance(help_text, str)
        assert "#note" in help_text or "#search" in help_text

    def test_format_status(self, adapter):
        """测试格式化状态"""
        stats = {"total_notes": 10, "today_notes": 2}
        status_text = adapter.format_status(stats)
        assert isinstance(status_text, str)

    def test_dedup(self, adapter):
        """测试事件去重"""
        event_id = "test_event_123"
        assert not adapter.dedup.is_duplicate(event_id)
        assert adapter.dedup.is_duplicate(event_id)
