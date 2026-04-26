"""utils/hashing.py 的单元测试。

compute_sha256 / verify_sha256 是文件完整性校验的基础工具，
属于纯函数，没有外部依赖，最适合做单元测试。
"""

import hashlib
import io

import pytest

from backend.app.utils.hashing import compute_sha256, verify_sha256


def _sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class TestComputeSha256:
    def test_结果与hashlib一致(self):
        data = b"hello world"
        assert compute_sha256(io.BytesIO(data)) == _sha256_of(data)

    def test_结果是64位十六进制字符串(self):
        result = compute_sha256(io.BytesIO(b"any data"))
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_相同内容结果相同(self):
        data = b"deterministic"
        h1 = compute_sha256(io.BytesIO(data))
        h2 = compute_sha256(io.BytesIO(data))
        assert h1 == h2

    def test_不同内容结果不同(self):
        h1 = compute_sha256(io.BytesIO(b"content_a"))
        h2 = compute_sha256(io.BytesIO(b"content_b"))
        assert h1 != h2

    def test_空文件有固定哈希(self):
        result = compute_sha256(io.BytesIO(b""))
        # sha256("") 是固定值，用 hashlib 验证而不是硬编码
        assert result == _sha256_of(b"")

    def test_大文件分块读取结果正确(self):
        # 20KB 数据，触发函数内的 while 循环多次迭代（chunk=8192）
        data = b"x" * 20_000
        result = compute_sha256(io.BytesIO(data))
        assert result == _sha256_of(data)

    def test_读取后文件指针在末尾(self):
        f = io.BytesIO(b"data")
        compute_sha256(f)
        assert f.tell() == 4  # 4 字节全部读完


class TestVerifySha256:
    def test_哈希匹配返回True(self):
        data = b"hello"
        correct_hash = _sha256_of(data)
        assert verify_sha256(io.BytesIO(data), correct_hash) is True

    def test_哈希不匹配返回False(self):
        data = b"hello"
        assert verify_sha256(io.BytesIO(data), "a" * 64) is False

    def test_大小写不敏感(self):
        data = b"hello"
        upper_hash = _sha256_of(data).upper()
        assert verify_sha256(io.BytesIO(data), upper_hash) is True

    def test_混合大小写(self):
        data = b"hello"
        mixed = _sha256_of(data)
        mixed = mixed[:32].upper() + mixed[32:]
        assert verify_sha256(io.BytesIO(data), mixed) is True

    def test_空文件验证(self):
        data = b""
        assert verify_sha256(io.BytesIO(data), _sha256_of(data)) is True
