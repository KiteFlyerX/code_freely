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

        # 检查并清理旧的锁文件
        self._cleanup_stale_locks(db_path)

        # 创建 SQLite 引擎
        url = f"sqlite:///{db_path}"

        self._engine = create_engine(
            url,
            connect_args={
                "check_same_thread": False,
                "timeout": 60,  # 增加到60秒超时，避免锁定问题
            },
            pool_size=5,  # 连接池大小
            max_overflow=10,  # 最大溢出连接数
            pool_pre_ping=True,  # 连接前先检测，使用连接池自动管理
            echo=False,  # 设为 True 可查看 SQL 日志
        )

        # 启用 WAL 模式以提高并发性能
        from sqlalchemy import text
        with self._engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA busy_timeout=60000"))  # 60秒忙等待
            conn.execute(text("PRAGMA synchronous=NORMAL"))  # 更好的性能
            conn.commit()

        # 创建会话工厂
        self._session_factory = scoped_session(
            sessionmaker(
                bind=self._engine,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False  # 避免对象过期问题
            )
        )

    def _cleanup_stale_locks(self, db_path: Path):
        """清理过期的数据库锁文件"""
        import glob
        try:
            # 查找并删除 -wal 和 -shm 文件
            for pattern in [f"{db_path}-wal", f"{db_path}-shm"]:
                for lock_file in glob.glob(str(pattern)):
                    try:
                        Path(lock_file).unlink(missing_ok=True)
                    except Exception:
                        pass  # 忽略删除失败的文件
        except Exception:
            pass  # 忽略清理错误

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
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        """
        return self._session_factory()

    def safe_query(self, query_func):
        """
        安全查询，自动处理数据库锁定错误

        使用示例:
            def get_user(session):
                return session.query(User).first()

            user = db_manager.safe_query(get_user)
        """
        import time
        max_retries = 3
        retry_delay = 0.1  # 100ms

        for attempt in range(max_retries):
            session = self._session_factory()
            try:
                result = query_func(session)
                session.commit()
                return result
            except Exception as e:
                session.rollback()
                if "database is locked" in str(e).lower() or "locked" in str(e).lower():
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                raise
            finally:
                session.close()

        return None

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
    创建数据目录和表结构，自动迁移缺失的列
    """
    manager = DatabaseManager()
    manager.create_tables()

    # 自动迁移：添加缺失的列
    _migrate_database(manager)

    return manager


def _migrate_database(manager):
    """
    自动迁移数据库，添加缺失的列

    检查并添加新增的列，避免删除现有数据
    """
    from sqlalchemy import inspect, text
    from sqlalchemy.engine import reflection

    engine = manager.engine
    inspector = inspect(engine)

    # 获取现有表
    existing_tables = inspector.get_table_names()

    # 迁移 conversation_messages 表
    if "conversation_messages" in existing_tables:
        # 获取现有列
        columns = [col["name"] for col in inspector.get_columns("conversation_messages")]

        # 需要添加的新列
        new_columns = {
            "input_tokens": "INTEGER",
            "output_tokens": "INTEGER",
            "total_tokens": "INTEGER",
            "context_length": "INTEGER",
        }

        with engine.connect() as conn:
            for column_name, column_type in new_columns.items():
                if column_name not in columns:
                    try:
                        conn.execute(text(f"ALTER TABLE conversation_messages ADD COLUMN {column_name} {column_type}"))
                        conn.commit()
                        print(f"[Migration] Added column: conversation_messages.{column_name}")
                    except Exception as e:
                        # 列可能已存在或其他错误，忽略
                        if f"duplicate column name: {column_name}" not in str(e).lower():
                            print(f"[Migration] Warning adding {column_name}: {e}")


def get_db_session() -> Session:
    """获取数据库会话的便捷函数"""
    return db_manager.get_session_sync()
