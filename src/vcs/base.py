"""
版本控制抽象层
定义统一的版本控制接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum


class VCSBackend(Enum):
    """版本控制系统类型"""
    GIT = "git"
    SVN = "svn"


@dataclass
class FileInfo:
    """文件信息"""
    path: str
    is_modified: bool
    is_new: bool = False
    is_deleted: bool = False


@dataclass
class CommitInfo:
    """提交信息"""
    hash: str
    author: str
    message: str
    timestamp: datetime
    files_changed: List[str]


@dataclass
class DiffInfo:
    """差异信息"""
    file_path: str
    old_content: str
    new_content: str
    diff_text: str


class BaseVCS(ABC):
    """
    版本控制抽象基类
    所有版本控制系统实现必须继承此类
    """

    def __init__(self, project_path: str):
        """
        初始化版本控制系统

        Args:
            project_path: 项目根目录路径
        """
        self.project_path = project_path

    @abstractmethod
    def is_repo(self) -> bool:
        """
        检查当前目录是否是版本控制仓库

        Returns:
            bool: 是否是仓库
        """
        pass

    @abstractmethod
    def get_current_branch(self) -> Optional[str]:
        """
        获取当前分支名称

        Returns:
            Optional[str]: 分支名称，如果不在任何分支返回 None
        """
        pass

    @abstractmethod
    def create_branch(self, branch_name: str) -> bool:
        """
        创建新分支

        Args:
            branch_name: 分支名称

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    def checkout_branch(self, branch_name: str) -> bool:
        """
        切换到指定分支

        Args:
            branch_name: 分支名称

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    def has_uncommitted_changes(self) -> bool:
        """
        检查是否有未提交的更改

        Returns:
            bool: 是否有未提交的更改
        """
        pass

    @abstractmethod
    def get_modified_files(self) -> List[FileInfo]:
        """
        获取已修改的文件列表

        Returns:
            List[FileInfo]: 修改的文件信息
        """
        pass

    @abstractmethod
    def get_file_content(self, file_path: str, revision: Optional[str] = None) -> Optional[str]:
        """
        获取文件内容

        Args:
            file_path: 文件路径
            revision: 版本号，None 表示当前版本

        Returns:
            Optional[str]: 文件内容，如果文件不存在返回 None
        """
        pass

    @abstractmethod
    def get_diff(self, file_path: str) -> Optional[str]:
        """
        获取文件的差异

        Args:
            file_path: 文件路径

        Returns:
            Optional[str]: 差异文本，如果没有差异返回 None
        """
        pass

    @abstractmethod
    def commit(self, message: str, files: Optional[List[str]] = None) -> Optional[str]:
        """
        提交更改

        Args:
            message: 提交消息
            files: 要提交的文件列表，None 表示所有更改

        Returns:
            Optional[str]: 提交的 hash，失败返回 None
        """
        pass

    @abstractmethod
    def get_recent_commits(self, limit: int = 10) -> List[CommitInfo]:
        """
        获取最近的提交记录

        Args:
            limit: 返回数量

        Returns:
            List[CommitInfo]: 提交信息列表
        """
        pass

    def create_temp_branch(self) -> Optional[str]:
        """
        创建临时分支（用于 AI 修改）

        Returns:
            Optional[str]: 分支名称，失败返回 None
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        branch_name = f"ai-temp-{timestamp}"

        if self.create_branch(branch_name):
            return branch_name
        return None
