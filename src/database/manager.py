"""
数据库管理模块
提供数据库连接、会话管理和初始化
"""
import os
from pathlib import Path
from typing import Optional, Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool

from ..models import Base


class DatabaseManager:
    """
    数据库管理器
    单例模式，管理数据库连接和会话
    """

    _instance: Optional["DatabaseManager"] = None
    _engine: Optional[Engine] = None
    _session_factory: Optional[scoped_session] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._engine is None:
            self._initialize_database()

    def _get_data_dir(self) -> Path:
        """获取数据目录路径"""
        home = Path.home()
        data_dir = home / ".codetrace" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def _get_database_path(self) -> Path:
        """获取数据库文件路径"""
        return self._get_data_dir() / "codetrace.db"

    def _initialize_database(self):
        """初始化数据库连接"""
        db_path = self._get_database_path()

        # 创建 SQLite 引擎
        url = f"sqlite:///{db_path}"

        self._engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # 单连接模式，适合 SQLite
            echo=False,  # 设为 True 可查看 SQL 日志
        )

        # 创建会话工厂
        self._session_factory = scoped_session(
            sessionmaker(bind=self._engine, autoflush=False, autocommit=False)
        )

    @property
    def engine(self) -> Engine:
        """获取数据库引擎"""
        if self._engine is None:
            self._initialize_database()
        return self._engine

    def create_tables(self):
        """创建所有数据表"""
        Base.metadata.create_all(self.engine)

    def drop_tables(self):
        """删除所有数据表（慎用）"""
        Base.metadata.drop_all(self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话（上下文管理器）

        使用示例:
            with db_manager.get_session() as session:
                user = session.query(User).first()
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session_sync(self) -> Session:
        """
        获取数据库会话（手动管理）

        使用示例:
            session = db_manager.get_session_sync()
            try:
                user = session.query(User).first()
                session.commit()
            finally:
                session.close()
        """
        return self._session_factory()

    def close(self):
        """关闭数据库连接"""
        if self._session_factory:
            self._session_factory.remove()
        if self._engine:
            self._engine.dispose()


# 全局数据库管理器实例
db_manager = DatabaseManager()


def init_database():
    """
    初始化数据库
    创建数据目录和表结构
    """
    manager = DatabaseManager()
    manager.create_tables()
    return manager


def get_db_session() -> Session:
    """获取数据库会话的便捷函数"""
    return db_manager.get_session_sync()
