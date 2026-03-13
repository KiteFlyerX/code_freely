"""
Bug 追踪服务
管理 Bug 报告、状态追踪和修复关联
"""
import traceback
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass

from ..database import get_db_session
from ..database.repositories import BugRepository, CodeChangeRepository
from ..models import BugReport, BugStatus, CodeChange


@dataclass
class BugCreateInfo:
    """Bug 创建信息"""
    title: str
    description: str
    code_change_id: Optional[int] = None
    error_stack: Optional[str] = None
    error_type: Optional[str] = None


@dataclass
class BugUpdateInfo:
    """Bug 更新信息"""
    status: Optional[BugStatus] = None
    fix_description: Optional[str] = None
    fix_code_change_id: Optional[int] = None


@dataclass
class BugDetail:
    """Bug 详情"""
    id: int
    title: str
    description: str
    status: BugStatus
    error_type: Optional[str]
    error_stack: Optional[str]
    fix_description: Optional[str]
    created_at: datetime
    updated_at: datetime
    fixed_at: Optional datetime]
    code_change_id: Optional[int]
    fix_code_change_id: Optional[int]

    # 关联信息
    file_path: Optional[str] = None
    project_path: Optional[str] = None
    code_diff: Optional[str] = None


class BugService:
    """
    Bug 追踪服务
    管理 Bug 生命周期
    """

    def __init__(self):
        self._bug_repo = BugRepository(get_db_session())
        self._code_change_repo = CodeChangeRepository(get_db_session())

    def create_bug(self, info: BugCreateInfo) -> int:
        """
        创建 Bug 报告

        Args:
            info: Bug 创建信息

        Returns:
            int: Bug ID
        """
        bug = self._bug_repo.create(
            title=info.title,
            description=info.description,
            code_change_id=info.code_change_id,
            error_stack=info.error_stack,
            error_type=info.error_type,
        )
        return bug.id

    def create_bug_from_exception(
        self,
        exception: Exception,
        title: str,
        code_change_id: Optional[int] = None,
        additional_context: Optional[str] = None,
    ) -> int:
        """
        从异常创建 Bug 报告

        Args:
            exception: 异常对象
            title: Bug 标题
            code_change_id: 关联的代码修改 ID
            additional_context: 额外上下文信息

        Returns:
            int: Bug ID
        """
        error_type = type(exception).__name__
        error_stack = traceback.format_exc()

        description = f"**错误类型**: {error_type}\n\n"

        if additional_context:
            description += f"**上下文**: {additional_context}\n\n"

        description += f"**堆栈信息**:\n```\n{error_stack}\n```"

        bug = self._bug_repo.create(
            title=title,
            description=description,
            code_change_id=code_change_id,
            error_stack=error_stack,
            error_type=error_type,
        )
        return bug.id

    def get_bug(self, bug_id: int) -> Optional[BugDetail]:
        """
        获取 Bug 详情

        Args:
            bug_id: Bug ID

        Returns:
            BugDetail: Bug 详情，不存在返回 None
        """
        bug = self._bug_repo.get_by_id(bug_id)
        if not bug:
            return None

        # 获取关联的代码修改信息
        file_path = None
        project_path = None
        code_diff = None

        if bug.code_change:
            file_path = bug.code_change.file_path
            project_path = bug.code_change.project_path
            code_diff = bug.code_change.diff

        return BugDetail(
            id=bug.id,
            title=bug.title,
            description=bug.description,
            status=bug.status,
            error_type=bug.error_type,
            error_stack=bug.error_stack,
            fix_description=bug.fix_description,
            created_at=bug.created_at,
            updated_at=bug.updated_at,
            fixed_at=bug.fixed_at,
            code_change_id=bug.code_change_id,
            fix_code_change_id=bug.fix_code_change_id,
            file_path=file_path,
            project_path=project_path,
            code_diff=code_diff,
        )

    def list_bugs(
        self,
        status: Optional[BugStatus] = None,
        project_path: Optional[str] = None,
        limit: int = 50,
    ) -> List[BugDetail]:
        """
        获取 Bug 列表

        Args:
            status: 状态过滤
            project_path: 项目路径过滤
            limit: 最大数量

        Returns:
            List[BugDetail]: Bug 详情列表
        """
        bugs = self._bug_repo.list_by_status(status=status, limit=limit)

        result = []
        for bug in bugs:
            # 获取项目路径
            proj_path = None
            if bug.code_change:
                proj_path = bug.code_change.project_path

            # 过滤项目路径
            if project_path and proj_path != project_path:
                continue

            result.append(BugDetail(
                id=bug.id,
                title=bug.title,
                description=bug.description,
                status=bug.status,
                error_type=bug.error_type,
                error_stack=bug.error_stack,
                fix_description=bug.fix_description,
                created_at=bug.created_at,
                updated_at=bug.updated_at,
                fixed_at=bug.fixed_at,
                code_change_id=bug.code_change_id,
                fix_code_change_id=bug.fix_code_change_id,
                file_path=bug.code_change.file_path if bug.code_change else None,
                project_path=proj_path,
                code_diff=bug.code_change.diff if bug.code_change else None,
            ))

        return result

    def update_bug(self, bug_id: int, info: BugUpdateInfo) -> bool:
        """
        更新 Bug 信息

        Args:
            bug_id: Bug ID
            info: 更新信息

        Returns:
            bool: 是否成功
        """
        bug = self._bug_repo.get_by_id(bug_id)
        if not bug:
            return False

        if info.status:
            self._bug_repo.update_status(bug_id, info.status)

        if info.fix_description:
            bug.fix_description = info.fix_description

        if info.fix_code_change_id:
            self._bug_repo.link_fix(bug_id, info.fix_code_change_id)

        return True

    def link_fix(self, bug_id: int, fix_code_change_id: int) -> bool:
        """
        关联修复代码修改

        Args:
            bug_id: Bug ID
            fix_code_change_id: 修复代码修改 ID

        Returns:
            bool: 是否成功
        """
        return self._bug_repo.link_fix(bug_id, fix_code_change_id)

    def mark_in_progress(self, bug_id: int) -> bool:
        """标记 Bug 为处理中"""
        return self._bug_repo.update_status(bug_id, BugStatus.IN_PROGRESS)

    def mark_fixed(self, bug_id: int, fix_description: Optional[str] = None) -> bool:
        """标记 Bug 为已修复"""
        if fix_description:
            bug = self._bug_repo.get_by_id(bug_id)
            if bug:
                bug.fix_description = fix_description
        return self._bug_repo.update_status(bug_id, BugStatus.FIXED)

    def mark_closed(self, bug_id: int) -> bool:
        """标记 Bug 为已关闭"""
        return self._bug_repo.update_status(bug_id, BugStatus.CLOSED)

    def get_bug_statistics(self, project_path: Optional[str] = None) -> dict:
        """
        获取 Bug 统计信息

        Args:
            project_path: 项目路径过滤

        Returns:
            dict: 统计信息
        """
        bugs = self.list_bugs(project_path=project_path, limit=1000)

        stats = {
            "total": len(bugs),
            "by_status": {},
            "by_error_type": {},
            "fixed_count": 0,
            "avg_fix_time_hours": 0,
        }

        fixed_times = []

        for bug in bugs:
            # 按状态统计
            status_key = bug.status.value
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1

            # 按错误类型统计
            if bug.error_type:
                stats["by_error_type"][bug.error_type] = (
                    stats["by_error_type"].get(bug.error_type, 0) + 1
                )

            # 修复统计
            if bug.status == BugStatus.FIXED and bug.fixed_at:
                stats["fixed_count"] += 1
                if bug.created_at:
                    delta = bug.fixed_at - bug.created_at
                    fixed_times.append(delta.total_seconds() / 3600)

        # 计算平均修复时间
        if fixed_times:
            stats["avg_fix_time_hours"] = sum(fixed_times) / len(fixed_times)

        return stats

    def search_bugs(self, keyword: str, limit: int = 50) -> List[BugDetail]:
        """
        搜索 Bug

        Args:
            keyword: 关键词
            limit: 最大数量

        Returns:
            List[BugDetail]: 匹配的 Bug 列表
        """
        all_bugs = self._bug_repo.list_by_status(limit=1000)

        result = []
        keyword_lower = keyword.lower()

        for bug in all_bugs:
            if (
                keyword_lower in bug.title.lower()
                or keyword_lower in bug.description.lower()
                or (bug.error_type and keyword_lower in bug.error_type.lower())
            ):
                result.append(self.get_bug(bug.id))

        return result[:limit]


# 全局 Bug 服务实例
bug_service = BugService()
