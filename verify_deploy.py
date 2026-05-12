#!/opt/miniconda/envs/pkb/bin/python
"""验证部署"""
import sys
sys.path.insert(0, '/opt/pkb-system/backend/src')

# 测试 parse_message
from input.adapters.feishu import FeishuAdapter, get_feishu_adapter

# 模拟飞书事件
test_event = {
    "event": {
        "sender": {
            "sender_id": {"open_id": "ou_test"}
        },
        "message": {
            "message_id": "om_test",
            "chat_id": "oc_test",
            "message_type": "text",
            "content": '{"text":"验证测试内容"}',
            "create_time": "123"
        }
    }
}

feishu = get_feishu_adapter()
result = feishu.parse_message(test_event)

print(f"parse_message result: {result}")
if result:
    print(f"content: '{result.content}'")
    print(f"message_id: '{result.message_id}'")
    print(f"user_id: '{result.user_id}'")
