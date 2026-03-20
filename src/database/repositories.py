"""
数据访问存储库层
封装对数据库的 CRUD 操作
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import Session, selectinload

from ..models import (
    Conversation,
    ConversationMessage,
    CodeChange,
    BugReport,
    CodeReview,
    KnowledgeEntry,
    SystemConfig,
    BugStatus,
    ReviewStatus,
)


class BaseRepository:
    """基础存储库"""

    def __init__(self, session: Session):
        self.session = session


class ConversationRepository(BaseRepository):
    """对话存储库"""

    def create(self, title: str, project_path: Optional[str] = None) -> Conversation:
        """创建新对话"""
        conversation = Conversation(title=title, project_path=project_path)
        self.session.add(conversation)
        self.session.flush()
        return conversation

    def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """根据 ID 获取对话"""
        return self.session.get(Conversation, conversation_id)

    def list_all(
        self, limit: int = 100, offset: int = 0, project_path: Optional[str] = None
    ) -> List[Conversation]:
        """获取对话列表"""
        query = select(Conversation).order_by(Conversation.updated_at.desc())

        if project_path:
            query = query.where(Conversation.project_path == project_path)

        query = query.limit(limit).offset(offset)
        return list(self.session.scalars(query).all())

    def update_title(self, conversation_id: int, title: str) -> bool:
        """更新对话标题"""
        result = self.session.execute(
            update(Conversation).where(Conversation.id == conversation_id).values(title=title)
        )
        return result.rowcount > 0

    def delete(self, conversation_id: int) -> bool:
        """删除对话"""
        result = self.session.execute(delete(Conversation).where(Conversation.id == conversation_id))
        return result.rowcount > 0


class MessageRepository(BaseRepository):
    """消息存储库"""

    def create(
        self,
        conversation_id: int,
        role: str,
        content: str,
        model: Optional[str] = None,
        tokens_used: Optional[int] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        context_length: Optional[int] = None,
    ) -> ConversationMessage:
        """创建新消息"""
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            tokens_used=tokens_used,  # 保留用于兼容
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            context_length=context_length,
        )
        self.session.add(message)
        self.session.flush()
        return message

    def get_by_conversation(self, conversation_id: int) -> List[ConversationMessage]:
        """获取对话的所有消息"""
        query = select(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.timestamp)
        return list(self.session.scalars(query).all())

    def get_last_n(self, conversation_id: int, n: int = 10) -> List[ConversationMessage]:
        """获取对话的最后 N 条消息"""
        query = select(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.timestamp.desc()).limit(n)
        return list(self.session.scalars(query).all())


class CodeChangeRepository(BaseRepository):
    """代码修改存储库"""

    def create(
        self,
        message_id: int,
        file_path: str,
        project_path: str,
        original_code: Optional[str] = None,
        modified_code: Optional[str] = None,
        diff: Optional[str] = None,
        branch_name: Optional[str] = None,
    ) -> CodeChange:
        """创建代码修改记录"""
        change = CodeChange(
            message_id=message_id,
            file_path=file_path,
            project_path=project_path,
            original_code=original_code,
            modified_code=modified_code,
            diff=diff,
            branch_name=branch_name,
        )
        self.session.add(change)
        self.session.flush()
        return change

    def get_by_id(self, change_id: int) -> Optional[CodeChange]:
        """根据 ID 获取代码修改"""
        return self.session.get(CodeChange, change_id)

    def list_by_project(
        self, project_path: str, limit: int = 100, offset: int = 0
    ) -> List[CodeChange]:
        """获取项目的代码修改列表"""
        query = select(CodeChange).where(
            CodeChange.project_path == project_path
        ).order_by(CodeChange.created_at.desc()).limit(limit).offset(offset)
        return list(self.session.scalars(query).all())

    def mark_applied(self, change_id: int, commit_hash: Optional[str] = None) -> bool:
        """标记代码修改已应用"""
        result = self.session.execute(
            update(CodeChange)
            .where(CodeChange.id == change_id)
            .values(is_applied=True, applied_at=datetime.now(), commit_hash=commit_hash)
        )
        return result.rowcount > 0

    def search(
        self, keyword: str, project_path: Optional[str] = None, limit: int = 50
    ) -> List[CodeChange]:
        """搜索代码修改"""
        query = select(CodeChange).where(
            or_(
                CodeChange.file_path.contains(keyword),
                CodeChange.original_code.contains(keyword),
                CodeChange.modified_code.contains(keyword),
            )
        )

        if project_path:
            query = query.where(CodeChange.project_path == project_path)

        query = query.order_by(CodeChange.created_at.desc()).limit(limit)
        return list(self.session.scalars(query).all())


class BugRepository(BaseRepository):
    """Bug 报告存储库"""

    def create(
        self,
        title: str,
        description: str,
        code_change_id: Optional[int] = None,
        error_stack: Optional[str] = None,
        error_type: Optional[str] = None,
    ) -> BugReport:
        """创建 Bug 报告"""
        bug = BugReport(
            title=title,
            description=description,
            code_change_id=code_change_id,
            error_stack=error_stack,
            error_type=error_type,
            status=BugStatus.PENDING,
        )
        self.session.add(bug)
        self.session.flush()
        return bug

    def get_by_id(self, bug_id: int) -> Optional[BugReport]:
        """根据 ID 获取 Bug"""
        return self.session.get(BugReport, bug_id)

    def list_by_status(
        self, status: Optional[BugStatus] = None, limit: int = 100
    ) -> List[BugReport]:
        """获取 Bug 列表"""
        query = select(BugReport).order_by(BugReport.created_at.desc())

        if status:
            query = query.where(BugReport.status == status)

        query = query.limit(limit)
        return list(self.session.scalars(query).all())

    def update_status(self, bug_id: int, status: BugStatus) -> bool:
        """更新 Bug 状态"""
        values = {"status": status}
        if status == BugStatus.FIXED:
            values["fixed_at"] = datetime.now()

        result = self.session.execute(
            update(BugReport).where(BugReport.id == bug_id).values(**values)
        )
        return result.rowcount > 0

    def link_fix(self, bug_id: int, fix_change_id: int) -> bool:
        """关联修复代码修改"""
        result = self.session.execute(
            update(BugReport)
            .where(BugReport.id == bug_id)
            .values(fix_code_change_id=fix_change_id, status=BugStatus.FIXED, fixed_at=datetime.now())
        )
        return result.rowcount > 0


class ReviewRepository(BaseRepository):
    """代码审查存储库"""

    def create(
        self, code_change_id: int, reviewer: str
    ) -> CodeReview:
        """创建代码审查"""
        review = CodeReview(
            code_change_id=code_change_id,
            reviewer=reviewer,
            status=ReviewStatus.PENDING,
        )
        self.session.add(review)
        self.session.flush()
        return review

    def get_by_code_change(self, code_change_id: int) -> List[CodeReview]:
        """获取代码修改的所有审查"""
        query = select(CodeReview).where(
            CodeReview.code_change_id == code_change_id
        ).order_by(CodeReview.created_at.desc())
        return list(self.session.scalars(query).all())

    def submit_review(
        self,
        review_id: int,
        status: ReviewStatus,
        comment: Optional[str] = None,
        rating: Optional[int] = None,
        line_comments: Optional[Dict[int, str]] = None,
    ) -> bool:
        """提交审查结果"""
        result = self.session.execute(
            update(CodeReview)
            .where(CodeReview.id == review_id)
            .values(
                status=status,
                comment=comment,
                rating=rating,
                line_comments=line_comments,
                reviewed_at=datetime.now(),
            )
        )
        return result.rowcount > 0

    def list_pending(self, reviewer: Optional[str] = None, limit: int = 50) -> List[CodeReview]:
        """获取待审查列表"""
        query = select(CodeReview).where(CodeReview.status == ReviewStatus.PENDING)

        if reviewer:
            query = query.where(CodeReview.reviewer == reviewer)

        query = query.order_by(CodeReview.created_at.desc()).limit(limit)
        return list(self.session.scalars(query).all())


class KnowledgeRepository(BaseRepository):
    """知识库存储库"""

    def create(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        tags: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
    ) -> KnowledgeEntry:
        """创建知识库条目"""
        entry = KnowledgeEntry(
            title=title,
            content=content,
            category=category,
            tags=tags,
            source_type=source_type,
            source_id=source_id,
        )
        self.session.add(entry)
        self.session.flush()
        return entry

    def search(self, keyword: str, category: Optional[str] = None, limit: int = 50) -> List[KnowledgeEntry]:
        """搜索知识库"""
        query = select(KnowledgeEntry).where(
            or_(
                KnowledgeEntry.title.contains(keyword),
                KnowledgeEntry.content.contains(keyword),
                KnowledgeEntry.tags.contains(keyword),
            )
        )

        if category:
            query = query.where(KnowledgeEntry.category == category)

        query = query.order_by(KnowledgeEntry.access_count.desc()).limit(limit)
        return list(self.session.scalars(query).all())

    def get_by_category(self, category: str, limit: int = 50) -> List[KnowledgeEntry]:
        """获取分类下的条目"""
        query = select(KnowledgeEntry).where(
            KnowledgeEntry.category == category
        ).order_by(KnowledgeEntry.access_count.desc()).limit(limit)
        return list(self.session.scalars(query).all())

    def increment_access(self, entry_id: int) -> bool:
        """增加访问计数"""
        result = self.session.execute(
            update(KnowledgeEntry)
            .where(KnowledgeEntry.id == entry_id)
            .values(access_count=KnowledgeEntry.access_count + 1)
        )
        return result.rowcount > 0

    def mark_helpful(self, entry_id: int) -> bool:
        """标记为有帮助"""
        result = self.session.execute(
            update(KnowledgeEntry)
            .where(KnowledgeEntry.id == entry_id)
            .values(helpful_count=KnowledgeEntry.helpful_count + 1)
        )
        return result.rowcount > 0


class ConfigRepository(BaseRepository):
    """配置存储库"""

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取配置值"""
        config = self.session.scalar(select(SystemConfig).where(SystemConfig.key == key))
        return config.value if config else default

    def set(self, key: str, value: str, description: Optional[str] = None) -> None:
        """设置配置值"""
        config = self.session.scalar(select(SystemConfig).where(SystemConfig.key == key))

        if config:
            config.value = value
            config.description = description
        else:
            config = SystemConfig(key=key, value=value, description=description)
            self.session.add(config)

    def delete(self, key: str) -> bool:
        """删除配置"""
        result = self.session.execute(delete(SystemConfig).where(SystemConfig.key == key))
        return result.rowcount > 0

    def get_all(self) -> Dict[str, str]:
        """获取所有配置"""
        configs = self.session.scalars(select(SystemConfig)).all()
        return {c.key: c.value for c in configs}


