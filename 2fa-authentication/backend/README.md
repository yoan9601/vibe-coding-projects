# Backend - FastAPI 2FA Authentication System

FastAPI backend with Telegram 2FA, role-based access, and comprehensive admin panel.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+**
- **PostgreSQL 15**
- **Redis 7**
- **Docker & Docker Compose** (recommended)

---

### Option 1: Docker (Recommended) 🐳

**Complete one-command setup with all services:**

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env and set your values (at minimum):
#    - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
#    - TELEGRAM_BOT_TOKEN (get from @BotFather)

# 3. Start everything
docker-compose up -d
```

**That's it!** Docker will:
- ✅ Build the backend container
- ✅ Start PostgreSQL database
- ✅ Start Redis cache
- ✅ Run database migrations automatically
- ✅ Start FastAPI application

**Access the API:**
- **Backend:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

**Useful Docker commands:**
```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart backend after code changes
docker-compose up -d --build backend

# Create admin user
docker exec -it vibe_backend python create_admin.py

# Access database
docker exec -it vibe_postgres psql -U vibe_user -d vibe_coding_db
```

📚 **[Full Docker Documentation](./DOCKER.md)** - Complete guide with troubleshooting

---

### Option 2: Manual Setup

**1. Install Dependencies:**
```bash
pip install -r requirements.txt
```

**2. Setup Environment:**
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings:
# - DATABASE_URL=postgresql://user:password@localhost:5432/dbname
# - TELEGRAM_BOT_TOKEN=your-bot-token
# - SECRET_KEY=your-secret-key
```

**3. Setup Database:**
```bash
# Ensure PostgreSQL and Redis are running

# Run migrations
alembic upgrade head

# Create admin user
python create_admin.py
```

**4. Start Server:**
```bash
# Development
uvicorn app.main:app --reload

# Or use the helper script
./run.sh
```

---

## 📚 API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## 🔑 Environment Variables

### Required Variables

Create a `.env` file with these values:

```env
# Security (REQUIRED)
SECRET_KEY=your-super-secret-key-change-this
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Application
DEBUG=True
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Get Telegram Bot Token:**
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the token

See [.env.example](./.env.example) for all available options.

---

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py          # User model
│   │   ├── tool.py          # Tool model
│   │   ├── tool_rating.py   # Rating model
│   │   ├── tool_comment.py  # Comment model
│   │   └── audit_log.py     # Audit log model
│   ├── schemas/             # Pydantic schemas
│   │   ├── user.py          # User schemas
│   │   ├── tool.py          # Tool schemas
│   │   └── rating_comment.py # Rating/Comment schemas
│   ├── routers/             # API endpoints
│   │   ├── auth.py          # Authentication & 2FA
│   │   ├── tools.py         # Tool CRUD
│   │   ├── admin.py         # Admin panel
│   │   └── ratings_comments.py  # Ratings & Comments
│   ├── services/            # Business logic
│   │   ├── telegram.py      # Telegram 2FA
│   │   ├── cache.py         # Redis caching
│   │   └── audit.py         # Audit logging
│   ├── middleware/          # Custom middleware
│   │   └── auth.py          # Role-based access
│   └── utils/               # Helper functions
│       └── security.py      # JWT, password hashing
├── alembic/                 # Database migrations
│   ├── versions/            # Migration files
│   └── env.py               # Alembic configuration
├── Dockerfile               # Docker container definition
├── docker-compose.yml       # Docker services (dev)
├── docker-compose.prod.yml  # Docker services (production)
├── .dockerignore            # Docker build optimization
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
├── create_admin.py          # Admin user creation script
├── test_api.py              # API testing script
└── README.md                # This file
```

---

## 🔐 API Endpoints

### Authentication (`/api/auth/`)
- `POST /register` - Register new user
- `POST /login` - Login (returns JWT + 2FA if enabled)
- `POST /verify-2fa` - Verify 2FA code
- `POST /setup-telegram` - Enable Telegram 2FA
- `POST /disable-2fa` - Disable 2FA
- `POST /change-password` - Change password
- `GET /me` - Get current user info

### Tools (`/api/tools/`)
- `GET /` - List tools (with filters & pagination)
- `POST /` - Create new tool
- `GET /{id}` - Get tool details
- `PUT /{id}` - Update tool
- `DELETE /{id}` - Delete tool
- `GET /my` - Get my tools
- `GET /stats` - Get tool statistics

### Ratings (`/api/tools/{id}/`)
- `POST /rate` - Rate a tool (1-5 stars)
- `GET /my-rating` - Get my rating for this tool
- `GET /ratings/stats` - Get rating statistics
- `GET /ratings` - List all ratings
- `DELETE /rate` - Delete my rating

### Comments (`/api/tools/{id}/comments/`)
- `POST /` - Add comment
- `GET /` - List comments (paginated)
- `PUT /{comment_id}` - Update comment
- `DELETE /{comment_id}` - Delete comment
- `POST /{comment_id}/vote` - Vote on comment (up/down)
- `DELETE /{comment_id}/vote` - Remove vote

### Admin (`/api/admin/`)
- `GET /tools/pending` - Get pending tools
- `POST /tools/{id}/approve` - Approve tool
- `POST /tools/{id}/reject` - Reject tool (with reason)
- `GET /users` - List all users
- `PUT /users/{id}/role` - Change user role
- `GET /stats/overview` - Get dashboard statistics
- `GET /audit-logs` - Get audit logs

