# NeuralAudit - Production Deployment Guide

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment (AWS/GCP)](#cloud-deployment)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- Python 3.8+
- pip or conda
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space

### Required Packages
All dependencies are in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### External Dependencies
- Selenium (web automation)
- PyTorch (machine learning)
- FastAPI (web framework)
- SQLAlchemy (database ORM)

---

## Local Development Setup

### Step 1: Clone and Setup
```bash
# Clone repository
git clone https://github.com/sujanian3179/NeuralAudit.git
cd NeuralAudit

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy template to create local .env
cp .env.example .env

# Edit .env with your local settings
# Important: Do NOT commit .env to git
nano .env
```

### Step 3: Verify Installation
```bash
# Test imports
python -c "from app.server import app; print('✅ All imports successful')"

# Run tests
pytest tests/ -v

# Check health
python main.py --api &
curl http://localhost:8000/health
pkill -f "main.py --api"
```

---

## Production Deployment

### Recommended Setup
- **Web Server**: Nginx (reverse proxy)
- **App Server**: Gunicorn (4+ workers)
- **Database**: PostgreSQL or Supabase
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or CloudWatch

### Step 1: Production Configuration
```bash
# Create .env.production with production settings
cat > .env.production << EOF
API_HOST=127.0.0.1
API_PORT=8000
API_DEBUG=False
LOG_LEVEL=WARNING
DEVICE=cuda  # if GPU available
CONFIDENCE_THRESHOLD=0.70
DB_TYPE=supabase
SUPABASE_URL=your-url
SUPABASE_KEY=your-key
MAX_WORKERS=8
EOF

# Set environment variable
export ENV_FILE=.env.production
```

### Step 2: Install Production Server
```bash
# Install Gunicorn for production deployment
pip install gunicorn

# Verify installation
gunicorn --version
```

### Step 3: Start with Gunicorn
```bash
# Basic startup with 4 workers
gunicorn -w 4 \
  -b 127.0.0.1:8000 \
  --env ENV_FILE=.env.production \
  app.server:app

# Advanced configuration (recommended)
gunicorn -w 4 \
  -b 127.0.0.1:8000 \
  --workers-class uvicorn.workers.UvicornWorker \
  --worker-connections 1000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  app.server:app
```

### Step 4: Nginx Reverse Proxy Setup

Create `/etc/nginx/sites-available/neuralaudit`:
```nginx
server {
    listen 80;
    server_name api.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # For long requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }

    # Websocket support (if needed)
    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    location /api {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/neuralaudit /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### Step 5: Systemd Service Setup

Create `/etc/systemd/system/neuralaudit.service`:
```ini
[Unit]
Description=NeuralAudit API Server
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/NeuralAudit
Environment="PATH=/var/www/NeuralAudit/venv/bin"
Environment="ENV_FILE=.env.production"
ExecStart=/var/www/NeuralAudit/venv/bin/gunicorn \
    -w 4 \
    -b 127.0.0.1:8000 \
    --workers-class uvicorn.workers.UvicornWorker \
    app.server:app

# Auto-restart on failure
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable neuralaudit
sudo systemctl start neuralaudit

# Check status
sudo systemctl status neuralaudit

# View logs
sudo journalctl -u neuralaudit -f
```

---

## Docker Deployment

### Step 1: Create Dockerfile

```dockerfile
# Use official Python runtime as base image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    chromium-browser \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "main.py", "--api"]
```

### Step 2: Create Docker Compose File

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      API_HOST: 0.0.0.0
      API_PORT: 8000
      API_DEBUG: "False"
      LOG_LEVEL: INFO
      DEVICE: cpu
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - api

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: neuralaudit
      POSTGRES_PASSWORD: secure-password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Step 3: Build and Run

```bash
# Build image
docker build -t neuralaudit:latest .

# Run container
docker run -p 8000:8000 neuralaudit:latest

# Or use docker-compose
docker-compose up -d

# View logs
docker logs -f neuralaudit-api-1

# Stop
docker-compose down
```

---

## Cloud Deployment

### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init -p python-3.11 neuralaudit

# Create environment
eb create neuralaudit-env

# Deploy
eb deploy

# Monitor
eb logs
eb status
```

### Google Cloud Platform

```bash
# Install Cloud SDK
# Deploy to Cloud Run
gcloud run deploy neuralaudit \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated
```

### Heroku

```bash
# Install Heroku CLI
# Create Procfile
echo "web: gunicorn app.server:app" > Procfile

# Deploy
heroku create neuralaudit
git push heroku main
```

---

## Monitoring & Maintenance

### Logging Setup

```bash
# View logs
tail -f logs/neuralaudit.log

# Rotate logs automatically
cat > /etc/logrotate.d/neuralaudit << EOF
/var/www/NeuralAudit/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
EOF
```

### Performance Monitoring

```bash
# Check resource usage
ps aux | grep gunicorn

# Monitor with htop
htop -p $(pgrep -f gunicorn)

# Database monitoring
# Query slow logs
tail -f /var/log/postgresql/postgresql.log
```

### Backup Strategy

```bash
# Backup database
pg_dump neuralaudit > backup_$(date +%Y%m%d).sql

# Backup models
tar -czf models_backup_$(date +%Y%m%d).tar.gz models/

# Automated backups (cron)
0 2 * * * pg_dump neuralaudit | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
0 3 * * * tar -czf /backups/models_$(date +\%Y\%m\%d).tar.gz models/
```

---

## Troubleshooting

### Issue: Server won't start
```bash
# Check logs
python main.py --api --verbose

# Check port availability
lsof -i :8000

# Kill process if stuck
pkill -f "python.*main.py"
```

### Issue: High memory usage
```bash
# Reduce workers
gunicorn -w 2 app.server:app

# Check for memory leaks
ps aux | grep python
top -p $(pgrep -f gunicorn)
```

### Issue: Slow requests
```bash
# Enable query logging
LOG_LEVEL=DEBUG

# Check database
EXPLAIN ANALYZE SELECT ...

# Monitor network
netstat -an | grep 8000
```

### Issue: Database connection errors
```bash
# Test connection
psql -h localhost -U postgres -d neuralaudit

# Check credentials in .env
cat .env

# Verify database exists
psql -l | grep neuralaudit
```

---

## Performance Tuning

### Gunicorn Workers
```
workers = (2 × CPU_count) + 1
# For 4 CPU: workers = 9 (but 4-8 typical for API)
```

### Database Connection Pool
```python
# In database.py
POOL_SIZE = 20
MAX_OVERFLOW = 0
POOL_TIMEOUT = 30
```

### Caching
```bash
# Add Redis for caching
docker run -d -p 6379:6379 redis:latest

# Update config
REDIS_URL=redis://localhost:6379
```

---

## Production Checklist

- [ ] Environment file properly configured
- [ ] .env is NOT committed to git
- [ ] Database backup strategy in place
- [ ] SSL/TLS certificates installed
- [ ] CORS configured for your domain
- [ ] Logging configured and monitored
- [ ] Monitoring/alerting set up
- [ ] Rate limiting enabled
- [ ] Health check endpoints working
- [ ] Automated scaling configured (if cloud)
- [ ] Failover strategy documented
- [ ] Disaster recovery plan in place

---

## Support & Resources

- **Documentation**: See API_STRUCTURE.md
- **GitHub**: https://github.com/sujanian3179/NeuralAudit
- **Issues**: Check GitHub issues
- **Logs**: Check `logs/` directory

---

**Version**: 1.0.0
**Last Updated**: April 25, 2024
