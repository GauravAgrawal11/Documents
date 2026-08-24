# 🚀 Production Deployment & Infrastructure Guide

This guide covers deployment strategies for **Watermarks Remover & Multi-Page Document Studio**.

---

## 1. Quick Local Deployment

### Windows
```cmd
# Double click start-server.bat or run:
start-server.bat
```

### macOS / Linux
```bash
# Clone the repository
git clone https://github.com/guillaumemeyer/watermarks-remover.git
cd watermarks-remover

# Make execution wrapper executable and run
python3 service/scripts/server.py --host 127.0.0.1 --port 8765
```
Access at: `http://localhost:8765`

---

## 2. Docker Deployment

### Using Docker Compose (Recommended)
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Build and start service
docker compose up -d --build

# 3. View logs
docker compose logs -f
```

### Using Standalone Docker Container
```bash
# Build Docker image
docker build -t watermarks-studio .

# Run container on port 8765
docker run -d -p 8765:8765 --name watermarks-studio-app watermarks-studio
```

---

## 3. Cloud Deployments

### A. Render (render.com)
1. Fork or push this repository to GitHub.
2. Log into Render and click **New Web Service**.
3. Select your repository.
4. Settings:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python service/scripts/server.py --host 0.0.0.0 --port $PORT`
5. Add Environment Variables:
   - `GROQ_API_KEY`: *(your api key)*
   - `WATERMARKS_SERVER_PORT`: `10000` (or leave default for Render `$PORT`)

---

### B. Railway (railway.app)
1. Link your GitHub repository in Railway.
2. Set the custom start command:
   ```bash
   python service/scripts/server.py --host 0.0.0.0 --port $PORT
   ```
3. Set your environment variables in the Railway dashboard.

---

### C. Fly.io
```bash
# Launch app configuration
fly launch

# Deploy app
fly deploy
```

---

## 4. Production Reverse Proxy (Nginx + Systemd on Ubuntu/Debian)

### 1. Systemd Service Setup
Create `/etc/systemd/system/watermarks-studio.service`:
```ini
[Unit]
Description=Watermarks Remover & Document Studio Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/watermarks-remover
ExecStart=/usr/bin/python3 service/scripts/server.py --host 127.0.0.1 --port 8765
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable watermarks-studio
sudo systemctl start watermarks-studio
```

### 2. Nginx Configuration
Create `/etc/nginx/sites-available/watermarks-studio`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

Enable and test:
```bash
sudo ln -s /etc/nginx/sites-available/watermarks-studio /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 5. Security & Authentication

- To secure your production API, set `WATERMARKS_SERVER_API_KEY=your-secure-secret-token` in your `.env`.
- When set, all HTTP endpoints require:
  `Authorization: Bearer your-secure-secret-token`
