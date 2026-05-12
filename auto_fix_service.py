#!/opt/miniconda/envs/pkb/bin/python
"""
自动修复脚本 - 在 PKB 服务启动前执行
"""
import os
import sys

MAIN_PY = '/opt/pkb-system/backend/src/main.py'
FEISHU_PY = '/opt/pkb-system/backend/src/input/adapters/feishu.py'

def fix_main():
    """修复 main.py"""
    with open(MAIN_PY, 'r') as f:
        content = f.read()
    
    # 1. 添加 header 字段到 FeishuWebhookReq
    if 'header: Optional[dict]' not in content:
        content = content.replace(
            'type: Optional[str] = None\n    event: Optional[dict] = None',
            'type: Optional[str] = None\n    header: Optional[dict] = None\n    event: Optional[dict] = None'
        )
        print("Added header field", file=sys.stderr, flush=True)
    
    # 2. 修改 event_id 提取
    if 'header.get("event_id"' not in content:
        content = content.replace(
            'event_id = webhook_req.event.get("event_id", "")',
            'header = webhook_req.header or {} if hasattr(webhook_req, "header") else body.get("header", {})\n    event_id = header.get("event_id", "")'
        )
        print("Modified event_id extraction", file=sys.stderr, flush=True)
    
    with open(MAIN_PY, 'w') as f:
        f.write(content)
    print("main.py fixed", file=sys.stderr, flush=True)

def fix_feishu():
    """修复 feishu.py"""
    with open(FEISHU_PY, 'r') as f:
        content = f.read()
    
    if 'message = event.get("message"' not in content:
        # 修改 parse_message 方法
        content = content.replace(
            'content = event.get("content", {})',
            'message = event.get("message", {})\n            content = message.get("content", {})'
        )
        content = content.replace(
            'message_id=event.get("message_id"',
            'message_id=message.get("message_id"'
        )
        content = content.replace(
            'chat_id=event.get("chat_id"',
            'chat_id=message.get("chat_id"'
        )
        content = content.replace(
            'message_type=event.get("message_type"',
            'message_type=message.get("message_type"'
        )
        content = content.replace(
            'create_time=event.get("create_time"',
            'create_time=message.get("create_time"'
        )
        
        with open(FEISHU_PY, 'w') as f:
            f.write(content)
        print("feishu.py fixed", file=sys.stderr, flush=True)
    else:
        print("feishu.py already fixed", file=sys.stderr, flush=True)

if __name__ == '__main__':
    print("Running auto-fix...", file=sys.stderr, flush=True)
    fix_main()
    fix_feishu()
    print("Auto-fix completed", file=sys.stderr, flush=True)