# ========== 新增的存储库类 ==========

# 导入新模型
try:
    from ..models import Bug, BugSeverity, HistoryEntry, IssueSeverity, ReviewIssue
except ImportError:
    # 如果新模型不可用，使用旧模型
    Bug = BugReport
    BugSeverity = BugStatus
    HistoryEntry = None
    IssueSeverity = None
    ReviewIssue = None


class BugRepository2(BaseRepository):
    """Bug 存储库 (新版本)"""

    def get_all_bugs(self) -> List:
        """获取所有 Bug"""
        if Bug is None:
            return []
        query = select(Bug).order_by(Bug.created_at.desc())
        return list(self.session.scalars(query).all())

    def get_by_id(self, bug_id: int) -> Optional[Bug]:
        """根据 ID 获取 Bug"""
        if Bug is None:
            return None
        return self.session.get(Bug, bug_id)

    def create_bug(
        self,
        title: str,
        description: Optional[str] = None,
        severity: BugSeverity = BugSeverity.MEDIUM,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        error_type: Optional[str] = None,
        error_stack: Optional[str] = None,
    ) -> Bug:
        """创建 Bug"""
        if Bug is None:
            raise ValueError("Bug model not available")
        bug = Bug(
            title=title,
            description=description,
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            error_type=error_type,
            error_stack=error_stack,
        )
        self.session.add(bug)
        self.session.flush()
        return bug