---

## 🧪 Testing

### Automated Testing
```bash
# Run test script
python test_api.py
```

### Manual Testing
```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

**With Docker:**
```bash
# Run tests inside container
docker exec -it vibe_backend python test_api.py
```

---

## 🛠️ Development

### Create Admin User
```bash
# Manual setup
python create_admin.py

# With Docker
docker exec -it vibe_backend python create_admin.py
```

### Database Migrations

**Manual setup:**
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**With Docker:**
```bash
# Migrations run automatically on container start

# Manual migration
docker exec -it vibe_backend alembic upgrade head

# Create new migration
docker exec -it vibe_backend alembic revision --autogenerate -m "description"
```

### Clear Redis Cache
```bash
# Manual setup
redis-cli FLUSHALL

# With Docker
docker exec -it vibe_redis redis-cli FLUSHALL
```

### Hot Reload During Development

**With Docker:**
- Code changes in `app/` directory auto-reload
- Database changes require migration
- Environment changes need container restart

**Manual setup:**
- Use `uvicorn app.main:app --reload`

---

## 📦 Dependencies

Main packages (see [requirements.txt](./requirements.txt)):
- **FastAPI 0.109.0** - Web framework
- **Uvicorn 0.27.0** - ASGI server
- **SQLAlchemy 2.0.25** - ORM
- **Alembic 1.13.1** - Migrations
- **Pydantic 2.5.3** - Data validation
- **PostgreSQL** - Database (psycopg2-binary)
- **Redis 5.0.1** - Caching
- **python-jose 3.3.0** - JWT
- **passlib 1.7.4** - Password hashing
- **python-telegram-bot 20.7** - Telegram integration

---

## 🔒 Security Features

- ✅ JWT token authentication (30-minute expiration)
- ✅ Bcrypt password hashing with salt
- ✅ Telegram 2FA via bot
- ✅ Role-based access control (User, Moderator, Admin)
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ CORS configuration
- ✅ Environment variables for secrets
- ✅ Comprehensive audit logging
- ✅ Password complexity requirements
- ✅ Token refresh mechanism
- ✅ Rate limiting (via Redis)

---

## 🚀 Deployment

### Docker Production

**1. Create production environment:**
```bash
cp .env.example .env.production

# Edit .env.production with production values:
# - Strong SECRET_KEY
# - Production DATABASE_URL
# - DEBUG=False
# - Proper CORS_ORIGINS
```

**2. Deploy with production compose:**
```bash
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

**3. Create admin user:**
```bash
docker exec -it vibe_backend_prod python create_admin.py
```

### Cloud Platforms

**Railway / Render:**
1. Connect GitHub repository
2. Set environment variables
3. Deploy automatically on push

**AWS / GCP / Azure:**
1. Use Docker image
2. Set up RDS (PostgreSQL) and ElastiCache (Redis)
3. Deploy container to ECS/Cloud Run/Container Instances

### Environment Variables (Production)

```env
# Required in production
SECRET_KEY=strong-random-key-here
TELEGRAM_BOT_TOKEN=your-production-bot-token
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_HOST=your-redis-host
DEBUG=False
CORS_ORIGINS=https://yourdomain.com
```

---

## 📖 Additional Documentation

- **[Docker Setup Guide](./DOCKER.md)** - Complete Docker documentation
- **[API Examples](../API_EXAMPLES.md)** - Detailed API usage examples
- **[Project Overview](../PROJECT_OVERVIEW.md)** - Technical deep dive
- **[Backend Fixes](../BACKEND_FIXES.md)** - API compatibility fixes log

---

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
docker ps | grep postgres
# or
pg_isready

# Verify DATABASE_URL in .env
```

### Redis Connection Error
```bash
# Check Redis is running
docker ps | grep redis
# or
redis-cli ping  # Should return PONG
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# With Docker, rebuild:
docker-compose up -d --build backend
```

### Migrations Fail
```bash
# Check database connection
python -c "from app.database import engine; print(engine.connect())"

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Port Already in Use
```bash
# Check what's using port 8000
# Windows:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000

# Change port in docker-compose.yml or kill the process
```

---

## 📊 Performance

### Optimization Features
- **Redis Caching:** 5-minute TTL for frequently accessed data
- **Database Indexing:** Optimized queries on foreign keys
- **Connection Pooling:** SQLAlchemy pool management
- **Lazy Loading:** Relationships loaded on-demand
- **Pagination:** Efficient data loading

### Monitoring
- Health check endpoint: `/health`
- Request timing in response headers
- Audit logs for tracking
- Redis cache hit rates

---

## 🤝 Contributing

This is a learning project, but feedback is welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

MIT License - See [LICENSE](../../LICENSE) file

---

## 📫 Support

- **Issues:** [GitHub Issues](https://github.com/yoan9601/vibe-coding-projects/issues)
- **Documentation:** [Main README](../../README.md)
- **Project:** [2FA Authentication](../README.md)

---

**Part of:** [2FA Authentication System](../)  
**Main Repo:** [vibe-coding-projects](../../)

---

<div align="center">

**Built with ❤️ during Vibe Coding Course**

Last Updated: January 2026

</div>
