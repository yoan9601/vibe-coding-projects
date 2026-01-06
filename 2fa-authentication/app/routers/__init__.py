from app.routers.auth import router as auth_router
from app.routers.tools import router as tools_router
from app.routers.admin import router as admin_router
from app.routers.ratings_comments import router as ratings_router

__all__ = ["auth_router", "tools_router", "admin_router", "ratings_router"]
