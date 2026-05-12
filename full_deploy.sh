#!/bin/bash
# 完整部署修复后的代码

echo "=== 部署 feishu.py ==="
cat > /opt/pkb-system/backend/src/input/adapters/feishu.py << 'EOF'
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
            return False  # 跳过测试事件
        
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
            message = event.get("message", {})  # 消息在 event.message 中

            # content 是 JSON 字符串
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
EOF

echo "feishu.py 部署完成"

echo "=== 部署 main.py (webhook 部分) ==="
# 只修改 webhook 函数中的 event_id 提取逻辑
MAIN_PY="/opt/pkb-system/backend/src/main.py"

# 备份
cp $MAIN_PY ${MAIN_PY}.backup.$(date +%Y%m%d)

# 使用 Python 修改文件
python3 << 'PYEOF'
import re

with open("/opt/pkb-system/backend/src/main.py", "r") as f:
    content = f.read()

# 1. 修改 FeishuWebhookRequest 添加 header 字段
old_model = '''class FeishuWebhookRequest(BaseModel):
    """飞书 Webhook 请求"""
    challenge: Optional[str] = None
    token: Optional[str] = None
    type: Optional[str] = None
    event: Optional[dict] = None'''

new_model = '''class FeishuWebhookRequest(BaseModel):
    """飞书 Webhook 请求"""
    challenge: Optional[str] = None
    token: Optional[str] = None
    type: Optional[str] = None
    schema_: Optional[str] = None
    header: Optional[dict] = None
    event: Optional[dict] = None'''

if old_model in content:
    content = content.replace(old_model, new_model)
    print("Updated FeishuWebhookRequest model")
else:
    print("WARNING: Could not find FeishuWebhookRequest model")

# 2. 修改 event_id 提取逻辑
old_dedup = '''    # 事件去重
    event_id = request.event.get("event_id", "")
    if feishu.dedup.is_duplicate(event_id):'''

new_dedup = '''    # 事件去重 - event_id 在 header 中
    header = request.header or {}
    event_id = header.get("event_id", "")
    print(f"DEBUG: event_id={event_id}", file=sys.stderr, flush=True)
    if feishu.dedup.is_duplicate(event_id):'''

if old_dedup in content:
    content = content.replace(old_dedup, new_dedup)
    print("Updated event_id extraction")
else:
    print("WARNING: Could not find event_id extraction")

with open("/opt/pkb-system/backend/src/main.py", "w") as f:
    f.write(content)

print("main.py 修改完成")
PYEOF

echo "=== 重启服务 ==="
systemctl restart pkb
sleep 3

if systemctl is-active pkb > /dev/null 2>&1; then
    echo "PKB 服务已启动并运行"
else
    echo "ERROR: PKB 服务启动失败"
    systemctl status pkb
fi

echo "=== 部署完成 ==="
