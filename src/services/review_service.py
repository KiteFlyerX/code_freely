"""
代码审查服务
管理代码审查流程、评论和评分
"""
from typing import Optional, List, Dict
from datetime import datetime
from dataclasses import dataclass, field

from ..database import get_db_session
from ..database.repositories import ReviewRepository, CodeChangeRepository
from ..models import CodeReview, ReviewStatus, CodeChange


@dataclass
class ReviewComment:
    """行评论"""
    line_number: int
    comment: str


@dataclass
class ReviewCreateInfo:
    """审查创建信息"""
    code_change_id: int
    reviewer: str


@dataclass
class ReviewSubmitInfo:
    """审查提交信息"""
    status: ReviewStatus
    comment: Optional[str] = None
    rating: Optional[int] = None  # 1-5 星
    line_comments: Dict[int, str] = field(default_factory=dict)


@dataclass
class ReviewDetail:
    """审查详情"""
    id: int
    code_change_id: int
    reviewer: str
    status: ReviewStatus
    comment: Optional[str]
    rating: Optional[int]
    line_comments: Optional[Dict[int, str]]
    created_at: datetime
    reviewed_at: Optional[datetime]

    # 关联信息
    file_path: Optional[str] = None
    project_path: Optional[str] = None
    diff: Optional[str] = None
    original_code: Optional[str] = None
    modified_code: Optional[str] = None


@dataclass
class ReviewSummary:
    """审查摘要"""
    code_change_id: int
    file_path: str
    project_path: str
    total_reviews: int
    pending_reviews: int
    approved_reviews: int
    changes_requested: int
    average_rating: Optional[float]
    reviewers: List[str]


