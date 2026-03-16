"""
数据模型定义
使用 SQLAlchemy ORM 定义所有数据库模型
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """ORM 基类"""
    pass


class BugStatus(str, Enum):
    """Bug 状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    CLOSED = "closed"


class ReviewStatus(str, Enum):
    """审查状态"""
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    MERGED = "merged"


class Conversation(Base):
    """
    对话记录模型
    记录与 AI 的多轮对话
    """
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    project_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联消息
    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title='{self.title}')>"


class ConversationMessage(Base):
    """对话消息模型"""
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # AI 响应元数据
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Token 统计
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 保留用于兼容
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 输入 tokens
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 输出 tokens
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 总 tokens

    # 上下文信息
    context_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 上下文消息数

    # 关联
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    code_changes: Mapped[List["CodeChange"]] = relationship(
        "CodeChange", back_populates="message", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ConversationMessage(id={self.id}, role='{self.role}')>"


class CodeChange(Base):
    """
    代码修改记录模型
    记录 AI 生成的代码修改
    """
    __tablename__ = "code_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("conversation_messages.id"), nullable=False)

    # 文件信息
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    project_path: Mapped[str] = mapped_column(String(512), nullable=False)

    # 代码内容
    original_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    modified_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    diff: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 版本控制
    branch_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    commit_hash: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # 状态
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # 关联 - 需要指定 foreign_keys 以避免歧义
    message: Mapped["ConversationMessage"] = relationship("ConversationMessage", back_populates="code_changes")
    bugs: Mapped[List["BugReport"]] = relationship(
        "BugReport",
        foreign_keys="BugReport.code_change_id",
        back_populates="code_change",
        cascade="all, delete-orphan"
    )
    reviews: Mapped[List["CodeReview"]] = relationship(
        "CodeReview", back_populates="code_change", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CodeChange(id={self.id}, file_path='{self.file_path}')>"


class BugReport(Base):
    """
    Bug 报告模型
    记录代码相关的 Bug
    """
    __tablename__ = "bug_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code_change_id: Mapped[Optional[int]] = mapped_column(ForeignKey("code_changes.id", name="fk_bug_code_change"), nullable=True)

    # Bug 信息
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[BugStatus] = mapped_column(SQLEnum(BugStatus), default=BugStatus.PENDING)

    # 错误信息
    error_stack: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # 修复信息
    fix_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fix_code_change_id: Mapped[Optional[int]] = mapped_column(ForeignKey("code_changes.id", name="fk_bug_fix_code_change"), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    fixed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关联
    code_change: Mapped[Optional["CodeChange"]] = relationship("CodeChange", foreign_keys=[code_change_id], back_populates="bugs")
    fix_change: Mapped[Optional["CodeChange"]] = relationship(
        "CodeChange", foreign_keys=[fix_code_change_id], post_update=True
    )

    def __repr__(self) -> str:
        return f"<BugReport(id={self.id}, title='{self.title}', status='{self.status}')>"


class CodeReview(Base):
    """
    代码审查模型
    记录代码审查过程
    """
    __tablename__ = "code_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code_change_id: Mapped[int] = mapped_column(ForeignKey("code_changes.id"), nullable=False)

    # 审查信息
    reviewer: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ReviewStatus] = mapped_column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING)

    # 审查结果
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 星

    # 行评论 (JSON 格式: {line_number: comment})
    line_comments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关联
    code_change: Mapped["CodeChange"] = relationship("CodeChange", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<CodeReview(id={self.id}, reviewer='{self.reviewer}', status='{self.status}')>"


class KnowledgeEntry(Base):
    """
    知识库条目模型
    存储从使用中提取的知识
    """
    __tablename__ = "knowledge_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 内容
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # 逗号分隔

    # 关联来源
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # bug, review, conversation
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 使用统计
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        return f"<KnowledgeEntry(id={self.id}, title='{self.title}')>"


class SystemConfig(Base):
    """
    系统配置模型
    存储应用配置
    """
    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        return f"<SystemConfig(key='{self.key}')>"
