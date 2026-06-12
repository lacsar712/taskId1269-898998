from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class KnowledgeCategory(Base):
    """知识库分类"""
    __tablename__ = "knowledge_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(30), unique=True, nullable=False)
    parent_id = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    description = Column(String(200))
    icon = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())


class KnowledgeArticle(Base):
    """知识库文章"""
    __tablename__ = "knowledge_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(String(500))
    content = Column(Text, nullable=False)
    category_id = Column(Integer, index=True)
    tags = Column(Text)
    author_id = Column(Integer)
    author_name = Column(String(50))
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    unhelpful_count = Column(Integer, default=0)
    attachment_names = Column(Text)
    status = Column(String(20), default="published")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class KnowledgeFeedback(Base):
    """知识库文章评价"""
    __tablename__ = "knowledge_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    user_name = Column(String(50))
    is_helpful = Column(Integer, default=0)
    comment = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('article_id', 'user_id', name='uix_article_user'),
    )
