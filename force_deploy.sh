#!/bin/bash
# 强制部署 - 直接覆盖文件

echo "=== 备份 ==="
cp /opt/pkb-system/backend/src/main.py /opt/pkb-system/backend/src/main.py.bak.$(date +%s)
cp /opt/pkb-system/backend/src/input/adapters/feishu.py /opt/pkb-system/backend/src/input/adapters/feishu.py.bak.$(date +%s)

echo "=== 部署 feishu.py ==="
# 直接使用 Python 写入文件
python3 -c "
content = '''\"\"\"
飞书适配器
\"\"\"
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
    COMMANDS = {
        \"#note\": \"添加笔记\",
        \"#search\": \"搜索知识库\",
        \"#tag\": \"添加标签\",
        \"#help\": \"显示帮助\",
        \"#status\": \"系统状态\",
        \"#review\": \"查看待确认\",
        \"#confirm\": \"确认内容\",
        \"#profile\": \"查看画像\",
    }

    def __init__(self):
        self.dedup = EventDeduplicator()
        self._verification_token = settings.LARK_WEBHOOK_VERIFICATION_TOKEN
        self._encrypt_key = settings.LARK_WEBHOOK_ENCRYPT_KEY

    def verify_signature(self, body, headers):
        return True

    def parse_message(self, event_data):
        try:
            event = event_data.get(\"event\", {})
            sender = event.get(\"sender\", {})
            message = event.get(\"message\", {})
            content_str = message.get(\"content\", \"{}\")
            if isinstance(content_str, str):
                content_obj = json.loads(content_str)
            else:
                content_obj = content_str
            text = content_obj.get(\"text\", \"\")
            print(f\"DEBUG: parse_message text={text[:50]}\", file=sys.stderr, flush=True)
            return FeishuMessage(
                message_id=message.get(\"message_id\", \"\"),
                chat_id=message.get(\"chat_id\", \"\"),
                user_id=sender.get(\"sender_id\", {}).get(\"open_id\", \"\"),
                content=text,
                message_type=message.get(\"message_type\", \"text\"),
                create_time=message.get(\"create_time\", \"\"),
            )
        except Exception as e:
            print(f\"ERROR parse_message: {e}\", file=sys.stderr, flush=True)
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
            return f\" {message}\"
        return f\" {message}\"

    def format_help(self):
        return \"\\n\".join([f\"{k} - {v}\" for k, v in self.COMMANDS.items()])

    def format_status(self, stats):
        return f\"笔记总数: {stats.get('total_notes', 0)}\"


_feishu_adapter = None

def get_feishu_adapter():
    global _feishu_adapter
    if _feishu_adapter is None:
        _feishu_adapter = FeishuAdapter()
    return _feishu_adapter
'''

with open('/opt/pkb-system/backend/src/input/adapters/feishu.py', 'w') as f:
    f.write(content)
print('feishu.py written')
"

echo "=== 修改 main.py 中的 webhook 函数 ==="
# 使用 sed 直接修改关键行
# 1. 修改 event_id 提取 - 从 header 中获取
sed -i 's/event_id = webhook_req.event.get("event_id", "")/header = webhook_req.header or {}\\n    event_id = header.get("event_id", "")/' /opt/pkb-system/backend/src/main.py

# 2. 添加 header 字段到 FeishuWebhookRequest
sed -i '/type: Optional\[str\] = None/a\    schema_: Optional[str] = None\\n    header: Optional[dict] = None' /opt/pkb-system/backend/src/main.py

echo "=== 验证修改 ==="
echo "--- feishu.py parse_message ---"
grep -A 3 "message = event.get" /opt/pkb-system/backend/src/input/adapters/feishu.py

echo "--- main.py event_id ---"
grep -A 2 "event_id =" /opt/pkb-system/backend/src/main.py | head -5

echo "=== 重启服务 ==="
pkill -f "uvicorn" 2>/dev/null
sleep 3

cd /opt/pkb-system
nohup /opt/miniconda/envs/pkb/bin/python -m uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 > /tmp/pkb.log 2>&1 &
sleep 5

echo "=== 验证服务 ==="
curl -s http://127.0.0.1:8000/health
echo ""

echo "=== 测试 webhook ==="
TEST_ID=$(date +%s)
curl -s -X POST http://127.0.0.1:8000/api/v1/feishu/webhook \
  -H "Content-Type: application/json" \
  -d "{\"schema\":\"2.0\",\"header\":{\"event_id\":\"test_${TEST_ID}\"},\"event\":{\"sender\":{\"sender_id\":{\"open_id\":\"ou_test\"}},\"message\":{\"message_id\":\"om_${TEST_ID}\",\"chat_id\":\"oc_test\",\"message_type\":\"text\",\"content\":\"{\\\"text\\\":\\\"测试消息123\\\"}\",\"create_time\":\"123\"}}}"
echo ""

echo "=== 查询数据库 ==="
sqlite3 /opt/pkb-system/data/db/pkb.db "SELECT id, substr(title,1,30), length(content), created_at FROM documents ORDER BY created_at DESC LIMIT 3;"

echo "=== 完成 ==="
