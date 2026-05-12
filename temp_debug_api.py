#!/opt/miniconda/envs/pkb/bin/python
"""临时调试 API - 查询最近的数据库记录和日志"""
import sqlite3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class DebugHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/debug':
            result = {}
            
            # 1. 查询最近的文档
            try:
                conn = sqlite3.connect('/opt/pkb-system/data/db/pkb.db')
                cursor = conn.cursor()
                cursor.execute('SELECT id, title, substr(content,1,200), source, created_at FROM documents ORDER BY created_at DESC LIMIT 5')
                rows = cursor.fetchall()
                result['recent_docs'] = []
                for row in rows:
                    result['recent_docs'].append({
                        'id': row[0],
                        'title': row[1],
                        'content_preview': row[2],
                        'source': row[3],
                        'created_at': row[4]
                    })
                conn.close()
            except Exception as e:
                result['db_error'] = str(e)
            
            # 2. 读取最近的 Nginx 日志
            try:
                with open('/var/log/nginx/access.log', 'r') as f:
                    lines = f.readlines()
                    result['nginx_recent'] = [l.strip() for l in lines[-10:]]
            except Exception as e:
                result['nginx_error'] = str(e)
            
            # 3. 读取 PKB 日志
            try:
                result['pkb_logs'] = []
                if os.path.exists('/tmp/recent_logs.txt'):
                    with open('/tmp/recent_logs.txt', 'r') as f:
                        result['pkb_logs'] = [l.strip() for l in f.readlines()[-20:]]
            except:
                pass
            
            response = json.dumps(result, ensure_ascii=False, indent=2)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 9998), DebugHandler)
    print("Debug server running on port 9998", flush=True)
    server.serve_forever()
