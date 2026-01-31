"""
SQLAlchemy declarative base and common model mixins.

例子：class Ticket(Base, IDMixin, TimestampMixin)
这种就是class X(Base, A, B, C)这种形式，
表达的意思就是“这张表 = 基础表能力 + A 功能 + B 功能 + C 功能”，
在上面这个例子种就是主键id和时间戳的列被添加进去了。
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declarative_base


# Declarative base for all models
Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    # DateTime意思是：这一列的数据类型（时间）。
    # default意思是：如果不填，系统自动写进去值。
    # default=lambda: datetime.now(timezone.utc)，其中lambda是“不用起名字的一次性小函数”。
    # 不能写成 default=datetime.now(timezone.utc) ， 否则模块加载那一瞬间，就把时间算死了，以后创建 100 条数据全是同一时间。
    # nullable=False意思是：不允许为空。


class IDMixin:
    """
    Mixin for integer primary key.
    主键（Primary Key）就是：每一行数据的“身份证号码”。
    """

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Column(...)：声明“这是表的一列”。
    # Integer：这一列是整数。
    # primary_key=True：这一列是主键。
    # index=True：给这列建索引（让按 id 查更快）
    # index 是用在“表里的某一列”上的，如果这一列有 index，数据库就可以通过这一列，快速定位到某一行（或几行）。
    # autoincrement=True：自动递增（数据库自己填 1、2、3…）。
    # 总体来看：任何继承了 IDMixin 的表，都会自动拥有一列 id（整数、唯一、查询很快、自动增长）。
