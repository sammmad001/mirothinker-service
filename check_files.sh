#!/bin/bash
# 检查服务器上的文件
echo "=== feishu.py parse_message 函数 ==="
grep -A 25 "def parse_message" /opt/pkb-system/backend/src/input/adapters/feishu.py

echo ""
echo "=== main.py webhook 函数 ==="
grep -A 10 "事件去重" /opt/pkb-system/backend/src/main.py

echo ""
echo "=== main.py FeishuWebhookRequest ==="
grep -A 8 "class FeishuWebhookRequest" /opt/pkb-system/backend/src/main.py
