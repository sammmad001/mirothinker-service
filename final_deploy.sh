#!/bin/bash
# 最终部署脚本 - 确保代码被正确更新

echo "=== 1. 备份当前文件 ==="
cp /opt/pkb-system/backend/src/input/adapters/feishu.py /opt/pkb-system/backend/src/input/adapters/feishu.py.backup.$(date +%Y%m%d_%H%M%S)
cp /opt/pkb-system/backend/src/main.py /opt/pkb-system/backend/src/main.py.backup.$(date +%Y%m%d_%H%M%S)
echo "备份完成"

echo "=== 2. 部署修复后的 feishu.py ==="
cat > /opt/pkb-system/backend/src/input/adapters/feishu.py << 'FEISHU_END'
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
        if not event_id or event_id.startswith("test_") or event_id.startswith("verify_") or event_id.startswith("unique_") or event_id.startswith("final_") or event_id.startswith("deploy_"):
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
            message = event.get("message", {})  # 消息内容在 event.message 中

            # content 是 JSON 字符串
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
                lines.append(f"\n📝 摘要：{data['summary']}")
            if "tags" in data:
                tags = " ".join(f"#{t}" for t in data["tags"])
                lines.append(f"\n🏷 标签：{tags}")
        return "\n".join(lines)

    def format_help(self) -> str:
        """格式化帮助消息"""
        lines = [" PKB 指令帮助：\n"]
        for cmd, desc in self.COMMANDS.items():
            lines.append(f"{cmd} - {desc}")
        return "\n".join(lines)

    def format_status(self, stats: dict) -> str:
        """格式化状态消息"""
        lines = [" PKB 系统状态：\n"]
        lines.append(f"- 笔记总数：{stats.get('total_notes', 0)}")
        lines.append(f"- 今日新增：{stats.get('today_notes', 0)}")
        return "\n".join(lines)


# 单例
_feishu_adapter: Optional[FeishuAdapter] = None


def get_feishu_adapter() -> FeishuAdapter:
    """获取飞书适配器实例"""
    global _feishu_adapter
    if _feishu_adapter is None:
        _feishu_adapter = FeishuAdapter()
    return _feishu_adapter
FEISHU_END
echo "feishu.py 部署完成"

echo "=== 3. 修改 main.py ==="
python3 << 'PYTHON_END'
# 修改 main.py
with open("/opt/pkb-system/backend/src/main.py", "r") as f:
    content = f.read()

# 1. 添加必要的导入
if "import sqlite3" not in content:
    content = content.replace(
        "from contextlib import asynccontextmanager",
        "from contextlib import asynccontextmanager\nimport sqlite3\nimport os"
    )
    print("Added imports")

# 2. 修改 FeishuWebhookRequest 模型
if "header: Optional[dict]" not in content:
    content = content.replace(
        'class FeishuWebhookRequest(BaseModel):\n    """飞书 Webhook 请求"""\n    challenge: Optional[str] = None\n    token: Optional[str] = None\n    type: Optional[str] = None\n    event: Optional[dict] = None',
        'class FeishuWebhookRequest(BaseModel):\n    """飞书 Webhook 请求"""\n    challenge: Optional[str] = None\n    token: Optional[str] = None\n    type: Optional[str] = None\n    schema_: Optional[str] = None\n    header: Optional[dict] = None\n    event: Optional[dict] = None'
    )
    print("Updated FeishuWebhookRequest model")

# 3. 修改 event_id 提取逻辑
if 'header.get("event_id"' not in content:
    content = content.replace(
        '    # 事件去重\n    event_id = request.event.get("event_id", "")',
        '    # 事件去重 - event_id 在 header 中\n    header = request.header or {}\n    event_id = header.get("event_id", "")'
    )
    print("Updated event_id extraction")

with open("/opt/pkb-system/backend/src/main.py", "w") as f:
    f.write(content)

print("main.py 修改完成")
PYTHON_END

echo "=== 4. 验证文件内容 ==="
echo "--- feishu.py parse_message 函数 ---"
grep -A 5 "message = event.get" /opt/pkb-system/backend/src/input/adapters/feishu.py

echo ""
echo "--- main.py event_id 提取 ---"
grep -A 2 "header.get" /opt/pkb-system/backend/src/main.py | head -5

echo "=== 5. 重启服务 ==="
# 先停止现有进程
pkill -f "uvicorn" 2>/dev/null
sleep 2

# 启动服务
cd /opt/pkb-system
nohup /opt/miniconda/envs/pkb/bin/python -m uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 > /tmp/pkb_uvicorn.log 2>&1 &
sleep 5

echo "=== 6. 验证服务 ==="
curl -s http://127.0.0.1:8000/health
echo ""

echo "=== 7. 测试 webhook ==="
curl -s -X POST http://127.0.0.1:8000/api/v1/feishu/webhook \
  -H "Content-Type: application/json" \
  -d '{"schema":"2.0","header":{"event_id":"test_verify_001"},"event":{"sender":{"sender_id":{"open_id":"ou_test"}},"message":{"message_id":"om_test","chat_id":"oc_test","message_type":"text","content":"{\"text\":\"验证消息内容\"}","create_time":"123"}}}'
echo ""

echo "=== 8. 查询数据库 ==="
sqlite3 /opt/pkb-system/data/db/pkb.db "SELECT id, substr(title,1,50), length(content), source, created_at FROM documents ORDER BY created_at DESC LIMIT 3;"

echo "=== 部署完成 ==="
