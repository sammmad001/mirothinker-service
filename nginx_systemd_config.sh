#!/bin/bash
# Nginx and Systemd configuration script

cat > /etc/nginx/conf.d/pkb.conf << 'NGINXEOF'
server {
    listen 80;
    server_name _;
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection upgrade;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
NGINXEOF

cat > /etc/systemd/system/pkb.service << 'SERVICEEOF'
[Unit]
Description=PKB API Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/pkb-system
Environment=PATH=/opt/miniconda/envs/pkb/bin
ExecStart=/opt/miniconda/envs/pkb/bin/python -m uvicorn backend.src.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

echo "Configuration files created"
