# 2FA Authentication System

A production-ready authentication system with Telegram 2FA, role-based access control, admin panel, and comprehensive audit logging built with FastAPI.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🌟 Features

### Authentication & Security
- ✅ User registration and login with JWT tokens
- ✅ **Telegram 2FA** - Two-factor authentication via Telegram Bot
- ✅ Bcrypt password hashing
- ✅ Token-based session management
- ✅ Secure code generation and verification

### Role-Based Access Control
- ✅ **Three-tier role system:** User, Moderator, Admin
- ✅ Route protection middleware
- ✅ Permission-based endpoint access
- ✅ Dynamic role assignment (admin only)

### Admin Panel
- ✅ Comprehensive tool management
- ✅ Approval/rejection workflow
- ✅ Advanced filtering (category, status, role)
- ✅ User management dashboard
- ✅ System statistics and analytics

### Performance & Monitoring
- ✅ **Redis caching** - Tool lists and statistics
- ✅ **Audit logging** - All critical actions tracked
- ✅ Activity monitoring
- ✅ IP address logging
- ✅ Connection pooling

## 🏗️ Tech Stack

**Backend Framework:** FastAPI 0.109.0  
**Database:** PostgreSQL 15 + SQLAlchemy ORM  
**Cache:** Redis 7  
**Authentication:** JWT + OAuth2 + Bcrypt  
**2FA:** Telegram Bot API (python-telegram-bot)  
**Migrations:** Alembic  
**Container:** Docker & Docker Compose  

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL 15+
- Redis 7+
- Telegram Bot Token (from @BotFather)
- Git

## 🚀 Quick Start

### Option 1: With Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/vibe-coding-projects.git
cd vibe-coding-projects/2fa-authentication

# Create environment file
cp .env.example .env
# Edit .env with your settings

# Start PostgreSQL and Redis
docker-compose up -d

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
./run.sh
```

### Option 2: Manual Setup

See [QUICKSTART.md](./QUICKSTART.md) for detailed step-by-step instructions.

## 🔧 Configuration

### 1. Create Telegram Bot

1. Open Telegram and find **@BotFather**
2. Send `/newbot`
3. Follow instructions and get your **Bot Token**
4. To get your Chat ID:
   - Send a message to your bot
   - Visit: `https://api.telegram.com/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find `"chat":{"id":123456789}` in the JSON response

### 2. Configure Environment Variables

Edit `.env` file:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/vibe_coding_db

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-from-botfather

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 3. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Create admin user
python create_admin.py
```

### 4. Start Application

```bash
python app/main.py
# or
uvicorn app.main:app --reload
```

API will be available at: `http://localhost:8000`

## 📚 API Documentation

Once running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🔐 API Usage Examples

### Register User

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure123"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure123"
  }'
```

### Setup Telegram 2FA

```bash
curl -X POST "http://localhost:8000/api/auth/setup-telegram" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_chat_id": "123456789"
  }'
```

### Create Tool

```bash
curl -X POST "http://localhost:8000/api/tools" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VS Code",
    "description": "Popular code editor from Microsoft",
    "category": "development",
    "url": "https://code.visualstudio.com"
  }'
