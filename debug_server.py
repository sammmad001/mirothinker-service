#!/usr/bin/env python3
"""临时 API 端点用于调试"""
import sqlite3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class DebugHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/debug/docs':
            conn = sqlite3.connect('/opt/pkb-system/data/db/pkb.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, content[:100], source, created_at FROM documents ORDER BY created_at DESC LIMIT 5')
            rows = cursor.fetchall()
            docs = []
            for row in rows:
                docs.append({
                    'id': row[0],
                    'title': row[1],
                    'content_preview': row[2],
                    'source': row[3],
                    'created_at': row[4]
                })
            conn.close()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(docs, ensure_ascii=False, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # 静默日志

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 9999), DebugHandler)
    print("Debug server running on port 9999")
    server.serve_forever()
