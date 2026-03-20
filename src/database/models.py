# -*- coding: utf-8 -*-
"""
数据模型
定义所有数据库表模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum
from ..database.manager import Base


class BugSeverity(Enum):
    """Bug 严重程度"""
    CRITICAL = "严重"
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


class BugStatus(Enum):
    """Bug 状态"""
    PENDING = "待处理"
    IN_PROGRESS = "进行中"
    FIXED = "已修复"
    CLOSED = "已关闭"


class Bug(Base):
    """Bug 模型"""
    __tablename__ = "bugs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(SQLEnum(BugSeverity), default=BugSeverity.MEDIUM)
    status = Column(SQLEnum(BugStatus), default=BugStatus.PENDING)
    file_path = Column(String(1000))
    line_number = Column(Integer)
    error_type = Column(String(200))
    error_stack = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    fixed_at = Column(DateTime)


class KnowledgeType(Enum):
    """知识类型"""
    CLASS = "类"
    FUNCTION = "函数"
    MODULE = "模块"
    VARIABLE = "变量"
    CONCEPT = "概念"


class KnowledgeEntry(Base):
    """知识库条目模型"""
    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    code_snippet = Column(Text)
    type = Column(SQLEnum(KnowledgeType), default=KnowledgeType.CONCEPT)
    file_path = Column(String(1000))
    tags = Column(String(500))
    access_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class HistoryEntry(Base):
    """历史记录模型"""
    __tablename__ = "history_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_type = Column(String(100), nullable=False)
    file_path = Column(String(1000))
    details = Column(Text)
    code_changes = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)


class IssueSeverity(Enum):
    """问题严重程度"""
    CRITICAL = "严重"
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"
    INFO = "信息"


class CodeReview(Base):
    """代码审查模型"""
    __tablename__ = "code_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(1000), nullable=False)
    overall_score = Column(Float)
    review_summary = Column(Text)
    review_timestamp = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)


class ReviewIssue(Base):
    """审查问题模型"""
    __tablename__ = "review_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(Integer, ForeignKey("code_reviews.id"))
    issue_type = Column(String(200), nullable=False)
    severity = Column(SQLEnum(IssueSeverity), default=IssueSeverity.MEDIUM)
    description = Column(Text)
    suggested_fix = Column(Text)
    line_number = Column(Integer)
    code_snippet = Column(Text)

    # 关系
    review = relationship("CodeReview", backref="issues")
