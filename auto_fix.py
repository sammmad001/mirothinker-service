#!/usr/bin/env python3
"""
自动部署修复 - 通过 HTTP API 验证
"""
import subprocess
import time

def ssh_exec(cmd, timeout=30):
    """执行 SSH 命令"""
    result = subprocess.run(
        ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'BatchMode=yes',
         '-o', 'ConnectTimeout=10',
         'root@47.93.253.208', cmd],
        capture_output=True, text=True, timeout=timeout,
        env={**__import__('os').environ, 
             'SSH_AUTH_SOCK': '/Users/sam/.ssh/agent/s.COPpKsqKcb.agent.pFd3uhTySP'}
    )
    return result.stdout + result.stderr

# Step 1: 上传修复脚本
print("=== 上传修复脚本 ===")
script = """
#!/bin/bash
cat > /tmp/fix_webhook.py << 'PYEOF'
import sys

# 读取 main.py
with open('/opt/pkb-system/backend/src/main.py', 'r') as f:
    lines = f.readlines()

# 找到 webhook 函数并修改
output = []
in_webhook = False
webhook_modified = False

for i, line in enumerate(lines):
    if '@app.post("/api/v1/feishu/webhook")' in line:
        in_webhook = True
        output.append(line)
        continue
    
    if in_webhook and 'event_id = ' in line and 'webhook_req.event.get' in line:
        # 修改 event_id 提取逻辑
        output.append('    # 事件去重 - event_id 在 header 中\\n')
        output.append('    header = webhook_req.header or {} if hasattr(webhook_req, "header") else body.get("header", {})\\n')
        output.append('    event_id = header.get("event_id", "")\\n')
        webhook_modified = True
        continue
    
    if in_webhook and 'class FeishuWebhookReq' in line:
        # 修改 FeishuWebhookReq 类定义，添加 header 字段
        output.append(line)
        # 在下一个字段前插入 header
        continue
    
    output.append(line)
    
    if in_webhook and webhook_modified and line.strip().startswith('webhook_req = FeishuWebhookReq'):
        # 在解析后添加调试
        output.append('    print(f"DEBUG: event_id={event_id}, has_event={webhook_req.event is not None}", file=sys.stderr, flush=True)\\n')
        in_webhook = False

if not webhook_modified:
    print("ERROR: Could not find event_id extraction to modify")
    sys.exit(1)

with open('/opt/pkb-system/backend/src/main.py', 'w') as f:
    f.writelines(output)

print("main.py modified successfully")

# 修改 feishu.py
with open('/opt/pkb-system/backend/src/input/adapters/feishu.py', 'r') as f:
    content = f.read()

if 'message = event.get("message"' not in content:
    content = content.replace(
        'content = event.get("content", {})',
        'message = event.get("message", {})\\n            content = message.get("content", {})'
    )
    content = content.replace(
        'message_id=event.get("message_id", "")',
        'message_id=message.get("message_id", "")'
    )
    content = content.replace(
        'chat_id=event.get("chat_id", "")',
        'chat_id=message.get("chat_id", "")'
    )
    content = content.replace(
        'message_type=event.get("message_type", "text")',
        'message_type=message.get("message_type", "text")'
    )
    content = content.replace(
        'create_time=event.get("create_time", "")',
        'create_time=message.get("create_time", "")'
    )
    
    with open('/opt/pkb-system/backend/src/input/adapters/feishu.py', 'w') as f:
        f.write(content)
    print("feishu.py modified successfully")
else:
    print("feishu.py already has correct code")

PYEOF

python3 /tmp/fix_webhook.py

# 重启服务
echo "Restarting service..."
pkill -f "uvicorn" 2>/dev/null
sleep 2
cd /opt/pkb-system && nohup /opt/miniconda/envs/pkb/bin/python -m uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 > /tmp/pkb.log 2>&1 &
sleep 4
echo "Service restarted"

# 验证
echo "Health check:"
curl -s http://127.0.0.1:8000/health
echo ""

# 测试 webhook
echo "Webhook test:"
curl -s -X POST http://127.0.0.1:8000/api/v1/feishu/webhook \\
  -H "Content-Type: application/json" \\
  -d '{"schema":"2.0","header":{"event_id":"auto_test_001"},"event":{"sender":{"sender_id":{"open_id":"ou_test"}},"message":{"message_id":"om_auto","chat_id":"oc_test","message_type":"text","content":"{\\"text\\":\\"自动测试消息\\"}","create_time":"123"}}}'
echo ""

# 查询数据库
echo "Database check:"
sqlite3 /opt/pkb-system/data/db/pkb.db "SELECT id, substr(title,1,30), length(content), created_at FROM documents ORDER BY created_at DESC LIMIT 3;"
"""

print("Script prepared")

# Step 2: 通过 HTTP 验证
print("\n=== 测试 webhook ===")
time.sleep(2)
import requests
try:
    import json
    test_data = {
        "schema": "2.0",
        "header": {"event_id": f"auto_verify_{int(time.time())}"},
        "event": {
            "sender": {"sender_id": {"open_id": "ou_test"}},
            "message": {
                "message_id": "om_auto",
                "chat_id": "oc_test",
                "message_type": "text",
                "content": '{"text":"自动验证消息XYZ"}',
                "create_time": "123"
            }
        }
    }
    
    response = requests.post(
        "http://47.93.253.208/api/v1/feishu/webhook",
        json=test_data,
        timeout=10
    )
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    
    if "长度" in response.text and "0 字" not in response.text:
        print("\n✅ SUCCESS: Message content is being parsed correctly!")
    else:
        print("\n❌ Issue: Message content still empty")
        
except Exception as e:
    print(f"Error: {e}")
