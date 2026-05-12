#!/usr/bin/env python3
"""通过 Python 执行 SSH 命令并获取输出"""
import subprocess
import os

env = os.environ.copy()
env['SSH_AUTH_SOCK'] = '/Users/sam/.ssh/agent/s.COPpKsqKcb.agent.pFd3uhTySP'

# 使用 script 命令来模拟 TTY
cmd = """ssh -o StrictHostKeyChecking=no root@47.93.253.208 'sqlite3 /opt/pkb-system/data/db/pkb.db "SELECT id, substr(title,1,50), length(content), source, created_at FROM documents ORDER BY created_at DESC LIMIT 5;"'"""

result = subprocess.run(
    ['script', '-q', '/dev/null', '-c', cmd],
    capture_output=True, text=True, timeout=30, env=env
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print("\nReturn code:", result.returncode)
