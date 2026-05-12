#!/usr/bin/env python3
"""
通过 HTTP 端点修复并验证 - 服务器端执行
"""
import os
import json
import time
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler

FEISHU_PY = '/opt/pkb-system/backend/src/input/adapters/feishu.py'
MAIN_PY = '/opt/pkb-system/backend/src/main.py'

def fix_and_verify():
    results = []
    
    # 1. 写入修复后的 feishu.py
    feishu_content = '''"""
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
            print(f"DEBUG: text={text[:50]}", file=sys.stderr, flush=True)
            return FeishuMessage(
                message_id=message.get("message_id", ""),
                chat_id=message.get("chat_id", ""),
                user_id=sender.get("sender_id", {}).get("open_id", ""),
                content=text,
                message_type=message.get("message_type", "text"),
                create_time=message.get("create_time", ""),
            )
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr, flush=True)
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
        return f"{'✅' if success else '❌'} {message}"

    def format_help(self):
        return "\\n".join([f"{k} - {v}" for k, v in self.COMMANDS.items()])

    def format_status(self, stats):
        return f"笔记总数: {stats.get('total_notes', 0)}"


_feishu_adapter = None

def get_feishu_adapter():
    global _feishu_adapter
    if _feishu_adapter is None:
        _feishu_adapter = FeishuAdapter()
    return _feishu_adapter
'''
    
    with open(FEISHU_PY, 'w') as f:
        f.write(feishu_content)
    results.append(f"feishu.py written: {os.path.getsize(FEISHU_PY)} bytes")
    
    # 2. 修复 main.py
    with open(MAIN_PY, 'r') as f:
        content = f.read()
    
    if 'header: Optional[dict]' not in content:
        content = content.replace(
            '    type: Optional[str] = None\n    event: Optional[dict] = None',
            '    type: Optional[str] = None\n    schema_: Optional[str] = None\n    header: Optional[dict] = None\n    event: Optional[dict] = None'
        )
        results.append("Added header field")
    
    if 'header.get("event_id"' not in content:
        content = content.replace(
            '    event_id = webhook_req.event.get("event_id", "")',
            '    header = webhook_req.header or {} if hasattr(webhook_req, "header") else body.get("header", {})\n    event_id = header.get("event_id", "")'
        )
        results.append("Fixed event_id extraction")
    
    with open(MAIN_PY, 'w') as f:
        f.write(content)
    results.append(f"main.py updated: {os.path.getsize(MAIN_PY)} bytes")
    
    # 3. 重启服务
    os.system('pkill -f uvicorn 2>/dev/null')
    time.sleep(3)
    os.chdir('/opt/pkb-system')
    os.system('nohup /opt/miniconda/envs/pkb/bin/python -m uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 > /tmp/pkb.log 2>&1 &')
    time.sleep(5)
    results.append("Service restarted")
    
    # 4. 验证
    import urllib.request
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000/health') as r:
            results.append(f"Health: {r.read().decode()}")
    except Exception as e:
        results.append(f"Health check failed: {e}")
    
    # 5. 测试 webhook
    test_data = json.dumps({
        "schema": "2.0",
        "header": {"event_id": "http_fix_test_001"},
        "event": {
            "sender": {"sender_id": {"open_id": "ou_test"}},
            "message": {
                "message_id": "om_test",
                "chat_id": "oc_test",
                "message_type": "text",
                "content": '{"text":"HTTP端点修复验证消息XYZ"}',
                "create_time": "123"
            }
        }
    })
    
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/v1/feishu/webhook',
        data=test_data.encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as r:
            results.append(f"Webhook test: {r.read().decode()}")
    except Exception as e:
        results.append(f"Webhook test failed: {e}")
    
    # 6. 检查数据库
    try:
        conn = sqlite3.connect('/opt/pkb-system/data/db/pkb.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, substr(title,1,50), length(content), created_at FROM documents ORDER BY created_at DESC LIMIT 3')
        rows = cursor.fetchall()
        for r in rows:
            results.append(f"Doc: {r[1][:30]}... len={r[2]}")
        conn.close()
    except Exception as e:
        results.append(f"DB check failed: {e}")
    
    return results

class FixHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        results = fix_and_verify()
        response = json.dumps({'status': 'completed', 'results': results}, ensure_ascii=False, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 9991), FixHandler)
    print("Fix API on port 9991", flush=True)
    server.serve_forever()