```

For more examples, see [API_EXAMPLES.md](./API_EXAMPLES.md)

## 📊 Project Structure

```
2fa-authentication/
├── app/
│   ├── models/              # Database models
│   │   ├── user.py         # User model & roles
│   │   ├── tool.py         # Tool model & enums
│   │   └── audit_log.py    # Audit logging
│   ├── schemas/             # Pydantic schemas
│   │   ├── user.py         # Request/Response schemas
│   │   └── tool.py
│   ├── routers/             # API endpoints
│   │   ├── auth.py         # Authentication routes
│   │   ├── tools.py        # Tool management
│   │   └── admin.py        # Admin panel
│   ├── services/            # Business logic
│   │   ├── telegram.py     # Telegram 2FA service
│   │   ├── cache.py        # Redis caching
│   │   └── audit.py        # Audit logging
│   ├── middleware/          # Custom middleware
│   │   └── auth.py         # Role-based access
│   ├── utils/               # Utilities
│   │   └── security.py     # JWT, password hashing
│   ├── config.py           # Configuration
│   ├── database.py         # Database connection
│   └── main.py             # FastAPI application
├── alembic/                 # Database migrations
├── .github/workflows/       # CI/CD pipeline
├── requirements.txt
├── docker-compose.yml
├── README.md
└── ...
```

## 🎯 Key Endpoints

### Public Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

### Authenticated Endpoints
- `GET /api/auth/me` - Get current user
- `POST /api/auth/setup-telegram` - Setup 2FA
- `POST /api/auth/verify-2fa` - Verify 2FA code
- `POST /api/tools` - Create tool
- `GET /api/tools` - List tools (with filters)
- `GET /api/tools/stats` - Tool statistics

### Moderator/Admin Endpoints
- `GET /api/admin/tools/pending` - Pending tools
- `POST /api/admin/tools/{id}/approve` - Approve/reject tool
- `GET /api/admin/stats/overview` - System statistics

### Admin-Only Endpoints
- `GET /api/admin/users` - List all users
- `PUT /api/admin/users/{id}/role` - Update user role
- `GET /api/admin/audit-logs` - View audit logs

## 🔒 Security Features

- **Password Security:** Bcrypt hashing with salt
- **JWT Tokens:** Secure token-based authentication
- **2FA Codes:** 6-digit codes with 5-minute expiration
- **Role-Based Access:** Three-tier permission system
- **Audit Logging:** All critical actions tracked
- **Environment Variables:** No hardcoded secrets
- **SQL Injection Protection:** SQLAlchemy ORM

## 🎨 Database Schema

### Users
- ID, username, email, password_hash
- Role (user/moderator/admin)
- Telegram chat_id, is_2fa_enabled
- Created timestamp

### Tools
- ID, name, description, category
- Status (pending/approved/rejected)
- URL, created_by, approved_by
- Created/updated timestamps

### Audit Logs
- ID, user_id, action, entity_type
- Entity_id, details (JSON), ip_address
- Timestamp

## 📈 Performance

### Caching Strategy
- Tool lists cached for 5 minutes
- Statistics cached for 5 minutes
- 2FA codes cached for 5 minutes
- Pattern-based cache invalidation

### Optimization
- Database connection pooling
- Indexed database queries
- Pagination support
- Efficient query building

## 🧪 Testing

### Manual Testing
```bash
# Run test script
python test_api.py

# Create test users
python create_admin.py
```

### Automated Testing
GitHub Actions CI/CD pipeline included:
- Code linting (flake8)
- Code formatting check (black)
- Security scanning (bandit)

## 📖 Documentation

- **README.md** - This file
- **QUICKSTART.md** - Get started in 10 minutes
- **API_EXAMPLES.md** - Complete API examples
- **GITHUB_SETUP.md** - GitHub deployment guide
- **PROJECT_OVERVIEW.md** - Technical deep dive
- **CONTRIBUTING.md** - Contribution guidelines

## 🚀 Deployment

### Production Checklist
- [ ] Change SECRET_KEY to a strong random value
- [ ] Update DATABASE_URL with production credentials
- [ ] Configure Redis connection
- [ ] Set up Telegram Bot
- [ ] Enable HTTPS
- [ ] Configure CORS for production domains
- [ ] Set DEBUG=False
- [ ] Run database migrations
- [ ] Create admin user
- [ ] Set up monitoring/logging

### Docker Deployment
```bash
docker-compose up -d
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

See [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 👨‍💻 Author

Built as part of the Vibe Coding course

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- Telegram for the Bot API
- SQLAlchemy for the powerful ORM
- The Vibe Coding community

## 📞 Support

For issues or questions:
1. Check the documentation
2. Review API_EXAMPLES.md
3. Check QUICKSTART.md for setup issues
4. Open an issue on GitHub

---

<div align="center">

**Built with ❤️ using FastAPI**

⭐ Star this project if you find it helpful!

</div>
