#!/usr/bin/env python3
"""验证服务器上的文件内容并通过 HTTP 返回结果"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class VerifyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        result = {}
        
        # Check main.py
        main_py = '/opt/pkb-system/backend/src/main.py'
        if os.path.exists(main_py):
            with open(main_py, 'r') as f:
                content = f.read()
            result['main_py'] = {
                'has_header_field': 'header: Optional[dict]' in content,
                'has_correct_event_id': 'header.get("event_id"' in content,
                'uses_request_object': 'request: Request' in content,
                'uses_pydantic_model': 'request: FeishuWebhookRequest' in content,
                'file_size': len(content)
            }
        else:
            result['main_py'] = {'error': 'File not found'}
        
        # Check feishu.py
        feishu_py = '/opt/pkb-system/backend/src/input/adapters/feishu.py'
        if os.path.exists(feishu_py):
            with open(feishu_py, 'r') as f:
                content = f.read()
            result['feishu_py'] = {
                'has_message_extraction': 'message = event.get("message"' in content,
                'has_correct_parse': 'message.get("message_id"' in content,
                'file_size': len(content)
            }
        else:
            result['feishu_py'] = {'error': 'File not found'}
        
        # Check database
        import sqlite3
        try:
            conn = sqlite3.connect('/opt/pkb-system/data/db/pkb.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, substr(title,1,50), length(content), created_at FROM documents ORDER BY created_at DESC LIMIT 3')
            rows = cursor.fetchall()
            result['recent_docs'] = [
                {'id': r[0], 'title': r[1], 'content_length': r[2], 'created_at': r[3]}
                for r in rows
            ]
            conn.close()
        except Exception as e:
            result['db_error'] = str(e)
        
        response = json.dumps(result, ensure_ascii=False, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 9994), VerifyHandler)
    print("Verify API running on port 9994", flush=True)
    server.serve_forever()
