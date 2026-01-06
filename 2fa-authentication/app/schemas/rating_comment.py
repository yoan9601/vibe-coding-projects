from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Rating schemas
class RatingCreate(BaseModel):
    """Schema for creating/updating a rating"""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")


class RatingResponse(BaseModel):
    """Schema for rating response"""
    id: int
    tool_id: int
    user_id: int
    rating: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RatingStats(BaseModel):
    """Schema for aggregated rating statistics"""
    average_rating: float
    total_ratings: int
    rating_distribution: dict  # {"1": count, "2": count, ...}


# Comment schemas
class CommentCreate(BaseModel):
    """Schema for creating a comment"""
    content: str = Field(..., min_length=10, max_length=2000)


class CommentUpdate(BaseModel):
    """Schema for updating a comment"""
    content: str = Field(..., min_length=10, max_length=2000)


class CommentResponse(BaseModel):
    """Schema for comment response"""
    id: int
    tool_id: int
    user_id: int
    content: str
    username: str
    upvotes: int
    downvotes: int
    user_vote: Optional[str] = None  # "up" or "down" or null
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CommentVoteCreate(BaseModel):
    """Schema for voting on a comment"""
    vote: str = Field(..., pattern="^(up|down)$")


class CommentsListResponse(BaseModel):
    """Schema for paginated comments list"""
    comments: list
    total: int


class CommentVoteResponse(BaseModel):
    """Schema for vote response"""
    id: int
    comment_id: int
    user_id: int
    vote_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True
