from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ToolComment(Base):
    """Tool comment/review model"""
    __tablename__ = "tool_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tool = relationship("Tool", back_populates="comments")
    user = relationship("User", back_populates="comments")
    votes = relationship("CommentVote", back_populates="comment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ToolComment(id={self.id}, tool_id={self.tool_id}, user_id={self.user_id})>"


class CommentVote(Base):
    """User votes on comments (upvote/downvote)"""
    __tablename__ = "comment_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("tool_comments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vote_type = Column(String(10), nullable=False)  # 'upvote' or 'downvote'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    comment = relationship("ToolComment", back_populates="votes")
    user = relationship("User", back_populates="comment_votes")
    
    def __repr__(self):
        return f"<CommentVote(comment_id={self.comment_id}, user_id={self.user_id}, type={self.vote_type})>"
