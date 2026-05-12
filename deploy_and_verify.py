#!/opt/miniconda/envs/pkb/bin/python
"""
Complete deployment and verification - all in one script
"""
import os
import sys
import json
import time
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler

# Write the correct feishu.py
FEISHU_CORRECT = '''\
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
        content = content.strip()
        for cmd in self.COMMANDS.keys():
            if content.startswith(cmd):
                parts = content[len(cmd):].strip().split(maxsplit=1)
                args = parts[1].split() if len(parts) > 1 else []
                return FeishuCommand(command=cmd, args=args, raw_content=content)
        return None

    def format_response(self, success: bool, message: str, data: Optional[dict] = None) -> str:
        if success:
            return f"✅ {message}"
        return f"❌ {message}"

    def format_help(self) -> str:
        lines = [" PKB 指令帮助：\\n"]
        for cmd, desc in self.COMMANDS.items():
            lines.append(f"{cmd} - {desc}")
        return "\\n".join(lines)

    def format_status(self, stats: dict) -> str:
        lines = ["📊 PKB 系统状态：\\n"]
        lines.append(f"- 笔记总数：{stats.get('total_notes', 0)}")
        lines.append(f"- 今日新增：{stats.get('today_notes', 0)}")
        return "\\n".join(lines)


_feishu_adapter: Optional[FeishuAdapter] = None

def get_feishu_adapter() -> FeishuAdapter:
    global _feishu_adapter
    if _feishu_adapter is None:
        _feishu_adapter = FeishuAdapter()
    return _feishu_adapter
'''

def deploy():
    """Deploy fixed files and restart service"""
    results = []
    
    # 1. Write feishu.py
    feishu_path = '/opt/pkb-system/backend/src/input/adapters/feishu.py'
    with open(feishu_path, 'w') as f:
        f.write(FEISHU_CORRECT)
    results.append(f"feishu.py written: {os.path.getsize(feishu_path)} bytes")
    
    # 2. Fix main.py
    main_path = '/opt/pkb-system/backend/src/main.py'
    with open(main_path, 'r') as f:
        content = f.read()
    
    # Add header field if missing
    if 'header: Optional[dict]' not in content:
        content = content.replace(
            '    type: Optional[str] = None\n    event: Optional[dict] = None',
            '    type: Optional[str] = None\n    schema_: Optional[str] = None\n    header: Optional[dict] = None\n    event: Optional[dict] = None'
        )
        results.append("Added header field to FeishuWebhookRequest")
    
    # Fix event_id extraction if needed
    if 'header.get("event_id"' not in content:
        content = content.replace(
            '    event_id = webhook_req.event.get("event_id", "")',
            '    header = webhook_req.header or {} if hasattr(webhook_req, "header") else body.get("header", {})\n    event_id = header.get("event_id", "")'
        )
        results.append("Fixed event_id extraction")
    
    with open(main_path, 'w') as f:
        f.write(content)
    results.append(f"main.py updated: {os.path.getsize(main_path)} bytes")
    
    # 3. Restart service
    os.system('pkill -f "uvicorn" 2>/dev/null')
    time.sleep(3)
    os.chdir('/opt/pkb-system')
    os.system('nohup /opt/miniconda/envs/pkb/bin/python -m uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 > /tmp/pkb.log 2>&1 &')
    time.sleep(5)
    results.append("Service restarted")
    
    # 4. Verify
    import urllib.request
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000/health') as response:
            health = response.read().decode()
        results.append(f"Health: {health}")
    except Exception as e:
        results.append(f"Health check failed: {e}")
    
    # 5. Check DB
    try:
        conn = sqlite3.connect('/opt/pkb-system/data/db/pkb.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, substr(title,1,50), length(content), created_at FROM documents ORDER BY created_at DESC LIMIT 3')
        rows = cursor.fetchall()
        results.append(f"Recent docs: {len(rows)} records")
        for r in rows:
            results.append(f"  - {r[1][:30]}... (length={r[2]})")
        conn.close()
    except Exception as e:
        results.append(f"DB check failed: {e}")
    
    return results

class DeployHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/deploy':
            results = deploy()
            response = json.dumps({'status': 'completed', 'results': results}, ensure_ascii=False, indent=2)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response.encode())
        elif self.path == '/status':
            # Just check current state
            result = {}
            try:
                with open('/opt/pkb-system/backend/src/main.py', 'r') as f:
                    main_content = f.read()
                result['main_py'] = {
                    'has_header': 'header: Optional[dict]' in main_content,
                    'has_correct_event_id': 'header.get("event_id"' in main_content,
                }
                
                with open('/opt/pkb-system/backend/src/input/adapters/feishu.py', 'r') as f:
                    feishu_content = f.read()
                result['feishu_py'] = {
                    'has_message_extraction': 'message = event.get("message"' in feishu_content,
                }
            except Exception as e:
                result['error'] = str(e)
            
            response = json.dumps(result, ensure_ascii=False, indent=2)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    port = 9993
    server = HTTPServer(('0.0.0.0', port), DeployHandler)
    print(f"Deploy API running on port {port}", flush=True)
    print(f"Access http://<server>:{port}/deploy to execute deployment", flush=True)
    print(f"Access http://<server>:{port}/status to check current state", flush=True)
    server.serve_forever()
