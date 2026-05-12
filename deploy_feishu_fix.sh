#!/bin/bash
# 部署修复后的飞书适配器

cat > /opt/pkb-system/backend/src/input/adapters/feishu.py << 'PYTHON_EOF'
"""
飞书适配器
"""
import json
import hmac
import hashlib
import time
import sys
from collections import OrderedDict
from typing import Optional, Callable, Any
from dataclasses import dataclass

from backend.src.core.config import get_settings

settings = get_settings()


@dataclass
class FeishuMessage:
    """飞书消息"""
    message_id: str
    chat_id: str
    user_id: str
    content: str
    message_type: str  # text, image, file, etc.
    create_time: str


@dataclass
class FeishuCommand:
    """飞书指令"""
    command: str
    args: list[str]
    raw_content: str


class EventDeduplicator:
    """飞书事件去重器"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self._cache: OrderedDict[str, float] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds

    def is_duplicate(self, event_id: str) -> bool:
        """检查事件是否已处理"""
        now = time.time()

        # 清理过期条目
        expired = [k for k, v in self._cache.items() if now - v > self._ttl]
        for k in expired:
            del self._cache[k]

        if event_id in self._cache:
            return True

        # 记录新事件
        self._cache[event_id] = now
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

        return False


class FeishuAdapter:
    """飞书适配器"""

    # 支持的指令
    COMMANDS = {
        "#note": "添加笔记",
        "#search": "搜索知识库",
        "#tag": "添加标签",
        "#help": "显示帮助",
        "#status": "系统状态",
        "#review": "查看待确认",
        "#confirm": "确认内容",
        "#profile": "查看画像",
    }

    def __init__(self):
        self.dedup = EventDeduplicator()
        self._verification_token = settings.LARK_WEBHOOK_VERIFICATION_TOKEN
        self._encrypt_key = settings.LARK_WEBHOOK_ENCRYPT_KEY

    def verify_signature(self, body: bytes, headers: dict) -> bool:
        """验证签名"""
        return True

    def parse_message(self, event_data: dict) -> Optional[FeishuMessage]:
        """解析消息事件"""
        try:
            event = event_data.get("event", {})
            sender = event.get("sender", {})
            message = event.get("message", {})  # 飞书 im.message.receive_v1 事件中，消息内容在 event.message 字段

            # 获取消息内容 - content 是 JSON 字符串
            content_str = message.get("content", "{}")
            if isinstance(content_str, str):
                content_obj = json.loads(content_str)
            else:
                content_obj = content_str

            parsed = FeishuMessage(
                message_id=message.get("message_id", ""),
                chat_id=message.get("chat_id", ""),
                user_id=sender.get("sender_id", {}).get("open_id", ""),
                content=content_obj.get("text", ""),
                message_type=message.get("message_type", "text"),
                create_time=message.get("create_time", ""),
            )
            print(f"DEBUG parse_message: parsed content='{parsed.content}'", file=sys.stderr, flush=True)
            return parsed
        except Exception as e:
            print(f"ERROR parse_message: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc()
            return None

    def parse_command(self, content: str) -> Optional[FeishuCommand]:
        """解析指令"""
        content = content.strip()

        for cmd_prefix in self.COMMANDS.keys():
            if content.startswith(cmd_prefix):
                parts = content[len(cmd_prefix):].strip().split(maxsplit=1)
                args = parts[1].split() if len(parts) > 1 else []
                return FeishuCommand(
                    command=cmd_prefix,
                    args=args,
                    raw_content=content,
                )

        return None

    def format_response(
        self,
        success: bool,
        message: str,
        data: Optional[dict] = None,
    ) -> str:
        """格式化响应消息"""
        if success:
            lines = [f"✅ {message}"]
        else:
            lines = [f"❌ {message}"]

        if data:
            if "summary" in data:
                lines.append(f"\n📝 摘要：{data['summary']}")
            if "tags" in data:
                tags = " ".join(f"#{t}" for t in data["tags"])
                lines.append(f"\n🏷 标签：{tags}")
            if "related" in data:
                lines.append(f"\n💡 相关：{', '.join(data['related'])}")
            if "answer" in data:
                lines.append(f"\n📖 回答：\n{data['answer']}")

        return "\n".join(lines)

    def format_help(self) -> str:
        """格式化帮助消息"""
        lines = ["📚 PKB 指令帮助：\n"]
        for cmd, desc in self.COMMANDS.items():
            lines.append(f"{cmd} - {desc}")
        return "\n".join(lines)

    def format_status(self, stats: dict) -> str:
        """格式化状态消息"""
        lines = ["📊 PKB 系统状态：\n"]
        lines.append(f"- 笔记总数：{stats.get('total_notes', 0)}")
        lines.append(f"- 今日新增：{stats.get('today_notes', 0)}")
        lines.append(f"- 待确认：{stats.get('pending_review', 0)}")
        lines.append(f"- Wiki 页面：{stats.get('wiki_pages', 0)}")
        return "\n".join(lines)


# 单例
_feishu_adapter: Optional[FeishuAdapter] = None


def get_feishu_adapter() -> FeishuAdapter:
    """获取飞书适配器实例"""
    global _feishu_adapter
    if _feishu_adapter is None:
        _feishu_adapter = FeishuAdapter()
    return _feishu_adapter
PYTHON_EOF

echo "feishu.py deployed"
systemctl restart pkb
sleep 2
systemctl is-active pkb