class KnowledgeRepository2(BaseRepository):
    """知识库存储库 (新版本)"""

    def get_all_entries(self) -> List:
        """获取所有知识条目"""
        query = select(KnowledgeEntry).order_by(KnowledgeEntry.created_at.desc())
        return list(self.session.scalars(query).all())

    def get_by_id(self, entry_id: int) -> Optional[KnowledgeEntry]:
        """根据 ID 获取条目"""
        return self.session.get(KnowledgeEntry, entry_id)


class HistoryRepository(BaseRepository):
    """历史记录存储库"""

    def get_all_entries(self) -> List:
        """获取所有历史记录"""
        if HistoryEntry is None:
            return []
        query = select(HistoryEntry).order_by(HistoryEntry.timestamp.desc())
        return list(self.session.scalars(query).all())

    def create_entry(
        self,
        operation_type: str,
        file_path: Optional[str] = None,
        details: Optional[str] = None,
        code_changes: Optional[str] = None,
    ) -> Optional[HistoryEntry]:
        """创建历史记录"""
        if HistoryEntry is None:
            return None
        entry = HistoryEntry(
            operation_type=operation_type,
            file_path=file_path,
            details=details,
            code_changes=code_changes,
        )
        self.session.add(entry)
        self.session.flush()
        return entry


class ReviewRepository2(BaseRepository):
    """代码审查存储库 (新版本)"""

    def get_all_reviews(self) -> List:
        """获取所有审查记录"""
        if ReviewIssue is None:
            return []
        
        # 加载审查及其关联的问题
        query = select(CodeReview).options(
            selectinload(CodeReview.issues)
        ).order_by(CodeReview.review_timestamp.desc())
        
        return list(self.session.scalars(query).all())

    def get_by_id(self, review_id: int) -> Optional[CodeReview]:
        """根据 ID 获取审查"""
        return self.session.get(CodeReview, review_id)
