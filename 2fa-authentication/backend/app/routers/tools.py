from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.tool import Tool, ToolStatus, ToolCategory
from app.models.tool_rating import ToolRating
from app.models.tool_comment import ToolComment
from app.schemas.tool import (
    ToolCreate, ToolUpdate, ToolResponse, ToolDetailResponse
)
from app.utils.security import get_current_user, get_current_user_optional
from app.services.cache import cache_service
from app.services.audit import audit_service

router = APIRouter(prefix="/api/tools", tags=["Tools"])


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_data: ToolCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new tool (requires authentication)"""
    new_tool = Tool(
        name=tool_data.name,
        description=tool_data.description,
        category=tool_data.category,
        url=tool_data.url,
        created_by=user.id,
        status=ToolStatus.PENDING
    )
    db.add(new_tool)
    db.commit()
    db.refresh(new_tool)
    cache_service.clear_pattern("tools:*")
    audit_service.log_action(
        db=db,
        user=user,
        action="create",
        entity_type="tool",
        entity_id=new_tool.id,
        details={"name": new_tool.name, "category": new_tool.category.value}
    )
    return new_tool


@router.get("/search", response_model=List[ToolResponse])
async def search_tools(
    q: str = Query(..., min_length=1, description="Search query"),
    category: Optional[ToolCategory] = None,
    status_filter: Optional[ToolStatus] = Query(None, alias="status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search tools by name or description"""
    search_pattern = f"%{q}%"
    query = db.query(Tool).filter(
        or_(
            Tool.name.ilike(search_pattern),
            Tool.description.ilike(search_pattern)
        )
    )
    if category:
        query = query.filter(Tool.category == category)
    if status_filter:
        query = query.filter(Tool.status == status_filter)
    tools = query.offset(skip).limit(limit).all()
    return tools


@router.get("/stats")
async def get_tools_stats(db: Session = Depends(get_db)):
    """Get statistics about tools (cached)"""
    cache_key = "tools:stats"
    cached_stats = cache_service.get(cache_key)
    if cached_stats:
        return cached_stats
    stats = {
        "total": db.query(Tool).count(),
        "by_status": {
            "pending": db.query(Tool).filter(Tool.status == ToolStatus.PENDING).count(),
            "approved": db.query(Tool).filter(Tool.status == ToolStatus.APPROVED).count(),
            "rejected": db.query(Tool).filter(Tool.status == ToolStatus.REJECTED).count(),
        },
        "by_category": {}
    }
    for category in ToolCategory:
        count = db.query(Tool).filter(Tool.category == category).count()
        stats["by_category"][category.value] = count
    cache_service.set(cache_key, stats, expire=300)
    return stats


@router.get("/my")
async def get_my_tools(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tools created by current user"""
    tools = db.query(Tool).filter(Tool.created_by == user.id).order_by(Tool.created_at.desc()).all()
    
    tools_with_ratings = []
    for tool in tools:
        tool_dict = {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "status": tool.status,
            "url": tool.url,
            "created_by": tool.created_by,
            "approved_by": tool.approved_by,
            "rejection_reason": tool.rejection_reason,
            "created_at": tool.created_at,
            "updated_at": tool.updated_at,
            "average_rating": None,
            "total_ratings": 0
        }
        if tool.ratings:
            total_ratings = len(tool.ratings)
            sum_ratings = sum(r.rating for r in tool.ratings)
            tool_dict["average_rating"] = round(sum_ratings / total_ratings, 2) if total_ratings > 0 else None
            tool_dict["total_ratings"] = total_ratings
        tools_with_ratings.append(tool_dict)
    
    return tools_with_ratings


@router.get("")
async def get_tools(
    category: Optional[ToolCategory] = None,
    status_filter: Optional[ToolStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of tools with optional filters"""
    query = db.query(Tool)
    if category:
        query = query.filter(Tool.category == category)
    if status_filter:
        query = query.filter(Tool.status == status_filter)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Tool.name.ilike(search_pattern),
                Tool.description.ilike(search_pattern)
            )
        )
    total = query.count()
    tools = query.order_by(Tool.created_at.desc()).offset(skip).limit(limit).all()
    
    tools_with_ratings = []
    for tool in tools:
        tool_dict = {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "status": tool.status,
            "url": tool.url,
            "created_by": tool.created_by,
            "approved_by": tool.approved_by,
            "rejection_reason": tool.rejection_reason,
            "created_at": tool.created_at,
            "updated_at": tool.updated_at,
            "average_rating": None,
            "total_ratings": 0
        }
        if tool.ratings:
            total_ratings = len(tool.ratings)
            sum_ratings = sum(r.rating for r in tool.ratings)
            tool_dict["average_rating"] = round(sum_ratings / total_ratings, 2) if total_ratings > 0 else None
            tool_dict["total_ratings"] = total_ratings
        tools_with_ratings.append(tool_dict)
    return {"tools": tools_with_ratings, "total": total}


@router.get("/{tool_id}", response_model=ToolDetailResponse)
async def get_tool(
    tool_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get a specific tool by ID with extended details"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    tool_dict = {
        **{k: v for k, v in tool.__dict__.items() if not k.startswith('_')},
        "created_by_username": tool.creator.username if tool.creator else None,
        "approved_by_username": tool.approver.username if tool.approver else None,
    }
    if tool.ratings:
        total_ratings = len(tool.ratings)
        sum_ratings = sum(r.rating for r in tool.ratings)
        tool_dict["average_rating"] = round(sum_ratings / total_ratings, 2) if total_ratings > 0 else None
        tool_dict["total_ratings"] = total_ratings
    else:
        tool_dict["average_rating"] = None
        tool_dict["total_ratings"] = 0
    tool_dict["user_rating"] = None
    if current_user:
        user_rating = db.query(ToolRating).filter(
            ToolRating.tool_id == tool_id,
            ToolRating.user_id == current_user.id
        ).first()
        if user_rating:
            tool_dict["user_rating"] = user_rating.rating
    tool_dict["total_comments"] = db.query(ToolComment).filter(ToolComment.tool_id == tool_id).count()
    return tool_dict


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: int,
    tool_data: ToolUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a tool (only creator or admin can update)"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    from app.models.user import UserRole
    if tool.created_by != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this tool"
        )
    update_data = tool_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tool, field, value)
    db.commit()
    db.refresh(tool)
    cache_service.clear_pattern("tools:*")
    audit_service.log_action(
        db=db,
        user=user,
        action="update",
        entity_type="tool",
        entity_id=tool.id,
        details=update_data
    )
    return tool


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a tool (only creator or admin can delete)"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    from app.models.user import UserRole
    if tool.created_by != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this tool"
        )
    audit_service.log_action(
        db=db,
        user=user,
        action="delete",
        entity_type="tool",
        entity_id=tool.id,
        details={"name": tool.name}
    )
    db.delete(tool)
    db.commit()
    cache_service.clear_pattern("tools:*")
    return None