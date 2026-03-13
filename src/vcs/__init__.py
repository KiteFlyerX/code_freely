"""
版本控制模块
提供统一的版本控制接口
"""
from .base import (
    BaseVCS,
    VCSBackend,
    FileInfo,
    CommitInfo,
    DiffInfo,
)
from .git_impl import GitVCS, GitVCSFactory

__all__ = [
    "BaseVCS",
    "VCSBackend",
    "FileInfo",
    "CommitInfo",
    "DiffInfo",
    "GitVCS",
    "GitVCSFactory",
]


def get_vcs(project_path: str) -> BaseVCS | None:
    """
    自动检测并获取项目的版本控制系统

    Args:
        project_path: 项目路径

    Returns:
        VCS 实例，如果不是支持的仓库返回 None
    """
    # 尝试 Git
    git_vcs = GitVCSFactory.create(project_path)
    if git_vcs:
        return git_vcs

    # 未来可以添加 SVN 等其他版本控制系统
    return None
