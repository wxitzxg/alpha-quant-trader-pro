"""统一的数据库连接管理"""

import logging
from contextlib import contextmanager
from typing import Optional, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session

logger = logging.getLogger(__name__)

Base = declarative_base()


class DatabaseManager:
    """
    统一的数据库连接管理器

    特性：
    - 连接池管理
    - 事务自动处理
    - 连接健康检查
    - 统一的错误处理
    """

    def __init__(
        self,
        db_url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_pre_ping: bool = True,
        pool_recycle: int = 3600,
        echo: bool = False
    ):
        """
        初始化数据库连接

        Args:
            db_url: 数据库连接字符串 (e.g., "postgresql://user:pass@localhost/dbname")
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            pool_pre_ping: 连接前检查可用性
            pool_recycle: 连接回收时间（秒）
            echo: 是否输出 SQL 日志
        """
        self.db_url = db_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow

        # 创建数据库引擎
        self.engine = create_engine(
            db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            pool_recycle=pool_recycle,
            echo=echo
        )

        # 创建会话工厂
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )

        # 创建 scoped_session 用于线程安全
        self.scoped_session = scoped_session(self.session_factory)

        logger.info(
            f"DatabaseManager initialized: {db_url}, "
            f"pool_size={pool_size}, max_overflow={max_overflow}"
        )

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话（上下文管理器）

        使用示例：
            with db_manager.get_session() as session:
                # 执行数据库操作
                session.query(User).all()

        Yields:
            SQLAlchemy Session 对象

        Raises:
            DatabaseError: 数据库操作异常
        """
        session = self.scoped_session
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            from common.exceptions import DatabaseError
            raise DatabaseError(
                message=f"Database session error: {str(e)}",
                original_error=e
            )
        finally:
            session.close()

    def create_all(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("All tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}", exc_info=True)
            from common.exceptions import DatabaseError
            raise DatabaseError(
                message=f"Failed to create tables: {str(e)}",
                original_error=e
            )

    def drop_all(self):
        """删除所有表（测试用）"""
        try:
            Base.metadata.drop_all(self.engine)
            logger.info("All tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}", exc_info=True)
            from common.exceptions import DatabaseError
            raise DatabaseError(
                message=f"Failed to drop tables: {str(e)}",
                original_error=e
            )

    def dispose(self):
        """释放数据库连接池"""
        try:
            self.engine.dispose()
            logger.info("Database connection pool disposed")
        except Exception as e:
            logger.error(f"Failed to dispose connection pool: {e}", exc_info=True)
            raise

    def __del__(self):
        """析构函数，确保连接池被释放"""
        try:
            self.dispose()
        except Exception:
            # 忽略析构函数中的异常
            pass
