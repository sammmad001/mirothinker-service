#!/usr/bin/env python3
"""
修复飞书 webhook 函数
"""

main_py = "/opt/pkb-system/backend/src/main.py"

with open(main_py, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到旧的 webhook 函数并替换
old_func_start = '@app.post("/api/v1/feishu/webhook")\nasync def feishu_webhook(request: Request):'
old_func_end = 'return await handle_feishu_note(message, feishu)'

start_idx = content.find(old_func_start)
end_idx = content.find(old_func_end, start_idx) + len(old_func_end)

if start_idx == -1 or end_idx == -1:
    print("ERROR: Could not find webhook function")
    exit(1)

new_func = '''@app.post("/api/v1/feishu/webhook")
async def feishu_webhook(request: Request):
    """飞书 Webhook 端点"""
    # 快速处理 URL 验证（飞书首次配置时发送，必须在3秒内响应）
    body = await request.json()
    
    # URL 验证 - 直接返回 challenge
    if "challenge" in body:
        return {"challenge": body["challenge"]}
    
    # 正常事件处理
    from pydantic import BaseModel
    class FeishuWebhookReq(BaseModel):
        challenge: Optional[str] = None
        token: Optional[str] = None
        type: Optional[str] = None
        event: Optional[dict] = None
    
    webhook_req = FeishuWebhookReq(**body)
    feishu = get_feishu_adapter()

    if not webhook_req.event:
        return {"success": False, "message": "No event data"}

    # 事件去重
    event_id = webhook_req.event.get("event_id", "")
    if feishu.dedup.is_duplicate(event_id):
        return {"success": True, "message": "Duplicate event"}

    # 解析消息
    message = feishu.parse_message({"event": webhook_req.event})
    if not message:
        return {"success": False, "message": "Failed to parse message"}

    # 检查是否是指令
    command = feishu.parse_command(message.content)

    if command:
        # 处理指令
        return await handle_feishu_command(command, feishu)
    else:
        # 普通笔记
        return await handle_feishu_note(message, feishu)'''

content = content[:start_idx] + new_func + content[end_idx:]

with open(main_py, 'w', encoding='utf-8') as f:
    f.write(content)

print("Webhook function fixed successfully")
print(f"Replaced {end_idx - start_idx} characters with {len(new_func)} characters")
