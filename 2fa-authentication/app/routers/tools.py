from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.tool import Tool, ToolStatus, ToolCategory
from app.schemas.tool import ToolCreate, ToolUpdate, ToolResponse
from app.utils.security import get_current_user
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
    
    # Create new tool
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
    
    # Clear cache
    cache_service.clear_pattern("tools:*")
    
    # Log creation
    audit_service.log_action(
        db=db,
        user=user,
        action="create",
        entity_type="tool",
        entity_id=new_tool.id,
        details={"name": new_tool.name, "category": new_tool.category.value}
    )
    
    return new_tool


@router.get("", response_model=List[ToolResponse])
async def get_tools(
    category: Optional[ToolCategory] = None,
    status_filter: Optional[ToolStatus] = Query(None, alias="status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of tools with optional filters"""
    
    # Try to get from cache
    cache_key = f"tools:list:{category}:{status_filter}:{skip}:{limit}"
    cached_data = cache_service.get(cache_key)
    
    if cached_data:
        return cached_data
    
    # Build query
    query = db.query(Tool)
    
    if category:
        query = query.filter(Tool.category == category)
    
    if status_filter:
        query = query.filter(Tool.status == status_filter)
    
    tools = query.offset(skip).limit(limit).all()
    
    # Cache results
    cache_service.set(cache_key, [ToolResponse.from_orm(t).dict() for t in tools], expire=300)
    
    return tools


@router.get("/stats")
async def get_tools_stats(db: Session = Depends(get_db)):
    """Get statistics about tools (cached)"""
    
    # Try cache first
    cache_key = "tools:stats"
    cached_stats = cache_service.get(cache_key)
    
    if cached_stats:
        return cached_stats
    
    # Calculate stats
    stats = {
        "total": db.query(Tool).count(),
        "by_status": {
            "pending": db.query(Tool).filter(Tool.status == ToolStatus.PENDING).count(),
            "approved": db.query(Tool).filter(Tool.status == ToolStatus.APPROVED).count(),
            "rejected": db.query(Tool).filter(Tool.status == ToolStatus.REJECTED).count(),
        },
        "by_category": {}
    }
    
    # Count by category
    for category in ToolCategory:
        count = db.query(Tool).filter(Tool.category == category).count()
        stats["by_category"][category.value] = count
    
    # Cache stats for 5 minutes
    cache_service.set(cache_key, stats, expire=300)
    
    return stats


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(tool_id: int, db: Session = Depends(get_db)):
    """Get a specific tool by ID"""
    
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    return tool


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
    
    # Check permissions
    from app.models.user import UserRole
    if tool.created_by != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this tool"
        )
    
    # Update fields
    update_data = tool_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tool, field, value)
    
    db.commit()
    db.refresh(tool)
    
    # Clear cache
    cache_service.clear_pattern("tools:*")
    
    # Log update
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
    
    # Check permissions
    from app.models.user import UserRole
    if tool.created_by != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this tool"
        )
    
    # Log before deletion
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
    
    # Clear cache
    cache_service.clear_pattern("tools:*")
    
    return None


@router.get("/my", response_model=List[ToolResponse])
async def get_my_tools(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tools created by current user"""
    
    tools = db.query(Tool).filter(Tool.created_by == user.id).all()
    return tools
