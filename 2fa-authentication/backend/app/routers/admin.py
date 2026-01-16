from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User, UserRole
from app.models.tool import Tool, ToolStatus, ToolCategory
from app.models.audit_log import AuditLog
from app.schemas.tool import ToolResponse, ToolApproval
from app.schemas.user import UserResponse
from app.utils.security import get_current_user
from app.middleware.auth import require_moderator, require_admin
from app.services.cache import cache_service
from app.services.audit import audit_service

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/tools", response_model=List[ToolResponse])
async def get_all_tools_admin(
    category: Optional[ToolCategory] = None,
    status_filter: Optional[ToolStatus] = Query(None, alias="status"),
    created_by: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(require_moderator),
    db: Session = Depends(get_db)
):
    """
    Get all tools with filters (moderator/admin only)
    Supports filtering by category, status, and creator
    """
    
    # Build query
    query = db.query(Tool)
    
    if category:
        query = query.filter(Tool.category == category)
    
    if status_filter:
        query = query.filter(Tool.status == status_filter)
    
    if created_by:
        query = query.filter(Tool.created_by == created_by)
    
    tools = query.order_by(Tool.created_at.desc()).offset(skip).limit(limit).all()
    
    return tools


@router.get("/tools/pending", response_model=List[ToolResponse])
async def get_pending_tools(
    user: User = Depends(require_moderator),
    db: Session = Depends(get_db)
):
    """Get all pending tools awaiting approval (moderator/admin only)"""
    
    tools = db.query(Tool)\
        .filter(Tool.status == ToolStatus.PENDING)\
        .order_by(Tool.created_at.desc())\
        .all()
    
    return tools


@router.post("/tools/{tool_id}/approve", response_model=ToolResponse)
async def approve_tool(
    tool_id: int,
    approval: ToolApproval,
    user: User = Depends(require_moderator),
    db: Session = Depends(get_db)
):
    """Approve or reject a tool (moderator/admin only)"""
    
    # Find tool
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    # Update status
    if approval.approved:
        tool.status = ToolStatus.APPROVED
        tool.rejection_reason = None  # Clear any previous rejection reason
        action = "approve"
    else:
        tool.status = ToolStatus.REJECTED
        tool.rejection_reason = approval.reason  # Save rejection reason!
        action = "reject"
    
    tool.approved_by = user.id
    
    db.commit()
    db.refresh(tool)
    
    # Clear cache
    cache_service.clear_pattern("tools:*")
    
    # Log approval/rejection
    audit_service.log_action(
        db=db,
        user=user,
        action=action,
        entity_type="tool",
        entity_id=tool.id,
        details={
            "status": tool.status.value,
            "reason": approval.reason
        }
    )
    
    return tool


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    role: Optional[UserRole] = None,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all users with optional role filter (admin only)"""
    
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    users = query.offset(skip).limit(limit).all()
    
    return users


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user role (admin only)"""
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from changing their own role
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    old_role = target_user.role
    target_user.role = new_role
    
    db.commit()
    db.refresh(target_user)
    
    # Log role change
    audit_service.log_action(
        db=db,
        user=current_user,
        action="change_role",
        entity_type="user",
        entity_id=target_user.id,
        details={
            "old_role": old_role.value,
            "new_role": new_role.value
        }
    )
    
    return target_user


@router.get("/audit-logs")
async def get_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get audit logs with filters (admin only)"""
    
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return logs


@router.get("/stats/overview")
async def get_admin_stats(
    user: User = Depends(require_moderator),
    db: Session = Depends(get_db)
):
    """Get comprehensive statistics (moderator/admin only)"""
    
    # Try cache first
    cache_key = "admin:stats:overview"
    cached_stats = cache_service.get(cache_key)
    
    if cached_stats:
        return cached_stats
    
    # Calculate stats
    stats = {
        "users": {
            "total": db.query(User).count(),
            "by_role": {
                "user": db.query(User).filter(User.role == UserRole.USER).count(),
                "moderator": db.query(User).filter(User.role == UserRole.MODERATOR).count(),
                "admin": db.query(User).filter(User.role == UserRole.ADMIN).count(),
            },
            "with_2fa": db.query(User).filter(User.is_2fa_enabled == True).count()
        },
        "tools": {
            "total": db.query(Tool).count(),
            "by_status": {
                "pending": db.query(Tool).filter(Tool.status == ToolStatus.PENDING).count(),
                "approved": db.query(Tool).filter(Tool.status == ToolStatus.APPROVED).count(),
                "rejected": db.query(Tool).filter(Tool.status == ToolStatus.REJECTED).count(),
            },
            "by_category": {}
        },
        "activity": {
            "total_actions": db.query(AuditLog).count(),
            "recent_actions": db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).count()
        }
    }
    
    # Count by category
    for category in ToolCategory:
        count = db.query(Tool).filter(Tool.category == category).count()
        stats["tools"]["by_category"][category.value] = count
    
    # Cache for 5 minutes
    cache_service.set(cache_key, stats, expire=300)

    return stats


@router.get("/statistics")
async def get_statistics(
    user: User = Depends(require_moderator),
    db: Session = Depends(get_db)
):
    """Get statistics for admin panel"""
    stats = {
        "users_by_role": [
            {"role": "user", "count": db.query(User).filter(User.role == UserRole.USER).count()},
            {"role": "moderator", "count": db.query(User).filter(User.role == UserRole.MODERATOR).count()},
            {"role": "admin", "count": db.query(User).filter(User.role == UserRole.ADMIN).count()},
        ],
        "tools_by_status": [
            {"status": "pending", "count": db.query(Tool).filter(Tool.status == ToolStatus.PENDING).count()},
            {"status": "approved", "count": db.query(Tool).filter(Tool.status == ToolStatus.APPROVED).count()},
            {"status": "rejected", "count": db.query(Tool).filter(Tool.status == ToolStatus.REJECTED).count()},
        ],
        "tools_by_category": [],
        "recent_activity": []
    }
    
    for category in ToolCategory:
        count = db.query(Tool).filter(Tool.category == category).count()
        stats["tools_by_category"].append({"category": category.value, "count": count})
    
    
    return stats
