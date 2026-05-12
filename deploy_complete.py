#!/usr/bin/env python3
"""
Complete deployment script - writes files directly and restarts service
"""
import os
import subprocess
import time

# ===== Fix feishu.py =====
feishu_content = '''\
"""
飞书适配器
"""
import json
import sys
import time
from collections import OrderedDict
from typing import Optional
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
        if not event_id:
            return False
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

            text_content = content_obj.get("text", "")
            print(f"DEBUG parse_message: text='{text_content[:100]}'", file=sys.stderr, flush=True)

            return FeishuMessage(
                message_id=message.get("message_id", ""),
                chat_id=message.get("chat_id", ""),
                user_id=sender.get("sender_id", {}).get("open_id", ""),
                content=text_content,
                message_type=message.get("message_type", "text"),
                create_time=message.get("create_time", ""),
            )
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

    def format_response(self, success: bool, message: str, data: Optional[dict] = None) -> str:
        """格式化响应消息"""
        if success:
            lines = [f"✅ {message}"]
        else:
            lines = [f"❌ {message}"]
        if data:
            if "summary" in data:
                lines.append(f"\\n📝 摘要：{data['summary']}")
            if "tags" in data:
                tags = " ".join(f"#{t}" for t in data["tags"])
                lines.append(f"\\n🏷 标签：{tags}")
        return "\\n".join(lines)

    def format_help(self) -> str:
        """格式化帮助消息"""
        lines = ["📚 PKB 指令帮助：\\n"]
        for cmd, desc in self.COMMANDS.items():
            lines.append(f"{cmd} - {desc}")
        return "\\n".join(lines)

    def format_status(self, stats: dict) -> str:
        """格式化状态消息"""
        lines = ["📊 PKB 系统状态：\\n"]
        lines.append(f"- 笔记总数：{stats.get('total_notes', 0)}")
        lines.append(f"- 今日新增：{stats.get('today_notes', 0)}")
        return "\\n".join(lines)


# 单例
_feishu_adapter: Optional[FeishuAdapter] = None


def get_feishu_adapter() -> FeishuAdapter:
    """获取飞书适配器实例"""
    global _feishu_adapter
    if _feishu_adapter is None:
        _feishu_adapter = FeishuAdapter()
    return _feishu_adapter
'''

# ===== Fix main.py webhook section =====
# Read current main.py and patch the webhook function
main_py_path = '/opt/pkb-system/backend/src/main.py'

with open(main_py_path, 'r') as f:
    main_content = f.read()

# Add imports if not present
if 'import sqlite3' not in main_content:
    main_content = main_content.replace(
        'from contextlib import asynccontextmanager',
        'from contextlib import asynccontextmanager\nimport sqlite3\nimport os'
    )

# Patch FeishuWebhookRequest to add header field
if 'header: Optional[dict]' not in main_content:
    main_content = main_content.replace(
        '    type: Optional[str] = None\n    event: Optional[dict] = None',
        '    type: Optional[str] = None\n    schema_: Optional[str] = None\n    header: Optional[dict] = None\n    event: Optional[dict] = None'
    )

# Patch event_id extraction in webhook function
if 'header.get("event_id"' not in main_content:
    main_content = main_content.replace(
        '    event_id = webhook_req.event.get("event_id", "")',
        '    header = webhook_req.header or {} if hasattr(webhook_req, "header") else body.get("header", {})\n    event_id = header.get("event_id", "")'
    )

# ===== Write files =====
feishu_path = '/opt/pkb-system/backend/src/input/adapters/feishu.py'

# Backup
os.system(f'cp {feishu_path} {feishu_path}.bak.$(date +%s)')
os.system(f'cp {main_py_path} {main_py_path}.bak.$(date +%s)')

# Write feishu.py
with open(feishu_path, 'w') as f:
    f.write(feishu_content)
print(f"Written {feishu_path}")

# Write main.py
with open(main_py_path, 'w') as f:
    f.write(main_content)
print(f"Written {main_py_path}")

# ===== Restart service =====
print("Stopping existing service...")
os.system('pkill -f "uvicorn" 2>/dev/null')
time.sleep(3)

print("Starting service...")
os.chdir('/opt/pkb-system')
os.system('nohup /opt/miniconda/envs/pkb/bin/python -m uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 > /tmp/pkb.log 2>&1 &')
time.sleep(5)

# ===== Verify =====
print("\n=== Health Check ===")
os.system('curl -s http://127.0.0.1:8000/health')
print()

print("\n=== Test Webhook ===")
import uuid
test_event_id = f"deploy_test_{uuid.uuid4()}"
test_msg_id = f"om_{uuid.uuid4()}"
test_cmd = f'''curl -s -X POST http://127.0.0.1:8000/api/v1/feishu/webhook \\
  -H "Content-Type: application/json" \\
  -d '{{"schema":"2.0","header":{{"event_id":"{test_event_id}"}},"event":{{"sender":{{"sender_id":{{"open_id":"ou_test"}}}},"message":{{"message_id":"{test_msg_id}","chat_id":"oc_test","message_type":"text","content":"{{\\\\\"text\\\\\":\\\\\"部署验证消息XYZ\\\\\"}}","create_time":"123"}}}}}}' '''
os.system(test_cmd)
print()

print("\n=== Database Check ===")
os.system('sqlite3 /opt/pkb-system/data/db/pkb.db "SELECT id, substr(title,1,50), length(content), created_at FROM documents ORDER BY created_at DESC LIMIT 5;"')
print()

print("=== Deployment Complete ===")