class CodeReviewService:
    """
    代码审查服务
    管理代码审查生命周期
    """

    def __init__(self):
        self._review_repo = ReviewRepository(get_db_session())
        self._code_change_repo = CodeChangeRepository(get_db_session())

    def create_review(self, info: ReviewCreateInfo) -> int:
        """
        创建代码审查

        Args:
            info: 审查创建信息

        Returns:
            int: 审查 ID
        """
        # 验证代码修改存在
        code_change = self._code_change_repo.get_by_id(info.code_change_id)
        if not code_change:
            raise ValueError(f"代码修改 {info.code_change_id} 不存在")

        review = self._review_repo.create(
            code_change_id=info.code_change_id,
            reviewer=info.reviewer,
        )
        return review.id

    def get_review(self, review_id: int) -> Optional[ReviewDetail]:
        """
        获取审查详情

        Args:
            review_id: 审查 ID

        Returns:
            ReviewDetail: 审查详情，不存在返回 None
        """
        review = self._review_repo.get_by_id(review_id)
        if not review:
            return None

        # 获取关联的代码修改信息
        code_change = review.code_change
        file_path = None
        project_path = None
        diff = None
        original_code = None
        modified_code = None

        if code_change:
            file_path = code_change.file_path
            project_path = code_change.project_path
            diff = code_change.diff
            original_code = code_change.original_code
            modified_code = code_change.modified_code

        return ReviewDetail(
            id=review.id,
            code_change_id=review.code_change_id,
            reviewer=review.reviewer,
            status=review.status,
            comment=review.comment,
            rating=review.rating,
            line_comments=review.line_comments,
            created_at=review.created_at,
            reviewed_at=review.reviewed_at,
            file_path=file_path,
            project_path=project_path,
            diff=diff,
            original_code=original_code,
            modified_code=modified_code,
        )

    def get_code_change_reviews(self, code_change_id: int) -> List[ReviewDetail]:
        """
        获取代码修改的所有审查

        Args:
            code_change_id: 代码修改 ID

        Returns:
            List[ReviewDetail]: 审查详情列表
        """
        reviews = self._review_repo.get_by_code_change(code_change_id)

        result = []
        for review in reviews:
            result.append(self.get_review(review.id))

        return result

    def submit_review(self, review_id: int, info: ReviewSubmitInfo) -> bool:
        """
        提交审查结果

        Args:
            review_id: 审查 ID
            info: 审查提交信息

        Returns:
            bool: 是否成功
        """
        return self._review_repo.submit_review(
            review_id=review_id,
            status=info.status,
            comment=info.comment,
            rating=info.rating,
            line_comments=info.line_comments,
        )

    def approve(self, review_id: int, comment: Optional[str] = None, rating: int = 5) -> bool:
        """批准审查"""
        return self._review_repo.submit_review(
            review_id=review_id,
            status=ReviewStatus.APPROVED,
            comment=comment,
            rating=rating,
        )

    def request_changes(
        self,
        review_id: int,
        comment: str,
        line_comments: Optional[Dict[int, str]] = None,
    ) -> bool:
        """请求修改"""
        return self._review_repo.submit_review(
            review_id=review_id,
            status=ReviewStatus.CHANGES_REQUESTED,
            comment=comment,
            rating=2,
            line_comments=line_comments or {},
        )

    def get_pending_reviews(self, reviewer: Optional[str] = None, limit: int = 50) -> List[ReviewDetail]:
        """
        获取待审查列表

        Args:
            reviewer: 审查者过滤
            limit: 最大数量

        Returns:
            List[ReviewDetail]: 待审查列表
        """
        reviews = self._review_repo.list_pending(reviewer=reviewer, limit=limit)

        result = []
        for review in reviews:
            result.append(self.get_review(review.id))

        return result

    def get_review_summary(self, code_change_id: int) -> ReviewSummary:
        """
        获取代码修改的审查摘要

        Args:
            code_change_id: 代码修改 ID

        Returns:
            ReviewSummary: 审查摘要
        """
        code_change = self._code_change_repo.get_by_id(code_change_id)
        if not code_change:
            raise ValueError(f"代码修改 {code_change_id} 不存在")

        reviews = self._review_repo.get_by_code_change(code_change_id)

        total = len(reviews)
        pending = sum(1 for r in reviews if r.status == ReviewStatus.PENDING)
        approved = sum(1 for r in reviews if r.status == ReviewStatus.APPROVED)
        changes_requested = sum(1 for r in reviews if r.status == ReviewStatus.CHANGES_REQUESTED)

        # 计算平均评分
        ratings = [r.rating for r in reviews if r.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        # 收集审查者
        reviewers = list(set(r.reviewer for r in reviews))

        return ReviewSummary(
            code_change_id=code_change_id,
            file_path=code_change.file_path,
            project_path=code_change.project_path,
            total_reviews=total,
            pending_reviews=pending,
            approved_reviews=approved,
            changes_requested=changes_requested,
            average_rating=avg_rating,
            reviewers=reviewers,
        )

    def get_reviewer_statistics(
        self, reviewer: str, project_path: Optional[str] = None
    ) -> dict:
        """
        获取审查者统计信息

        Args:
            reviewer: 审查者
            project_path: 项目路径过滤

        Returns:
            dict: 统计信息
        """
        # 获取该审查者的所有审查
        all_reviews = self._review_repo.list_pending(reviewer=None, limit=1000)
        user_reviews = [r for r in all_reviews if r.reviewer == reviewer]

        # 过滤项目路径
        if project_path:
            filtered_reviews = []
            for review in user_reviews:
                if review.code_change and review.code_change.project_path == project_path:
                    filtered_reviews.append(review)
            user_reviews = filtered_reviews

        stats = {
            "total": len(user_reviews),
            "by_status": {},
            "average_rating": 0,
            "total_comments": 0,
        }

        ratings = []

        for review in user_reviews:
            # 按状态统计
            status_key = review.status.value
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1

            # 评分统计
            if review.rating:
                ratings.append(review.rating)

            # 评论统计
            if review.comment:
                stats["total_comments"] += 1

        # 计算平均评分
        if ratings:
            stats["average_rating"] = sum(ratings) / len(ratings)

        return stats

    def can_merge(self, code_change_id: int, min_approvals: int = 1) -> tuple[bool, str]:
        """
        检查代码修改是否可以合并

        Args:
            code_change_id: 代码修改 ID
            min_approvals: 最少需要多少个批准

        Returns:
            tuple[bool, str]: (是否可以合并, 原因说明)
        """
        reviews = self._review_repo.get_by_code_change(code_change_id)

        # 检查是否有待处理的审查
        pending = [r for r in reviews if r.status == ReviewStatus.PENDING]
        if pending:
            return False, f"还有 {len(pending)} 个待处理的审查"

        # 检查批准数量
        approved = [r for r in reviews if r.status == ReviewStatus.APPROVED]
        if len(approved) < min_approvals:
            return False, f"需要至少 {min_approvals} 个批准，当前只有 {len(approved)} 个"

        # 检查是否有请求修改
        changes_requested = [r for r in reviews if r.status == ReviewStatus.CHANGES_REQUESTED]
        if changes_requested:
            return False, f"有 {len(changes_requested)} 个审查请求修改"

        return True, "可以合并"

    def mark_merged(self, code_change_id: int) -> bool:
        """
        标记代码修改为已合并

        Args:
            code_change_id: 代码修改 ID

        Returns:
            bool: 是否成功
        """
        reviews = self._review_repo.get_by_code_change(code_change_id)

        for review in reviews:
            self._review_repo.submit_review(
                review.id,
                ReviewStatus.MERGED,
                review.comment,
                review.rating,
            )

        return True

    def search_reviews(
        self,
        keyword: str,
        reviewer: Optional[str] = None,
        project_path: Optional[str] = None,
        limit: int = 50,
    ) -> List[ReviewDetail]:
        """
        搜索审查

        Args:
            keyword: 关键词
            reviewer: 审查者过滤
            project_path: 项目路径过滤
            limit: 最大数量

        Returns:
            List[ReviewDetail]: 匹配的审查列表
        """
        all_reviews = self._review_repo.list_pending(reviewer=None, limit=1000)

        result = []
        keyword_lower = keyword.lower()

        for review in all_reviews:
            # 审查者过滤
            if reviewer and review.reviewer != reviewer:
                continue

            # 项目路径过滤
            if project_path:
                if not review.code_change or review.code_change.project_path != project_path:
                    continue

            # 关键词搜索
            if (
                (review.comment and keyword_lower in review.comment.lower())
                or (review.line_comments and keyword_lower in str(review.line_comments).lower())
            ):
                result.append(self.get_review(review.id))

        return result[:limit]


# 全局代码审查服务实例
review_service = CodeReviewService()
