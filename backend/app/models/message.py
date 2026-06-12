from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class MessageType(str, enum.Enum):
    """消息类型枚举"""
    ALARM = "alarm"
    APPROVAL = "approval"
    WORKORDER = "workorder"
    ANNOUNCEMENT = "announcement"


class MessagePriority(str, enum.Enum):
    """消息优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Message(Base):
    """消息实体"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    summary = Column(String(500))
    message_type = Column(Enum(MessageType), nullable=False, index=True)
    priority = Column(Enum(MessagePriority), default=MessagePriority.MEDIUM)
    sender_id = Column(Integer)
    sender_name = Column(String(50))
    related_type = Column(String(50))
    related_id = Column(Integer)
    related_url = Column(String(500))
    is_global = Column(Boolean, default=False)
    target_user_ids = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    user_reads = relationship("UserMessageRead", back_populates="message", cascade="all, delete-orphan")


class UserMessageRead(Base):
    """用户消息已读状态"""
    __tablename__ = "user_message_reads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    message = relationship("Message", back_populates="user_reads")
