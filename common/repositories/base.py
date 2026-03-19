"""Repository 模式基类"""

from typing import TypeVar, Generic, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from common.database import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """
    Repository 基类

    提供通用的数据访问操作
    所有具体的 Repository 应继承此类
    """

    def __init__(self, session: Session, model_class: type[T]):
        """
        初始化 Repository

        Args:
            session: SQLAlchemy 会话
            model_class: 模型类
        """
        self.session = session
        self.model_class = model_class

    def get(self, id: int) -> Optional[T]:
        """根据 ID 获取单个对象"""
        return self.session.get(self.model_class, id)

    def get_by(self, **kwargs) -> Optional[T]:
        """根据条件获取单个对象"""
        stmt = select(self.model_class).filter_by(**kwargs).limit(1)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def list(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        获取对象列表

        Args:
            limit: 限制返回数量
            offset: 跳过数量

        Returns:
            对象列表
        """
        stmt = select(self.model_class)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def filter(self, **kwargs) -> List[T]:
        """根据条件过滤对象列表"""
        stmt = select(self.model_class).filter_by(**kwargs)
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def add(self, obj: T) -> T:
        """添加对象"""
        self.session.add(obj)
        return obj

    def add_all(self, objs: List[T]) -> List[T]:
        """批量添加对象"""
        self.session.add_all(objs)
        return objs

    def update(self, obj: T) -> T:
        """更新对象（自动跟踪）"""
        # SQLAlchemy 会自动跟踪对象变化，无需显式更新
        return obj

    def delete(self, obj: T) -> None:
        """删除对象"""
        self.session.delete(obj)

    def delete_by_id(self, id: int) -> bool:
        """根据 ID 删除对象"""
        obj = self.get(id)
        if obj:
            self.delete(obj)
            return True
        return False

    def count(self) -> int:
        """统计对象数量"""
        stmt = select(self.model_class)
        result = self.session.execute(stmt).scalars().all()
        return len(result)

    def exists(self, **kwargs) -> bool:
        """检查对象是否存在"""
        stmt = select(self.model_class).filter_by(**kwargs).limit(1)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result is not None


class TransactionalRepository(BaseRepository[T]):
    """
    支持事务的 Repository

    在 Repository 层级控制事务
    """

    def __init__(self, session_factory, model_class: type[T]):
        """
        初始化事务型 Repository

        Args:
            session_factory: 会话工厂
            model_class: 模型类
        """
        self.session_factory = session_factory
        self.model_class = model_class

    def __enter__(self):
        """进入上下文，创建会话"""
        self.session = self.session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，提交或回滚"""
        if exc_type is None:
            self.session.commit()
        else:
            self.session.rollback()
        self.session.close()

    def get_session(self):
        """获取当前会话"""
        return self.session
