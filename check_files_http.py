#!/usr/bin/env python3
"""通过 HTTP 端点验证服务器上的文件内容"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os

class CheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        result = {}
        
        # Check main.py
        try:
            with open('/opt/pkb-system/backend/src/main.py', 'r') as f:
                main_content = f.read()
            result['main_py'] = {
                'exists': True,
                'size': len(main_content),
                'has_header_field': 'header: Optional[dict]' in main_content,
                'has_correct_event_id': 'header.get("event_id"' in main_content,
                'uses_request_object': 'request: Request' in main_content and 'FeishuWebhookRequest' not in main_content.split('feishu_webhook')[1].split('async def handle')[0],
            }
        except Exception as e:
            result['main_py'] = {'error': str(e)}
        
        # Check feishu.py
        try:
            with open('/opt/pkb-system/backend/src/input/adapters/feishu.py', 'r') as f:
                feishu_content = f.read()
            result['feishu_py'] = {
                'exists': True,
                'size': len(feishu_content),
                'has_message_extraction': 'message = event.get("message"' in feishu_content,
                'has_test_skip': 'event_id.startswith("test_")' in feishu_content,
            }
        except Exception as e:
            result['feishu_py'] = {'error': str(e)}
        
        response = json.dumps(result, ensure_ascii=False, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 9992), CheckHandler)
    print("Check API running on port 9992", flush=True)
    server.serve_forever()
