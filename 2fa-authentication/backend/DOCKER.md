# 🐳 Docker Setup Guide

Complete guide for running the 2FA Authentication System with Docker.

---

## 📋 Prerequisites

- **Docker Desktop** installed and running
  - Windows/Mac: [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
  - Linux: Install Docker Engine and Docker Compose
- **Git** (for cloning the repository)
- **8000**, **5432**, and **6379** ports available

---

## 🚀 Quick Start (Development)

### 1. Clone & Navigate
```bash
git clone https://github.com/yoan9601/vibe-coding-projects.git
cd vibe-coding-projects/2fa-authentication/backend
```

### 2. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set your values
# At minimum, set:
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - TELEGRAM_BOT_TOKEN (get from @BotFather)
```

### 3. Start All Services
```bash
docker-compose up -d
```

This will:
- ✅ Pull Docker images (first time only)
- ✅ Build the backend container
- ✅ Start PostgreSQL database
- ✅ Start Redis cache
- ✅ Run database migrations automatically
- ✅ Start FastAPI application

### 4. Verify Everything is Running
```bash
# Check container status
docker-compose ps

# Should show 3 containers running:
# - vibe_postgres (healthy)
# - vibe_redis (healthy)
# - vibe_backend (healthy)

# Check logs
docker-compose logs backend

# Test the API
curl http://localhost:8000/health
```

### 5. Access the Application
- **API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🛑 Stop Services

```bash
# Stop all containers
docker-compose down

# Stop and remove volumes (deletes database data!)
docker-compose down -v
```

---

## 🏭 Production Deployment

### 1. Use Production Docker Compose
```bash
# Copy production environment template
cp .env.example .env.production

# Edit .env.production with production values
# IMPORTANT: Set strong SECRET_KEY and TELEGRAM_BOT_TOKEN
nano .env.production
```

### 2. Start Production Services
```bash
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

### 3. Create Admin User
```bash
# Access backend container
docker exec -it vibe_backend_prod bash

# Inside container, create admin
python create_admin.py

# Exit container
exit
```

### 4. Monitor Logs
```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

---

## 🔧 Common Operations

### View Logs
```bash
# All services
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# Specific service
docker-compose logs backend
docker-compose logs postgres
docker-compose logs redis

# Last 100 lines
docker-compose logs --tail=100
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Rebuild After Code Changes
```bash
# Rebuild and restart backend
docker-compose up -d --build backend

# Or rebuild everything
docker-compose up -d --build
```

### Access Container Shell
```bash
# Backend container
docker exec -it vibe_backend bash

# PostgreSQL container
docker exec -it vibe_postgres psql -U vibe_user -d vibe_coding_db

# Redis container
docker exec -it vibe_redis redis-cli
```

### Database Operations
```bash
# Run migrations
docker exec -it vibe_backend alembic upgrade head

# Create new migration
docker exec -it vibe_backend alembic revision --autogenerate -m "description"

# Access PostgreSQL
docker exec -it vibe_postgres psql -U vibe_user -d vibe_coding_db

# Backup database
docker exec vibe_postgres pg_dump -U vibe_user vibe_coding_db > backup.sql

# Restore database
cat backup.sql | docker exec -i vibe_postgres psql -U vibe_user -d vibe_coding_db
```

### Redis Operations
```bash
# Access Redis CLI
docker exec -it vibe_redis redis-cli

# Check Redis keys
docker exec -it vibe_redis redis-cli KEYS '*'

# Clear cache
docker exec -it vibe_redis redis-cli FLUSHALL
```

---

## 📊 Health Checks

All services have health checks configured:

```bash
# Check health status
docker-compose ps

# Detailed health check logs
docker inspect vibe_backend | grep -A 10 Health
```

**Health Check Endpoints:**
- **Backend:** `GET /health` - Returns API status
- **PostgreSQL:** `pg_isready` - Database connectivity
- **Redis:** `redis-cli ping` - Cache connectivity

---

## 🐛 Troubleshooting

### Problem: Containers Won't Start

**Check Docker is running:**
```bash
docker ps
```

**Check ports are available:**
```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :5432
netstat -ano | findstr :6379

# Linux/Mac
lsof -i :8000
lsof -i :5432
lsof -i :6379
```

**Check logs for errors:**
```bash
docker-compose logs
```

### Problem: Database Connection Failed

**Ensure PostgreSQL is healthy:**
```bash
docker-compose ps postgres
# Should show "healthy" status

# Check PostgreSQL logs
docker-compose logs postgres
```

**Test database connection:**
```bash
docker exec -it vibe_postgres pg_isready -U vibe_user
```

### Problem: Backend Shows Errors

**Check backend logs:**
```bash
docker-compose logs backend
```

**Verify environment variables:**
```bash
docker exec -it vibe_backend env | grep DATABASE_URL
```

**Restart backend:**
```bash
docker-compose restart backend
```

### Problem: "Module not found" Errors

**Rebuild backend container:**
```bash
docker-compose up -d --build backend
```

### Problem: Migrations Fail

**Check database connection:**
```bash
docker exec -it vibe_backend python -c "from app.database import engine; print(engine.connect())"
```

**Run migrations manually:**
```bash
docker exec -it vibe_backend alembic upgrade head
```

**Reset database (WARNING: deletes all data):**
```bash
docker-compose down -v
docker-compose up -d
```

### Problem: Changes Not Reflected

**For development (with mounted volumes):**
```bash
# Backend automatically reloads with --reload flag
# Just save your file and check logs:
docker-compose logs -f backend
```

**For production or if volumes not working:**
```bash
# Rebuild the container
docker-compose up -d --build backend
```

---

## 🔒 Security Notes

### Development
- Default credentials are in `docker-compose.yml`
- Debug mode is enabled
- Use only on localhost

### Production
- ✅ Set strong `SECRET_KEY` (32+ random characters)
- ✅ Change all default passwords
- ✅ Set `DEBUG=False`
- ✅ Use environment variables for secrets
- ✅ Configure CORS origins properly
- ✅ Use HTTPS in production
- ✅ Keep Docker images updated
- ✅ Regular backups of database

---

## 📝 Environment Variables

### Required Variables (in .env)

```bash
# Security
SECRET_KEY=your-secret-key-here
TELEGRAM_BOT_TOKEN=your-bot-token-here

# Database (override for different setups)
DATABASE_URL=postgresql://vibe_user:vibe_password@postgres:5432/vibe_coding_db

# Application
DEBUG=False  # Set to False in production!
```

### Optional Variables

```bash
# Database credentials (for docker-compose)
POSTGRES_USER=vibe_user
POSTGRES_PASSWORD=vibe_password
POSTGRES_DB=vibe_coding_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# CORS
CORS_ORIGINS=https://yourdomain.com

# Workers (production)
WORKERS=4
```

---

## 📊 Container Resources

### Default Resource Allocation
```yaml
Backend: ~200MB RAM
PostgreSQL: ~100MB RAM  
Redis: ~20MB RAM
Total: ~320MB RAM
```

### Customize Resources (Optional)
Edit `docker-compose.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

---

## 🚀 CI/CD Integration

### GitHub Actions Example
```yaml
name: Docker Build

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker images
        run: docker-compose build
      
      - name: Run tests
        run: docker-compose run backend pytest
```

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI in Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Redis Docker Image](https://hub.docker.com/_/redis)

---

## ✅ Checklist for First-Time Setup

- [ ] Docker Desktop installed and running
- [ ] Repository cloned
- [ ] `.env` file created from `.env.example`
- [ ] `SECRET_KEY` set (use: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] `TELEGRAM_BOT_TOKEN` obtained from @BotFather
- [ ] Ports 8000, 5432, 6379 available
- [ ] Run `docker-compose up -d`
- [ ] Verify with `docker-compose ps` (all healthy)
- [ ] Test API: `curl http://localhost:8000/health`
- [ ] Access Swagger docs: http://localhost:8000/docs
- [ ] Create admin user if needed: `docker exec -it vibe_backend python create_admin.py`

---

**🎉 You're all set! The application is now running in Docker.**

For issues or questions, check the troubleshooting section or open an issue on GitHub.
