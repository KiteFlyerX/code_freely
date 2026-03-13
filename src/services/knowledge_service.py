"""
知识库服务
自动沉淀知识、分类、标签和全文检索
"""
import re
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import Counter

from ..database import get_db_session
from ..database.repositories import KnowledgeRepository, BugRepository, ReviewRepository
from ..models import KnowledgeEntry


@dataclass
class KnowledgeCreateInfo:
    """知识库条目创建信息"""
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None


@dataclass
class KnowledgeEntryDetail:
    """知识库条目详情"""
    id: int
    title: str
    content: str
    category: Optional[str]
    tags: List[str]
    source_type: Optional[str]
    source_id: Optional[int]
    access_count: int
    helpful_count: int
    created_at: datetime
    updated_at: datetime


@dataclass
class KnowledgeStats:
    """知识库统计"""
    total_entries: int
    entries_by_category: Dict[str, int]
    top_tags: List[tuple[str, int]]
    most_accessed: List[KnowledgeEntryDetail]
    recent_entries: List[KnowledgeEntryDetail]


class KnowledgeService:
    """
    知识库服务
    管理知识的沉淀、分类和检索
    """

    # 预定义分类
    CATEGORIES = [
        "最佳实践",
        "常见问题",
        "错误模式",
        "设计模式",
        "代码规范",
        "工具使用",
        "性能优化",
        "安全建议",
    ]

    def __init__(self):
        self._knowledge_repo = KnowledgeRepository(get_db_session())
        self._bug_repo = BugRepository(get_db_session())
        self._review_repo = ReviewRepository(get_db_session())

    def create_entry(self, info: KnowledgeCreateInfo) -> int:
        """
        创建知识库条目

        Args:
            info: 创建信息

        Returns:
            int: 条目 ID
        """
        # 转换标签列表为逗号分隔字符串
        tags_str = ",".join(info.tags) if info.tags else None

        entry = self._knowledge_repo.create(
            title=info.title,
            content=info.content,
            category=info.category,
            tags=tags_str,
            source_type=info.source_type,
            source_id=info.source_id,
        )
        return entry.id

    def get_entry(self, entry_id: int) -> Optional[KnowledgeEntryDetail]:
        """
        获取知识库条目

        Args:
            entry_id: 条目 ID

        Returns:
            KnowledgeEntryDetail: 条目详情，不存在返回 None
        """
        entry = self._knowledge_repo.session.get(KnowledgeEntry, entry_id)
        if not entry:
            return None

        # 增加访问计数
        self._knowledge_repo.increment_access(entry_id)

        return self._to_detail(entry)

    def search(
        self,
        keyword: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[KnowledgeEntryDetail]:
        """
        搜索知识库

        Args:
            keyword: 关键词
            category: 分类过滤
            tags: 标签过滤
            limit: 最大数量

        Returns:
            List[KnowledgeEntryDetail]: 匹配的条目列表
        """
        entries = self._knowledge_repo.search(keyword=keyword, category=category, limit=limit)

        # 标签过滤
        if tags:
            filtered = []
            for entry in entries:
                entry_tags = self._parse_tags(entry.tags)
                if any(tag in entry_tags for tag in tags):
                    filtered.append(entry)
            entries = filtered

        return [self._to_detail(e) for e in entries]

    def get_by_category(self, category: str, limit: int = 50) -> List[KnowledgeEntryDetail]:
        """
        按分类获取条目

        Args:
            category: 分类名称
            limit: 最大数量

        Returns:
            List[KnowledgeEntryDetail]: 条目列表
        """
        entries = self._knowledge_repo.get_by_category(category=category, limit=limit)
        return [self._to_detail(e) for e in entries]

    def get_recent(self, days: int = 7, limit: int = 20) -> List[KnowledgeEntryDetail]:
        """
        获取最近的条目

        Args:
            days: 天数
            limit: 最大数量

        Returns:
            List[KnowledgeEntryDetail]: 条目列表
        """
        session = self._knowledge_repo.session
        since = datetime.now() - timedelta(days=days)

        entries = (
            session.query(KnowledgeEntry)
            .filter(KnowledgeEntry.created_at >= since)
            .order_by(KnowledgeEntry.created_at.desc())
            .limit(limit)
            .all()
        )

        return [self._to_detail(e) for e in entries]

    def mark_helpful(self, entry_id: int) -> bool:
        """
        标记条目为有帮助

        Args:
            entry_id: 条目 ID

        Returns:
            bool: 是否成功
        """
        return self._knowledge_repo.mark_helpful(entry_id)

    def get_statistics(self) -> KnowledgeStats:
        """
        获取知识库统计

        Returns:
            KnowledgeStats: 统计信息
        """
        session = self._knowledge_repo.session

        # 总条目数
        total = session.query(KnowledgeEntry).count()

        # 按分类统计
        category_stats = {}
        for cat in self.CATEGORIES:
            count = (
                session.query(KnowledgeEntry)
                .filter(KnowledgeEntry.category == cat)
                .count()
            )
            if count > 0:
                category_stats[cat] = count

        # 标签统计
        all_entries = session.query(KnowledgeEntry).all()
        tag_counter = Counter()
        for entry in all_entries:
            tags = self._parse_tags(entry.tags)
            tag_counter.update(tags)

        top_tags = tag_counter.most_common(20)

        # 最常访问
        most_accessed = (
            session.query(KnowledgeEntry)
            .order_by(KnowledgeEntry.access_count.desc())
            .limit(10)
            .all()
        )

        # 最近条目
        recent = (
            session.query(KnowledgeEntry)
            .order_by(KnowledgeEntry.created_at.desc())
            .limit(10)
            .all()
        )

        return KnowledgeStats(
            total_entries=total,
            entries_by_category=category_stats,
            top_tags=top_tags,
            most_accessed=[self._to_detail(e) for e in most_accessed],
            recent_entries=[self._to_detail(e) for e in recent],
        )

    def extract_from_bug(self, bug_id: int) -> Optional[int]:
        """
        从 Bug 提取知识

        Args:
            bug_id: Bug ID

        Returns:
            Optional[int]: 创建的知识条目 ID
        """
        bug = self._bug_repo.get_by_id(bug_id)
        if not bug:
            return None

        # 生成标题
        title = f"Bug: {bug.title}"

        # 生成内容
        content = f"## 问题描述\n\n{bug.description}\n\n"

        if bug.error_type:
            content += f"**错误类型**: {bug.error_type}\n\n"

        if bug.fix_description:
            content += f"## 解决方案\n\n{bug.fix_description}\n\n"

        # 自动分类
        category = self._categorize_bug(bug)

        # 自动标签
        tags = self._generate_tags_from_bug(bug)

        return self.create_entry(
            KnowledgeCreateInfo(
                title=title,
                content=content,
                category=category,
                tags=tags,
                source_type="bug",
                source_id=bug.id,
            )
        )

    def extract_from_review(self, review_id: int) -> Optional[int]:
        """
        从代码审查提取知识

        Args:
            review_id: 审查 ID

        Returns:
            Optional[int]: 创建的知识条目 ID
        """
        review = self._review_repo.get_by_id(review_id)
        if not review or not review.code_change:
            return None

        # 生成标题
        title = f"审查建议: {review.code_change.file_path}"

        # 生成内容
        content = f"## 文件\n\n{review.code_change.file_path}\n\n"

        if review.comment:
            content += f"## 审查意见\n\n{review.comment}\n\n"

        if review.line_comments:
            content += "## 行评论\n\n"
            for line, comment in review.line_comments.items():
                content += f"- **行 {line}**: {comment}\n"

        # 自动标签
        tags = ["代码审查", "代码质量"]
        if review.code_change:
            # 从文件扩展名添加语言标签
            ext = review.code_change.file_path.split(".")[-1]
            if ext:
                tags.append(ext)

        return self.create_entry(
            KnowledgeCreateInfo(
                title=title,
                content=content,
                category="最佳实践",
                tags=tags,
                source_type="review",
                source_id=review.id,
            )
        )

    def extract_from_conversation(
        self, message_id: int, title: Optional[str] = None
    ) -> Optional[int]:
        """
        从对话提取知识

        Args:
            message_id: 消息 ID
            title: 自定义标题

        Returns:
            Optional[int]: 创建的知识条目 ID
        """
        from ..models import ConversationMessage

        session = self._knowledge_repo.session
        message = session.get(ConversationMessage, message_id)

        if not message or message.role != "assistant":
            return None

        # 生成标题
        if not title:
            # 从对话内容的第一行提取标题
            lines = message.content.strip().split("\n")
            title = lines[0][:50] if lines else "AI 对话记录"

        # 生成内容
        content = message.content

        # 自动标签
        tags = self._generate_tags_from_text(content)

        return self.create_entry(
            KnowledgeCreateInfo(
                title=title,
                content=content,
                category="常见问题",
                tags=tags,
                source_type="conversation",
                source_id=message.id,
            )
        )

    def find_similar(self, entry_id: int, limit: int = 5) -> List[KnowledgeEntryDetail]:
        """
        查找相似条目

        Args:
            entry_id: 条目 ID
            limit: 返回数量

        Returns:
            List[KnowledgeEntryDetail]: 相似条目列表
        """
        entry = self._knowledge_repo.session.get(KnowledgeEntry, entry_id)
        if not entry:
            return []

        # 使用标题和内容的关键词搜索
        keywords = self._extract_keywords(entry.title + " " + entry.content)

        results = []
        for keyword in keywords[:3]:  # 使用前3个关键词
            entries = self._knowledge_repo.search(keyword, limit=limit)
            for e in entries:
                if e.id != entry_id:
                    results.append(self._to_detail(e))

        # 去重并限制数量
        seen = set()
        unique_results = []
        for r in results:
            if r.id not in seen:
                seen.add(r.id)
                unique_results.append(r)
                if len(unique_results) >= limit:
                    break

        return unique_results

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return self.CATEGORIES

    def _to_detail(self, entry: KnowledgeEntry) -> KnowledgeEntryDetail:
        """转换为详情对象"""
        return KnowledgeEntryDetail(
            id=entry.id,
            title=entry.title,
            content=entry.content,
            category=entry.category,
            tags=self._parse_tags(entry.tags),
            source_type=entry.source_type,
            source_id=entry.source_id,
            access_count=entry.access_count,
            helpful_count=entry.helpful_count,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )

    def _parse_tags(self, tags_str: Optional[str]) -> List[str]:
        """解析标签字符串"""
        if not tags_str:
            return []
        return [t.strip() for t in tags_str.split(",") if t.strip()]

    def _categorize_bug(self, bug) -> str:
        """自动分类 Bug"""
        if bug.error_type:
            error_lower = bug.error_type.lower()

            # 错误类型映射到分类
            if "syntax" in error_lower:
                return "常见问题"
            elif "import" in error_lower or "module" in error_lower:
                return "常见问题"
            elif "type" in error_lower or "value" in error_lower:
                return "常见问题"
            elif "memory" in error_lower or "leak" in error_lower:
                return "性能优化"
            elif "security" in error_lower or "auth" in error_lower:
                return "安全建议"
            elif "timeout" in error_lower or "slow" in error_lower:
                return "性能优化"

        return "错误模式"

    def _generate_tags_from_bug(self, bug) -> List[str]:
        """从 Bug 生成标签"""
        tags = ["bug"]

        if bug.error_type:
            tags.append(bug.error_type)

        # 从描述中提取关键词
        keywords = self._extract_keywords(bug.description)
        tags.extend(keywords[:2])

        return tags

    def _generate_tags_from_text(self, text: str) -> List[str]:
        """从文本生成标签"""
        keywords = self._extract_keywords(text)
        return keywords[:3]

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 移除代码块
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

        # 分词
        words = re.findall(r"\b[a-zA-Z\u4e00-\u9fa5]{2,}\b", text)

        # 统计词频
        counter = Counter(words)

        # 返回最常见的词
        return [word for word, count in counter.most_common(10)]


# 全局知识库服务实例
knowledge_service = KnowledgeService()
