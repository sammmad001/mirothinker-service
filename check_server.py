#!/usr/bin/env python3
"""通过 SSH 查询服务器数据库和日志"""
import subprocess
import json

def ssh_cmd(cmd):
    """执行 SSH 命令并返回输出"""
    result = subprocess.run(
        ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'BatchMode=yes',
         'root@47.93.253.208', cmd],
        capture_output=True, text=True, timeout=30,
        env={**__import__('os').environ, 'SSH_AUTH_SOCK': '/Users/sam/.ssh/agent/s.COPpKsqKcb.agent.pFd3uhTySP'}
    )
    return result.stdout + result.stderr

# 1. 查询数据库
print("=" * 60)
print("最近 5 条文档记录:")
print("=" * 60)
db_output = ssh_cmd("""python3 -c \"
import sqlite3
conn = sqlite3.connect('/opt/pkb-system/data/db/pkb.db')
cursor = conn.cursor()
cursor.execute('SELECT id, title, substr(content,1,100), source, created_at FROM documents ORDER BY created_at DESC LIMIT 5')
rows = cursor.fetchall()
for r in rows:
    print(f'ID: {r[0]}')
    print(f'Title: {r[1]}')
    print(f'Content: {r[2]}')
    print(f'Source: {r[3]}')
    print(f'Time: {r[4]}')
    print('---')
conn.close()
\"""")
print(db_output if db_output else "(无输出)")

# 2. 查看 Nginx 访问日志中最近的飞书 webhook 请求
print("=" * 60)
print("最近飞书 Webhook 请求:")
print("=" * 60)
nginx_output = ssh_cmd("tail -20 /var/log/nginx/access.log | grep webhook")
print(nginx_output if nginx_output else "(无输出)")

# 3. 查看 PKB 服务日志
print("=" * 60)
print("PKB 服务日志 (最近):")
print("=" * 60)
pkb_output = ssh_cmd("journalctl -u pkb --no-pager -n 30 2>/dev/null || tail -30 /tmp/pkb.log 2>/dev/null || echo 'No logs found'")
print(pkb_output if pkb_output else "(无输出)")
