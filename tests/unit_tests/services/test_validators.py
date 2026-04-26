"""services/validators.py 的单元测试。

FileHashValidator 和 ConfigFormatValidator 都是纯异步方法，
不依赖数据库或外部服务，直接实例化调用即可，无需 mock_db / mock_audit。

返回结构：{ valid: bool, errors: list, warnings: list, report: dict }
"""

import json

import pytest

from backend.app.services.validators import ConfigFormatValidator, FileHashValidator


# ── FileHashValidator ──────────────────────────────────────────────────────


class TestFileHashValidator:
    @pytest.fixture
    def validator(self):
        return FileHashValidator()

    async def test_哈希匹配时valid为True(self, validator):
        import hashlib

        data = b"artifact content"
        expected = hashlib.sha256(data).hexdigest()

        result = await validator.validate(data, {"expected_hash": expected})

        assert result["valid"] is True
        assert result["errors"] == []

    async def test_哈希不匹配时valid为False(self, validator):
        result = await validator.validate(b"content", {"expected_hash": "wrong" * 16})

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "mismatch" in result["errors"][0].lower()

    async def test_没有expected_hash时默认valid为True(self, validator):
        # metadata 里没有 expected_hash → 跳过校验
        result = await validator.validate(b"anything", {})

        assert result["valid"] is True
        assert result["errors"] == []

    async def test_report包含computed_hash和file_size(self, validator):
        data = b"hello"
        result = await validator.validate(data, {})

        assert "computed_hash" in result["report"]
        assert result["report"]["file_size"] == 5
        assert len(result["report"]["computed_hash"]) == 64

    async def test_空文件也能校验(self, validator):
        import hashlib

        data = b""
        expected = hashlib.sha256(data).hexdigest()
        result = await validator.validate(data, {"expected_hash": expected})

        assert result["valid"] is True


# ── ConfigFormatValidator ──────────────────────────────────────────────────


class TestConfigFormatValidator:
    @pytest.fixture
    def validator(self):
        return ConfigFormatValidator()

    # ── JSON ──────────────────────────────────────────────────────────────

    async def test_有效json文件valid为True(self, validator):
        data = json.dumps({"key": "value", "num": 42}).encode()
        result = await validator.validate(data, {"filename": "config.json"})

        assert result["valid"] is True
        assert result["errors"] == []
        assert result["report"]["format"] == "json"

    async def test_json报告包含顶层keys(self, validator):
        data = json.dumps({"a": 1, "b": 2}).encode()
        result = await validator.validate(data, {"filename": "config.json"})

        assert set(result["report"]["keys"]) == {"a", "b"}

    async def test_无效json文件valid为False(self, validator):
        result = await validator.validate(b"not json {{{", {"filename": "bad.json"})

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "JSON" in result["errors"][0]

    async def test_空json对象有效(self, validator):
        result = await validator.validate(b"{}", {"filename": "empty.json"})

        assert result["valid"] is True

    # ── YAML ──────────────────────────────────────────────────────────────

    async def test_有效yaml文件valid为True(self, validator):
        data = b"key: value\nnum: 42\n"
        result = await validator.validate(data, {"filename": "config.yaml"})

        assert result["valid"] is True
        assert result["report"]["format"] == "yaml"

    async def test_yml扩展名也被识别(self, validator):
        data = b"a: 1\n"
        result = await validator.validate(data, {"filename": "config.yml"})

        assert result["valid"] is True
        assert result["report"]["format"] == "yaml"

    async def test_无效yaml文件valid为False(self, validator):
        result = await validator.validate(b"key: [unclosed", {"filename": "bad.yaml"})

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "YAML" in result["errors"][0]

    # ── INI ───────────────────────────────────────────────────────────────

    async def test_有效ini文件valid为True(self, validator):
        data = b"[section]\nkey = value\n"
        result = await validator.validate(data, {"filename": "config.ini"})

        assert result["valid"] is True
        assert result["report"]["format"] == "ini"
        assert "section" in result["report"]["sections"]

    # ── 未知格式 ──────────────────────────────────────────────────────────

    async def test_未知扩展名给出warning不报错(self, validator):
        result = await validator.validate(b"anything", {"filename": "config.toml"})

        assert result["valid"] is True  # 没有解析错误
        assert len(result["warnings"]) == 1
        assert result["report"]["format"] == "unknown"

    async def test_没有filename时也给出warning(self, validator):
        result = await validator.validate(b"data", {})

        assert result["valid"] is True
        assert len(result["warnings"]) == 1
