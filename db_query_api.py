#!/opt/miniconda/envs/pkb/bin/python
"""临时 API - 查询数据库"""
import sqlite3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        conn = None
        try:
            conn = sqlite3.connect('/opt/pkb-system/data/db/pkb.db')
            cursor = conn.cursor()
            
            # 总文档数
            cursor.execute('SELECT COUNT(*) FROM documents')
            total = cursor.fetchone()[0]
            
            # 最近 10 条
            cursor.execute('''
                SELECT id, title, substr(content,1,200), source, created_at 
                FROM documents 
                ORDER BY created_at DESC 
                LIMIT 10
            ''')
            rows = cursor.fetchall()
            
            docs = []
            for r in rows:
                docs.append({
                    'id': r[0],
                    'title': r[1],
                    'content_preview': r[2],
                    'content_length': len(r[2]) if r[2] else 0,
                    'source': r[3],
                    'created_at': r[4]
                })
            
            result = {'total': total, 'recent': docs}
            response = json.dumps(result, ensure_ascii=False, indent=2)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}, ensure_ascii=False).encode('utf-8'))
        finally:
            if conn:
                conn.close()
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 9997), Handler)
    print("DB query server running on port 9997", flush=True)
    server.serve_forever()
