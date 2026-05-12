#!/usr/bin/env python3
"""
临时修复 API - 通过 HTTP 端点执行修复并返回结果
"""
import json
import os
import sqlite3
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

class FixHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/fix':
            result = {'status': 'starting', 'steps': []}
            
            try:
                # Step 1: 备份
                import shutil
                shutil.copy2(
                    '/opt/pkb-system/backend/src/main.py',
                    '/opt/pkb-system/backend/src/main.py.backup'
                )
                result['steps'].append('Backed up main.py')
                
                # Step 2: 修改 main.py
                with open('/opt/pkb-system/backend/src/main.py', 'r') as f:
                    content = f.read()
                
                # 修改 event_id 提取
                if 'webhook_req.event.get("event_id"' in content:
                    content = content.replace(
                        'event_id = webhook_req.event.get("event_id", "")',
                        'header = webhook_req.header or {} if hasattr(webhook_req, "header") else body.get("header", {})\n    event_id = header.get("event_id", "")'
                    )
                    result['steps'].append('Modified event_id extraction in main.py')
                
                # 添加 header 字段到 FeishuWebhookReq
                if 'header: Optional[dict]' not in content:
                    content = content.replace(
                        'type: Optional[str] = None\n    event:',
                        'type: Optional[str] = None\n    header: Optional[dict] = None\n    event:'
                    )
                    result['steps'].append('Added header field to FeishuWebhookReq')
                
                with open('/opt/pkb-system/backend/src/main.py', 'w') as f:
                    f.write(content)
                
                # Step 3: 修改 feishu.py
                feishu_path = '/opt/pkb-system/backend/src/input/adapters/feishu.py'
                with open(feishu_path, 'r') as f:
                    feishu_content = f.read()
                
                if 'message = event.get("message"' not in feishu_content:
                    feishu_content = feishu_content.replace(
                        'content = event.get("content", {})',
                        'message = event.get("message", {})\n            content = message.get("content", {})'
                    )
                    feishu_content = feishu_content.replace(
                        'message_id=event.get("message_id"',
                        'message_id=message.get("message_id"'
                    )
                    feishu_content = feishu_content.replace(
                        'chat_id=event.get("chat_id"',
                        'chat_id=message.get("chat_id"'
                    )
                    feishu_content = feishu_content.replace(
                        'message_type=event.get("message_type"',
                        'message_type=message.get("message_type"'
                    )
                    feishu_content = feishu_content.replace(
                        'create_time=event.get("create_time"',
                        'create_time=message.get("create_time"'
                    )
                    result['steps'].append('Modified feishu.py parse_message')
                    
                    with open(feishu_path, 'w') as f:
                        f.write(feishu_content)
                
                # Step 4: 重启服务
                os.system('pkill -f "uvicorn" 2>/dev/null')
                import time
                time.sleep(2)
                os.system('cd /opt/pkb-system && nohup /opt/miniconda/envs/pkb/bin/python -m uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 > /tmp/pkb.log 2>&1 &')
                time.sleep(4)
                result['steps'].append('Service restarted')
                
                # Step 5: 验证
                result['health'] = os.popen('curl -s http://127.0.0.1:8000/health').read()
                
                # Step 6: 查询数据库
                conn = sqlite3.connect('/opt/pkb-system/data/db/pkb.db')
                cursor = conn.cursor()
                cursor.execute('SELECT id, substr(title,1,50), length(content), created_at FROM documents ORDER BY created_at DESC LIMIT 5')
                rows = cursor.fetchall()
                result['recent_docs'] = [
                    {'id': r[0], 'title': r[1], 'content_length': r[2], 'created_at': r[3]}
                    for r in rows
                ]
                conn.close()
                result['status'] = 'completed'
                
            except Exception as e:
                result['status'] = 'error'
                result['error'] = str(e)
                import traceback
                result['traceback'] = traceback.format_exc()
            
            response = json.dumps(result, ensure_ascii=False, indent=2)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 9996), FixHandler)
    print("Fix API running on port 9996. Access http://<server>:9996/fix to execute fix", flush=True)
    server.serve_forever()
