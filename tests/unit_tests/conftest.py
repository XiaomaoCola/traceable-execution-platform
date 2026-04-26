"""unit_tests 层的 conftest：mock 掉所有外部依赖，让单元测试无需数据库或网络。

提供的 fixture：
  - mock_db      : 模拟 AsyncSession，支持 execute/add/commit/refresh 调用链
  - mock_audit   : 将 audit_logger.log 替换为 AsyncMock，避免写入真实日志文件

两个 fixture 都不是 autouse，只有显式声明的测试才会用到，
纯函数测试（variable_pool、hashing 等）不受影响。
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_db():
    """模拟 SQLAlchemy AsyncSession。

    使用方式：
        async def test_something(mock_db):
            mock_db.execute.return_value.scalar_one_or_none.return_value = some_model
            result = await my_service.do_something(mock_db, ...)
    """
    session = AsyncMock()
    # 模拟异步数据库对象。

    # execute() 返回一个普通 MagicMock，让调用方可以链式调用
    # .scalar_one_or_none() / .scalar_one() / .scalars().all() 等
    execute_result = MagicMock()
    # 创建假的“查询结果对象”

    session.execute.return_value = execute_result

    execute_result.scalar_one_or_none.return_value = None
    execute_result.scalar_one.return_value = None
    execute_result.scalars.return_value.all.return_value = []

    session.add = MagicMock()
    # 对应真实代码 db.add(obj) ，把一个 ORM 对象加入 session。   add() 不是 async 的，不需要 await ， 所以用 MagicMock()。
    session.commit = AsyncMock()
    # 对应真实代码 await db.commit() ， 提交事务，真正写入数据库。
    session.refresh = AsyncMock()
    session.delete = MagicMock()

    return session


@pytest.fixture
def mock_audit():
    """将 audit_logger.log 替换为 AsyncMock，防止单元测试写入真实审计日志。

    使用方式：
        async def test_login(mock_db, mock_audit):
            await auth_service.authenticate_user(mock_db, "user", "wrong_pass")
            mock_audit.assert_awaited_once()
    """
    import backend.app.audit.audit_logger as _module
    mock_log = AsyncMock()
    mock_logger = MagicMock()
    mock_logger.log = mock_log
    _module._audit_logger = mock_logger
    yield mock_log
    _module._audit_logger = None
