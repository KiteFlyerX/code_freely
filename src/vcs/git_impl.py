"""
Git 版本控制实现
使用 GitPython 库实现 Git 操作
"""
from typing import Optional, List
from pathlib import Path
import git as gitpython

from .base import BaseVCS, VCSBackend, FileInfo, CommitInfo, DiffInfo


class GitVCS(BaseVCS):
    """
    Git 版本控制实现
    """

    def __init__(self, project_path: str):
        super().__init__(project_path)
        self._repo: Optional[gitpython.Repo] = None

    @property
    def repo(self) -> Optional[gitpython.Repo]:
        """获取 Git 仓库对象"""
        if self._repo is None:
            try:
                self._repo = gitpython.Repo(self.project_path)
            except Exception:
                return None
        return self._repo

    def is_repo(self) -> bool:
        """检查是否是 Git 仓库"""
        try:
            gitpython.Repo(self.project_path)
            return True
        except Exception:
            return False

    def get_current_branch(self) -> Optional[str]:
        """获取当前分支名称"""
        if not self.repo:
            return None

        try:
            return self.repo.active_branch.name
        except Exception:
            # 可能在 detached HEAD 状态
            return None

    def create_branch(self, branch_name: str) -> bool:
        """创建新分支"""
        if not self.repo:
            return False

        try:
            # 创建新分支
            new_branch = self.repo.create_head(branch_name)
            # 切换到新分支
            new_branch.checkout()
            return True
        except Exception:
            return False

    def checkout_branch(self, branch_name: str) -> bool:
        """切换到指定分支"""
        if not self.repo:
            return False

        try:
            self.repo.heads[branch_name].checkout()
            return True
        except Exception:
            return False

    def has_uncommitted_changes(self) -> bool:
        """检查是否有未提交的更改"""
        if not self.repo:
            return False

        return self.repo.is_dirty()

    def get_modified_files(self) -> List[FileInfo]:
        """获取已修改的文件列表"""
        if not self.repo:
            return []

        files = []

        # 获取已修改的文件
        for item in self.repo.index.diff(None):
            files.append(FileInfo(
                path=item.a_path,
                is_modified=True,
            ))

        # 获取新文件
        for item in self.repo.untracked_files:
            files.append(FileInfo(
                path=item,
                is_modified=False,
                is_new=True,
            ))

        return files

    def get_file_content(self, file_path: str, revision: Optional[str] = None) -> Optional[str]:
        """
        获取文件内容

        Args:
            file_path: 文件路径（相对于项目根目录）
            revision: 版本号（commit hash），None 表示当前工作区
        """
        if not self.repo:
            return None

        try:
            if revision is None:
                # 读取工作区文件
                full_path = Path(self.project_path) / file_path
                return full_path.read_text(encoding="utf-8")
            else:
                # 读取指定版本
                commit = self.repo.commit(revision)
                blob = commit.tree[file_path]
                return blob.data_stream.read().decode("utf-8")
        except Exception:
            return None

    def get_diff(self, file_path: str) -> Optional[str]:
        """获取文件的差异"""
        if not self.repo:
            return None

        try:
            # 获取工作区与暂存区的差异
            diff = self.repo.index.diff(None, paths=file_path, create_patch=True)
            if diff:
                return diff[0].diff.decode("utf-8") if isinstance(diff[0].diff, bytes) else str(diff[0].diff)

            # 获取暂存区与上次提交的差异
            diff_cached = self.repo.index.diff("HEAD", paths=file_path, create_patch=True)
            if diff_cached:
                d = diff_cached[0]
                return d.diff.decode("utf-8") if isinstance(d.diff, bytes) else str(d.diff)

            return None
        except Exception:
            return None

    def commit(self, message: str, files: Optional[List[str]] = None) -> Optional[str]:
        """提交更改"""
        if not self.repo:
            return None

        try:
            # 添加文件到暂存区
            if files:
                self.repo.index.add(files)
            else:
                self.repo.index.add([item.a_path for item in self.repo.index.diff(None)])
                self.repo.index.add(self.repo.untracked_files)

            # 提交
            commit = self.repo.index.commit(message)
            return commit.hexsha
        except Exception:
            return None

    def get_recent_commits(self, limit: int = 10) -> List[CommitInfo]:
        """获取最近的提交记录"""
        if not self.repo:
            return []

        commits = []

        for commit in list(self.repo.iter_commits(max_count=limit)):
            commits.append(CommitInfo(
                hash=commit.hexsha,
                author=commit.author.name,
                message=commit.message.strip(),
                timestamp=commit.committed_datetime,
                files_changed=[item.a_path for item in commit.stats.files],
            ))

        return commits

    def get_full_diff(self, file_path: str, old_revision: str, new_revision: Optional[str] = None) -> Optional[str]:
        """
        获取两个版本之间的完整差异

        Args:
            file_path: 文件路径
            old_revision: 旧版本
            new_revision: 新版本，None 表示工作区
        """
        if not self.repo:
            return None

        try:
            if new_revision is None:
                # 工作区与指定版本的差异
                commit = self.repo.commit(old_revision)
                diff = self.repo.git.diff(commit, file_path)
            else:
                # 两个版本之间的差异
                diff = self.repo.git.diff(old_revision, new_revision, file_path)

            return diff
        except Exception:
            return None

    def stash_changes(self) -> bool:
        """暂存当前更改"""
        if not self.repo:
            return False

        try:
            self.repo.git.stash()
            return True
        except Exception:
            return False

    def stash_pop(self) -> bool:
        """恢复暂存的更改"""
        if not self.repo:
            return False

        try:
            self.repo.git.stash("pop")
            return True
        except Exception:
            return False


class GitVCSFactory:
    """Git VCS 工厂类"""

    @staticmethod
    def create(project_path: str) -> Optional[GitVCS]:
        """
        创建 Git VCS 实例

        Args:
            project_path: 项目路径

        Returns:
            GitVCS 实例，如果不是 Git 仓库返回 None
        """
        vcs = GitVCS(project_path)
        if vcs.is_repo():
            return vcs
        return None

    @staticmethod
    def detect_vcs(project_path: str) -> Optional[VCSBackend]:
        """
        检测项目使用的版本控制系统

        Args:
            project_path: 项目路径

        Returns:
            VCSBackend 类型，如果不是支持的仓库返回 None
        """
        if GitVCS(project_path).is_repo():
            return VCSBackend.GIT
        return None
