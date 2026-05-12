#!/usr/bin/env python3
"""
测试飞书 webhook 端点 - 模拟飞书发送消息
"""
import requests
import json

# 模拟飞书 im.message.receive_v1 事件
test_payload = {
    "schema": "2.0",
    "header": {
        "event_id": "test_123456",
        "event_type": "im.message.receive_v1",
        "create_time": "1234567890",
        "token": "test_token"
    },
    "event": {
        "sender": {
            "sender_id": {
                "open_id": "ou_test_user"
            },
            "sender_type": "user"
        },
        "message": {
            "message_id": "om_test_123",
            "chat_id": "oc_test_chat",
            "message_type": "text",
            "content": "{\"text\":\"测试消息 6\"}",
            "create_time": "1234567890"
        }
    }
}

# 发送请求
url = "http://47.93.253.208/api/v1/feishu/webhook"
print(f"Sending test message to {url}")
print(f"Payload: {json.dumps(test_payload, ensure_ascii=False)}\n")

response = requests.post(url, json=test_payload)
print(f"Response status: {response.status_code}")
print(f"Response body: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

# 查询数据库
print("\n\nChecking database for recent documents...")
# 通过一个自定义的查询端点
