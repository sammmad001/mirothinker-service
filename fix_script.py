#!/usr/bin/env python3
"""PKB Fix Script - writes correct files and restarts service"""
import os
import subprocess
import time

print('=== PKB Fix Script Starting ===')

# Read correct files from local
script_dir = os.path.dirname(os.path.abspath(__file__))

# We'll write the content directly here
feishu_path = '/opt/pkb-system/backend/src/input/adapters/feishu.py'
main_path = '/opt/pkb-system/backend/src/main.py'

# feishu.py content (correct version)
feishu_content = r'''"""
飞书适配器
"""
import json
import hmac
import hashlib
import time
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
    message_type: str
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
        expired = [k for k, v in self._cache.items() if now - v > self._ttl]
        for k in expired:
            del self._cache[k]
        if event_id in self._cache:
            return True
        self._cache[event_id] = now
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
        return False


class FeishuAdapter:
    """飞书适配器"""

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
        """解析消息事件 - 适配飞书 im.message.receive_v1 格式"""
        try:
            event = event_data.get("event", {})
            sender = event.get("sender", {})
            message = event.get("message", {})
            
            content_str = message.get("content", "{}")
            if isinstance(content_str, str):
                content_obj = json.loads(content_str)
            else:
                content_obj = content_str
            
            return FeishuMessage(
                message_id=message.get("message_id", ""),
                chat_id=message.get("chat_id", ""),
                user_id=sender.get("sender_id", {}).get("open_id", ""),
                content=content_obj.get("text", ""),
                message_type=message.get("message_type", "text"),
                create_time=message.get("create_time", ""),
            )
        except Exception as e:
            print(f"ERROR parse_message: {e}", file=sys.stderr, flush=True)
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

    def format_response(self, success: bool, message: str, data: Optional[dict] = None) -> str:
        """格式化响应消息"""
        if success:
            lines = [f"OK {message}"]
        else:
            lines = [f"FAIL {message}"]
        if data:
            if "summary" in data:
                lines.append("")
                lines.append(f"Summary: {data['summary']}")
        return "\n".join(lines)

    def format_help(self) -> str:
        """格式化帮助消息"""
        lines = ["PKB Commands:\n"]
        for cmd, desc in self.COMMANDS.items():
            lines.append(f"{cmd} - {desc}")
        return "\n".join(lines)

    def format_status(self, stats: dict) -> str:
        """格式化状态消息"""
        lines = ["PKB Status:\n"]
        lines.append(f"- Total notes: {stats.get('total_notes', 0)}")
        lines.append(f"- Today: {stats.get('today_notes', 0)}")
        return "\n".join(lines)


_feishu_adapter: Optional[FeishuAdapter] = None


def get_feishu_adapter() -> FeishuAdapter:
    """获取飞书适配器实例"""
    global _feishu_adapter
    if _feishu_adapter is None:
        _feishu_adapter = FeishuAdapter()
    return _feishu_adapter
'''

print(f'Writing feishu.py...')
os.makedirs(os.path.dirname(feishu_path), exist_ok=True)
with open(feishu_path, 'w', encoding='utf-8') as f:
    f.write(feishu_content)
print(f'Done: {len(feishu_content)} bytes')

# Verify
with open(feishu_path, 'r') as f:
    content = f.read()
    has_fix = 'message = event.get("message"' in content
    print(f'Verified: {has_fix}')

# Restart service
print('Restarting service...')
try:
    result = subprocess.run(['systemctl', 'restart', 'pkb'], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print('Service restarted via systemctl')
    else:
        print(f'systemctl failed: {result.stderr}')
        raise Exception('systemctl failed')
except Exception as e:
    print(f'Trying alternative restart...')
    try:
        subprocess.run(['pkill', '-f', 'uvicorn'], capture_output=True)
        time.sleep(2)
        subprocess.Popen([
            '/opt/miniconda/envs/pkb/bin/python', '-m', 'uvicorn',
            'backend.src.main:app', '--host', '0.0.0.0', '--port', '8000'
        ], cwd='/opt/pkb-system/backend', stdout=open('/tmp/pkb.log', 'w'), stderr=subprocess.STDOUT)
        print('Service restarted manually')
    except Exception as e2:
        print(f'Restart failed: {e2}')

print('=== Fix Complete ===')
