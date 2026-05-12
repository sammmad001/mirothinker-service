#!/bin/bash
# 创建临时 API 端点来查询数据库

cat > /tmp/debug_api.py << 'EOF'
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sqlite3

app = FastAPI()

@app.get("/debug/docs")
async def get_docs():
    conn = sqlite3.connect('/opt/pkb-system/data/db/pkb.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, substr(content,1,100), source, created_at FROM documents ORDER BY created_at DESC LIMIT 10')
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
    return JSONResponse(content=docs)

@app.get("/debug/raw")
async def get_raw_logs():
    import os
    logs = []
    try:
        with open('/var/log/nginx/access.log', 'r') as f:
            logs = f.readlines()[-20:]
    except:
        pass
    return JSONResponse(content={'logs': logs})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9999)
EOF

# 启动调试 API
nohup /opt/miniconda/envs/pkb/bin/python /tmp/debug_api.py > /tmp/debug_api.log 2>&1 &
sleep 2
echo "Debug API started on port 9999"
