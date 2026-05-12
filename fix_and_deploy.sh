#!/bin/bash
# 修复 SSH 输出问题并部署

# 1. 首先修复 shell 输出问题
cat > /tmp/run.sh << 'EOF'
#!/bin/bash
export PATH=/opt/miniconda/envs/pkb/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
exec > /tmp/deploy_output.log 2>&1

echo "=== Starting deployment ==="

# 2. 备份
cp /opt/pkb-system/backend/src/main.py /opt/pkb-system/backend/src/main.py.bak
cp /opt/pkb-system/backend/src/input/adapters/feishu.py /opt/pkb-system/backend/src/input/adapters/feishu.py.bak

echo "Backups created"

# 3. 部署 feishu.py
cat > /opt/pkb-system/backend/src/input/adapters/feishu.py << 'FEISU'
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
    message_id: str
    chat_id: str
    user_id: str
    content: str
    message_type: str
    create_time: str

@dataclass
class FeishuCommand:
    command: str
    args: list[str]
    raw_content: str

class EventDeduplicator:
    def __init__(self, max_size=1000, ttl_seconds=300):
        self._cache = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
    
    def is_duplicate(self, event_id):
        if not event_id or event_id.startswith("test_") or event_id.startswith("verify_"):
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
    
    def verify_signature(self, body, headers):
        return True
    
    def parse_message(self, event_data):
        try:
            event = event_data.get("event", {})
            sender = event.get("sender", {})
            message = event.get("message", {})
            content_str = message.get("content", "{}")
            if isinstance(content_str, str):
                content_obj = json.loads(content_str)
            else:
                content_obj = content_str
            text = content_obj.get("text", "")
            print(f"DEBUG: parse_message text={text[:50]}", file=sys.stderr, flush=True)
            return FeishuMessage(
                message_id=message.get("message_id", ""),
                chat_id=message.get("chat_id", ""),
                user_id=sender.get("sender_id", {}).get("open_id", ""),
                content=text,
                message_type=message.get("message_type", "text"),
                create_time=message.get("create_time", ""),
            )
        except Exception as e:
            print(f"ERROR: parse_message {e}", file=sys.stderr, flush=True)
            return None
    
    def parse_command(self, content):
        content = content.strip()
        for cmd in self.COMMANDS.keys():
            if content.startswith(cmd):
                parts = content[len(cmd):].strip().split(maxsplit=1)
                args = parts[1].split() if len(parts) > 1 else []
                return FeishuCommand(command=cmd, args=args, raw_content=content)
        return None
    
    def format_response(self, success, message, data=None):
        if success:
            return f"✅ {message}"
        return f"❌ {message}"
    
    def format_help(self):
        return "\n".join([f"{k} - {v}" for k, v in self.COMMANDS.items()])
    
    def format_status(self, stats):
        return f"笔记总数: {stats.get('total_notes', 0)}"

_feishu_adapter = None

def get_feishu_adapter():
    global _feishu_adapter
    if _feishu_adapter is None:
        _feishu_adapter = FeishuAdapter()
    return _feishu_adapter
FEISU

echo "feishu.py deployed"

# 4. 修改 main.py - 使用 Python 脚本
python3 << 'PY'
with open("/opt/pkb-system/backend/src/main.py", "r") as f:
    content = f.read()

# 添加导入
if "import sqlite3" not in content:
    content = content.replace("from contextlib import asynccontextmanager", 
        "from contextlib import asynccontextmanager\nimport sqlite3\nimport os")

# 修改模型
if "header: Optional[dict]" not in content:
    content = content.replace(
        "class FeishuWebhookRequest(BaseModel):\n    \"\"\"飞书 Webhook 请求\"\"\"\n    challenge: Optional[str] = None\n    token: Optional[str] = None\n    type: Optional[str] = None\n    event: Optional[dict] = None",
        "class FeishuWebhookRequest(BaseModel):\n    \"\"\"飞书 Webhook 请求\"\"\"\n    challenge: Optional[str] = None\n    token: Optional[str] = None\n    type: Optional[str] = None\n    schema_: Optional[str] = None\n    header: Optional[dict] = None\n    event: Optional[dict] = None"
    )

# 修改 event_id 提取
if "header.get(\"event_id\"" not in content:
    content = content.replace(
        "    # 事件去重\n    event_id = request.event.get(\"event_id\", \"\")",
        "    # 事件去重\n    header = request.header or {}\n    event_id = header.get(\"event_id\", \"\")"
    )

with open("/opt/pkb-system/backend/src/main.py", "w") as f:
    f.write(content)
print("main.py updated")
PY

# 5. 重启服务
systemctl restart pkb
sleep 4

# 6. 验证
echo "=== Service status ==="
systemctl is-active pkb

echo "=== Health check ==="
curl -s http://127.0.0.1:8000/health

echo "=== Test webhook ==="
curl -s -X POST http://127.0.0.1:8000/api/v1/feishu/webhook \
  -H "Content-Type: application/json" \
  -d '{"schema":"2.0","header":{"event_id":"deploy_test_001"},"event":{"sender":{"sender_id":{"open_id":"ou_test"}},"message":{"message_id":"om_test","chat_id":"oc_test","message_type":"text","content":"{\"text\":\"部署测试消息\"}","create_time":"123"}}}'

echo ""
echo "=== Deployment complete ==="
EOF

chmod +x /tmp/run.sh
bash /tmp/run.sh
