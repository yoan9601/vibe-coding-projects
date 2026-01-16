from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class ToolCategory(str, enum.Enum):
    """Tool category enumeration"""
    DEVELOPMENT = "development"
    DESIGN = "design"
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    ANALYTICS = "analytics"
    OTHER = "other"


class ToolStatus(str, enum.Enum):
    """Tool approval status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Tool(Base):
    """Tool model for storing tool information"""
    __tablename__ = "tools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    category = Column(
        SQLEnum(ToolCategory, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    
    status = Column(
        SQLEnum(ToolStatus, values_callable=lambda x: [e.value for e in x]),
        default=ToolStatus.PENDING,
        nullable=False,
        index=True
    )
    
    url = Column(String(500), nullable=True)
    
    # Foreign keys
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="tools", foreign_keys=[created_by])
    approver = relationship("User", back_populates="approved_tools", foreign_keys=[approved_by])
    ratings = relationship("ToolRating", back_populates="tool", cascade="all, delete-orphan")
    comments = relationship("ToolComment", back_populates="tool", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tool(name='{self.name}', category='{self.category}', status='{self.status}')>"