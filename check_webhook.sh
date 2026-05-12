#!/bin/bash
# 查看 webhook 函数的代码
grep -A 30 "async def feishu_webhook" /opt/pkb-system/backend/src/main.py
