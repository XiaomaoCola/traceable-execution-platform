"""auth_service.py 的单元测试。

测试两个函数：
  - authenticate_user：用户名+密码登录，覆盖用户不存在/密码错/未激活/正常四条路径
  - create_user：注册新用户，覆盖用户名重复/邮箱重复/正常创建三条路径

外部依赖全部 mock：
  - mock_db  (AsyncSession)      —— 来自 unit_tests/conftest.py
  - mock_audit (audit_logger.log) —— 来自 unit_tests/conftest.py
  - verify_password              —— 用 patch 控制密码校验结果
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.app.schemas.user import UserCreate
from backend.app.services import auth_service


def _make_user(*, is_active=True, is_admin=False):
    """构造一个 mock User 对象，避免每个测试都重复写同样的属性。"""
    user = MagicMock()
    user.id = 1
    user.username = "alice"
    user.email = "alice@example.com"
    user.hashed_password = "hashed_pw"
    user.is_active = is_active
    user.is_admin = is_admin
    return user


# ── authenticate_user ─────────────────────────────────────────────────────


class TestAuthenticateUser:
    async def test_用户不存在返回None(self, mock_db, mock_audit):
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = await auth_service.authenticate_user(mock_db, "ghost", "any")

        assert result is None
        mock_audit.assert_awaited_once()

    async def test_密码错误返回None(self, mock_db, mock_audit):
        mock_db.execute.return_value.scalar_one_or_none.return_value = _make_user()

        with patch("backend.app.services.auth_service.verify_password", return_value=False):
            result = await auth_service.authenticate_user(mock_db, "alice", "wrong")

        assert result is None
        mock_audit.assert_awaited_once()

    async def test_用户未激活返回None(self, mock_db, mock_audit):
        mock_db.execute.return_value.scalar_one_or_none.return_value = _make_user(is_active=False)

        with patch("backend.app.services.auth_service.verify_password", return_value=True):
            result = await auth_service.authenticate_user(mock_db, "alice", "correct")

        assert result is None
        mock_audit.assert_awaited_once()

    async def test_认证成功返回用户对象(self, mock_db, mock_audit):
        user = _make_user()
        mock_db.execute.return_value.scalar_one_or_none.return_value = user

        with patch("backend.app.services.auth_service.verify_password", return_value=True):
            result = await auth_service.authenticate_user(mock_db, "alice", "correct")

        assert result is user
        mock_audit.assert_awaited_once()

    async def test_失败时审计日志包含用户名(self, mock_db, mock_audit):
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        await auth_service.authenticate_user(mock_db, "target_user", "pw")

        call_args = mock_audit.call_args[0][0]  # 第一个位置参数是 AuditEvent
        assert call_args.actor_username == "target_user"
        assert call_args.success is False


# ── create_user ───────────────────────────────────────────────────────────


class TestCreateUser:
    def _user_create(self, username="bob", email="bob@example.com"):
        return UserCreate(username=username, email=email, password="secret123")

    async def test_用户名已存在抛400(self, mock_db, mock_audit):
        # 第一次 execute（查用户名）返回已有用户
        mock_db.execute.return_value.scalar_one_or_none.return_value = _make_user()

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.create_user(mock_db, self._user_create())

        assert exc_info.value.status_code == 400
        assert "Username" in exc_info.value.detail

    async def test_邮箱已存在抛400(self, mock_db, mock_audit):
        # 第一次 execute（查用户名）→ None，第二次 execute（查邮箱）→ 已有用户
        results = [MagicMock(), MagicMock()]
        results[0].scalar_one_or_none.return_value = None   # 用户名不重复
        results[1].scalar_one_or_none.return_value = _make_user()  # 邮箱重复
        mock_db.execute.side_effect = results

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.create_user(mock_db, self._user_create())

        assert exc_info.value.status_code == 400
        assert "Email" in exc_info.value.detail

    async def test_正常创建返回用户对象(self, mock_db, mock_audit):
        # 两次查重都返回 None → 可以创建
        no_conflict = MagicMock()
        no_conflict.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = no_conflict

        with patch("backend.app.services.auth_service.get_password_hash", return_value="hashed"):
            await auth_service.create_user(mock_db, self._user_create())

        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()
        mock_audit.assert_awaited_once()
        # result 是实际写入 db 的 User 对象（由 db.add 接收的那个）
        actual_user = mock_db.add.call_args[0][0]
        assert actual_user.username == "bob"
        assert actual_user.hashed_password == "hashed"

    async def test_创建时密码被哈希不存原文(self, mock_db, mock_audit):
        no_conflict = MagicMock()
        no_conflict.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = no_conflict

        with patch(
            "backend.app.services.auth_service.get_password_hash", return_value="hashed_pw"
        ) as mock_hash:
            await auth_service.create_user(mock_db, self._user_create(username="carol"))

        mock_hash.assert_called_once_with("secret123")
        actual_user = mock_db.add.call_args[0][0]
        assert actual_user.hashed_password == "hashed_pw"
        assert not hasattr(actual_user, "password") or actual_user.hashed_password != "secret123"

    async def test_创建时记录审计日志(self, mock_db, mock_audit):
        no_conflict = MagicMock()
        no_conflict.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = no_conflict

        creator = _make_user()
        with patch("backend.app.services.auth_service.get_password_hash", return_value="h"):
            await auth_service.create_user(mock_db, self._user_create(), creator=creator)

        mock_audit.assert_awaited_once()
        event = mock_audit.call_args[0][0]
        assert event.actor_username == creator.username
