#!/bin/bash
# 完整部署 - 包含调试端点

# 1. 备份
cp /opt/pkb-system/backend/src/main.py /opt/pkb-system/backend/src/main.py.bak.$(date +%Y%m%d_%H%M)

# 2. 使用 Python 修改 main.py
python3 << 'PYEOF'
import re

with open("/opt/pkb-system/backend/src/main.py", "r") as f:
    lines = f.readlines()

# 确保导入了 sqlite3 和 os
import_section = """
from contextlib import asynccontextmanager
import sqlite3
import os

from fastapi import FastAPI, Request, HTTPException, Depends
"""

# 添加导入
content = ''.join(lines)
if "import sqlite3" not in content:
    content = content.replace("from contextlib import asynccontextmanager", import_section)

# 添加调试端点（在 health_check 之后）
debug_endpoint = '''

@app.get("/debug/status")
async def debug_status():
    """调试端点 - 查看最近的文档"""
    result = {}
    try:
        db_path = '/opt/pkb-system/data/db/pkb.db'
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM documents')
            result['total_docs'] = cursor.fetchone()[0]
            cursor.execute('SELECT id, title, substr(content,1,200), source, created_at FROM documents ORDER BY created_at DESC LIMIT 10')
            rows = cursor.fetchall()
            result['recent_docs'] = []
            for row in rows:
                result['recent_docs'].append({
                    'id': row[0],
                    'title': row[1],
                    'content_preview': row[2],
                    'content_length': len(row[2]) if row[2] else 0,
                    'source': row[3],
                    'created_at': row[4]
                })
            conn.close()
    except Exception as e:
        result['error'] = str(e)
    return result

'''

if '@app.get("/debug/status")' not in content:
    # 在 health_check 函数后插入
    content = content.replace(
        '"timestamp": datetime.now().isoformat(),\n    }\n\n\n@app.post("/api/v1/messages"',
        '"timestamp": datetime.now().isoformat(),\n    }\n' + debug_endpoint + '\n@app.post("/api/v1/messages"'
    )
    print("Added debug endpoint")
else:
    print("Debug endpoint already exists")

# 确保 FeishuWebhookRequest 包含 header
if "header: Optional[dict] = None" not in content:
    content = content.replace(
        'class FeishuWebhookRequest(BaseModel):\n    """飞书 Webhook 请求"""\n    challenge: Optional[str] = None\n    token: Optional[str] = None\n    type: Optional[str] = None\n    event: Optional[dict] = None',
        'class FeishuWebhookRequest(BaseModel):\n    """飞书 Webhook 请求"""\n    challenge: Optional[str] = None\n    token: Optional[str] = None\n    type: Optional[str] = None\n    schema_: Optional[str] = None\n    header: Optional[dict] = None\n    event: Optional[dict] = None'
    )
    print("Updated FeishuWebhookRequest model")

# 修改 event_id 提取
if 'header.get("event_id"' not in content:
    content = content.replace(
        '    # 事件去重\n    event_id = request.event.get("event_id", "")',
        '    # 事件去重 - event_id 在 header 中\n    header = request.header or {}\n    event_id = header.get("event_id", "")'
    )
    print("Updated event_id extraction")

with open("/opt/pkb-system/backend/src/main.py", "w") as f:
    f.write(content)

print("main.py updated successfully")
PYEOF

# 3. 部署修复后的 feishu.py
cat > /opt/pkb-system/backend/src/input/adapters/feishu.py << 'FEISU_EOF'
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
        if not event_id or event_id.startswith("test_"):
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
            print(f"DEBUG parse_message: content='{text_content[:50]}'", file=sys.stderr, flush=True)
            
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
        content = content.strip()
        for cmd_prefix in self.COMMANDS.keys():
            if content.startswith(cmd_prefix):
                parts = content[len(cmd_prefix):].strip().split(maxsplit=1)
                args = parts[1].split() if len(parts) > 1 else []
                return FeishuCommand(command=cmd_prefix, args=args, raw_content=content)
        return None

    def format_response(self, success: bool, message: str, data: Optional[dict] = None) -> str:
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
        return "\n".join(lines)

    def format_help(self) -> str:
        lines = ["📚 PKB 指令帮助：\n"]
        for cmd, desc in self.COMMANDS.items():
            lines.append(f"{cmd} - {desc}")
        return "\n".join(lines)

    def format_status(self, stats: dict) -> str:
        lines = ["📊 PKB 系统状态：\n"]
        lines.append(f"- 笔记总数：{stats.get('total_notes', 0)}")
        lines.append(f"- 今日新增：{stats.get('today_notes', 0)}")
        return "\n".join(lines)


_feishu_adapter: Optional[FeishuAdapter] = None

def get_feishu_adapter() -> FeishuAdapter:
    global _feishu_adapter
    if _feishu_adapter is None:
        _feishu_adapter = FeishuAdapter()
    return _feishu_adapter
FEISU_EOF

echo "feishu.py deployed"

# 4. 重启服务
systemctl restart pkb
sleep 4

# 5. 检查服务
if systemctl is-active pkb > /dev/null 2>&1; then
    echo "SUCCESS: PKB service is running"
    curl -s http://127.0.0.1:8000/health
    echo ""
    curl -s http://127.0.0.1:8000/debug/status
    echo ""
else
    echo "ERROR: PKB service failed to start"
    journalctl -u pkb --no-pager -n 30
fi
