from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.tool import Tool
from app.models.tool_rating import ToolRating
from app.models.tool_comment import ToolComment, CommentVote
from app.schemas.rating_comment import (
    RatingCreate, RatingResponse, RatingStats,
    CommentCreate, CommentUpdate, CommentResponse,
    CommentVoteCreate
)
from app.utils.security import get_current_user
from app.services.cache import cache_service
from app.services.audit import audit_service
from app.middleware.auth import require_moderator

router = APIRouter(prefix="/api/tools", tags=["Ratings & Comments"])


# ===== RATINGS =====

@router.post("/{tool_id}/rate", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def rate_tool(
    tool_id: int,
    rating_data: RatingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rate a tool (1-5 stars). Users can update their existing rating."""
    
    # Check if tool exists
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Check if user already rated this tool
    existing_rating = db.query(ToolRating).filter(
        ToolRating.tool_id == tool_id,
        ToolRating.user_id == user.id
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_data.rating
        db.commit()
        db.refresh(existing_rating)
        rating = existing_rating
        action = "update_rating"
    else:
        # Create new rating
        rating = ToolRating(
            tool_id=tool_id,
            user_id=user.id,
            rating=rating_data.rating
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)
        action = "create_rating"
    
    # Clear rating cache
    cache_service.delete(f"rating:stats:{tool_id}")
    cache_service.clear_pattern("tools:*")
    
    # Log action
    audit_service.log_action(
        db=db,
        user=user,
        action=action,
        entity_type="tool_rating",
        entity_id=rating.id,
        details={"tool_id": tool_id, "rating": rating_data.rating}
    )
    
    return rating


@router.get("/{tool_id}/my-rating")
async def get_my_rating(
    tool_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's rating for a tool"""
    
    rating = db.query(ToolRating).filter(
        ToolRating.tool_id == tool_id,
        ToolRating.user_id == user.id
    ).first()
    
    if rating:
        return {"rating": rating.rating}
    else:
        return {"rating": None}


@router.get("/{tool_id}/ratings/stats", response_model=RatingStats)
async def get_rating_stats(tool_id: int, db: Session = Depends(get_db)):
    """Get rating statistics for a tool"""
    
    # Try cache first
    cache_key = f"rating:stats:{tool_id}"
    cached = cache_service.get(cache_key)
    if cached:
        return cached
    
    # Calculate stats
    ratings = db.query(ToolRating).filter(ToolRating.tool_id == tool_id).all()
    
    if not ratings:
        stats = {
            "average_rating": 0.0,
            "total_ratings": 0,
            "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        }
    else:
        total = len(ratings)
        avg = sum(r.rating for r in ratings) / total
        
        distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        for r in ratings:
            distribution[str(r.rating)] += 1
        
        stats = {
            "average_rating": round(avg, 2),
            "total_ratings": total,
            "rating_distribution": distribution
        }
    
    # Cache for 5 minutes
    cache_service.set(cache_key, stats, expire=300)
    
    return stats


@router.get("/{tool_id}/ratings", response_model=List[RatingResponse])
async def get_tool_ratings(
    tool_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all ratings for a tool"""
    
    ratings = db.query(ToolRating)\
        .filter(ToolRating.tool_id == tool_id)\
        .order_by(ToolRating.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return ratings


@router.delete("/{tool_id}/rate", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating(
    tool_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete your rating for a tool"""
    
    rating = db.query(ToolRating).filter(
        ToolRating.tool_id == tool_id,
        ToolRating.user_id == user.id
    ).first()
    
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    db.delete(rating)
    db.commit()
    
    # Clear cache
    cache_service.delete(f"rating:stats:{tool_id}")
    cache_service.clear_pattern("tools:*")
    
    # Log action
    audit_service.log_action(
        db=db,
        user=user,
        action="delete_rating",
        entity_type="tool_rating",
        entity_id=rating.id,
        details={"tool_id": tool_id}
    )
    
    return None


# ===== COMMENTS =====

@router.post("/{tool_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    tool_id: int,
    comment_data: CommentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a comment on a tool"""
    
    # Check if tool exists
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Create comment
    comment = ToolComment(
        tool_id=tool_id,
        user_id=user.id,
        comment=comment_data.comment
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Clear cache
    cache_service.clear_pattern(f"comments:{tool_id}:*")
    
    # Log action
    audit_service.log_action(
        db=db,
        user=user,
        action="create_comment",
        entity_type="tool_comment",
        entity_id=comment.id,
        details={"tool_id": tool_id}
    )
    
    return comment


@router.get("/{tool_id}/comments", response_model=List[CommentResponse])
async def get_tool_comments(
    tool_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all comments for a tool"""
    
    # Try cache
    cache_key = f"comments:{tool_id}:{skip}:{limit}"
    cached = cache_service.get(cache_key)
    if cached:
        return cached
    
    comments = db.query(ToolComment)\
        .filter(ToolComment.tool_id == tool_id)\
        .order_by(ToolComment.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Add username to each comment
    result = []
    for comment in comments:
        comment_dict = CommentResponse.from_orm(comment).dict()
        comment_dict['username'] = comment.user.username
        result.append(comment_dict)
    
    # Cache for 5 minutes
    cache_service.set(cache_key, result, expire=300)
    
    return result


@router.put("/{tool_id}/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    tool_id: int,
    comment_id: int,
    comment_data: CommentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update your comment"""
    
    comment = db.query(ToolComment).filter(
        ToolComment.id == comment_id,
        ToolComment.tool_id == tool_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check ownership
    if comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    
    # Update
    comment.comment = comment_data.comment
    db.commit()
    db.refresh(comment)
    
    # Clear cache
    cache_service.clear_pattern(f"comments:{tool_id}:*")
    
    # Log action
    audit_service.log_action(
        db=db,
        user=user,
        action="update_comment",
        entity_type="tool_comment",
        entity_id=comment.id,
        details={"tool_id": tool_id}
    )
    
    return comment


@router.delete("/{tool_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    tool_id: int,
    comment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a comment (own comment or moderator)"""
    
    comment = db.query(ToolComment).filter(
        ToolComment.id == comment_id,
        ToolComment.tool_id == tool_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check permissions (owner or moderator)
    from app.models.user import UserRole
    if comment.user_id != user.id and user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    db.delete(comment)
    db.commit()
    
    # Clear cache
    cache_service.clear_pattern(f"comments:{tool_id}:*")
    
    # Log action
    audit_service.log_action(
        db=db,
        user=user,
        action="delete_comment",
        entity_type="tool_comment",
        entity_id=comment.id,
        details={"tool_id": tool_id, "reason": "deleted by moderator" if comment.user_id != user.id else "deleted by owner"}
    )
    
    return None


# ===== COMMENT VOTING =====

@router.post("/{tool_id}/comments/{comment_id}/vote", status_code=status.HTTP_200_OK)
async def vote_on_comment(
    tool_id: int,
    comment_id: int,
    vote_data: CommentVoteCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upvote or downvote a comment"""
    
    # Check if comment exists
    comment = db.query(ToolComment).filter(
        ToolComment.id == comment_id,
        ToolComment.tool_id == tool_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user already voted
    existing_vote = db.query(CommentVote).filter(
        CommentVote.comment_id == comment_id,
        CommentVote.user_id == user.id
    ).first()
    
    if existing_vote:
        # Remove old vote count
        if existing_vote.vote_type == "upvote":
            comment.upvotes -= 1
        else:
            comment.downvotes -= 1
        
        # Update vote type
        existing_vote.vote_type = vote_data.vote_type
    else:
        # Create new vote
        existing_vote = CommentVote(
            comment_id=comment_id,
            user_id=user.id,
            vote_type=vote_data.vote_type
        )
        db.add(existing_vote)
    
    # Add new vote count
    if vote_data.vote_type == "upvote":
        comment.upvotes += 1
    else:
        comment.downvotes += 1
    
    db.commit()
    
    # Clear cache
    cache_service.clear_pattern(f"comments:{tool_id}:*")
    
    return {"message": f"Comment {vote_data.vote_type}d successfully"}


@router.delete("/{tool_id}/comments/{comment_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
async def remove_vote(
    tool_id: int,
    comment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove your vote from a comment"""
    
    vote = db.query(CommentVote).filter(
        CommentVote.comment_id == comment_id,
        CommentVote.user_id == user.id
    ).first()
    
    if not vote:
        raise HTTPException(status_code=404, detail="Vote not found")
    
    # Get comment and update counts
    comment = db.query(ToolComment).filter(ToolComment.id == comment_id).first()
    if comment:
        if vote.vote_type == "upvote":
            comment.upvotes -= 1
        else:
            comment.downvotes -= 1
    
    db.delete(vote)
    db.commit()
    
    # Clear cache
    cache_service.clear_pattern(f"comments:{tool_id}:*")
    
    return None
