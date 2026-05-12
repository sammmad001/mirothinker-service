#!/bin/bash
# 添加详细的调试日志到飞书 webhook 端点

MAIN_PY="/opt/pkb-system/backend/src/main.py"

# 备份原文件
cp $MAIN_PY ${MAIN_PY}.backup.$(date +%Y%m%d_%H%M%S)

# 在 webhook 函数中添加调试日志
python3 << 'PYTHON_SCRIPT'
import re

with open("/opt/pkb-system/backend/src/main.py", "r") as f:
    content = f.read()

# 查找 feishu_webhook 函数
old_webhook = '''@app.post("/api/v1/feishu/webhook")
async def feishu_webhook(request: FeishuWebhookRequest):
    """飞书 Webhook 端点"""
    feishu = get_feishu_adapter()'''

new_webhook = '''@app.post("/api/v1/feishu/webhook")
async def feishu_webhook(request: FeishuWebhookRequest):
    """飞书 Webhook 端点"""
    import sys
    import json
    print(f"DEBUG: Full request body: {json.dumps(request.dict(), ensure_ascii=False)}", file=sys.stderr, flush=True)
    
    feishu = get_feishu_adapter()'''

if old_webhook in content:
    content = content.replace(old_webhook, new_webhook)
    with open("/opt/pkb-system/backend/src/main.py", "w") as f:
        f.write(content)
    print("Successfully added debug logging")
else:
    print("ERROR: Could not find webhook function to patch")
    print("Searching for webhook pattern...")
    if "async def feishu_webhook" in content:
        print("Found webhook function definition")
    if "FeishuWebhookRequest" in content:
        print("Found FeishuWebhookRequest model")
PYTHON_SCRIPT

# 重启服务
systemctl restart pkb

# 检查服务状态
sleep 2
systemctl is-active pkb
