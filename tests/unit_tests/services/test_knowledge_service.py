"""knowledge_service 的单元测试。

【什么是单元测试？】
单元测试就是：针对一个具体函数，给它各种输入，验证输出是否符合预期。
不需要数据库、不需要网络、不需要 Docker，直接在本地跑。

运行方式：
  pytest tests/                      # 跑所有测试
  pytest tests/unit_tests/services/test_knowledge_service.py -v   # 跑这个文件，-v 显示每条测试的名字

【为什么要测 _chunk_text 和 _extract_text？】
这两个函数是知识库功能的核心入口：
  - _extract_text：把上传的文件变成纯文本
  - _chunk_text：把长文本切成小片，直接影响向量检索的质量

如果这两个函数出 bug，所有上传的文档都会被错误处理，
但因为处理是异步后台进行的，你在界面上很难发现，测试能帮你提前发现。
"""

import pytest

# 直接从模块里把两个私有函数拿出来测。
# 以下划线开头（_chunk_text）只是"建议不要在模块外用"的约定，并不是真的禁止访问。
from backend.app.services.knowledge_service import _chunk_text, _extract_text, CHUNK_SIZE


# ── _extract_text 测试 ─────────────────────────────────────────────────────


class TestExtractText:
    """测试文本提取函数。"""

    def test_txt_正常提取(self):
        """最基本的情况：给一段 UTF-8 文本，应该原样返回。"""
        content = "你好，这是一段测试文本。".encode("utf-8")
        result = _extract_text("文件.txt", content)
        assert result == "你好，这是一段测试文本。"

    def test_txt_空文件(self):
        """空文件应该返回空字符串，不能崩溃。"""
        result = _extract_text("empty.txt", b"")
        assert result == ""

    def test_md_和_txt_一样处理(self):
        """.md 文件也按纯文本处理。"""
        content = "# 标题\n\n正文内容".encode("utf-8")
        result = _extract_text("readme.md", content)
        assert "标题" in result
        assert "正文内容" in result

    def test_txt_损坏编码不崩溃(self):
        """文件里有乱码字节时，应该跳过而不是抛异常（errors='ignore'）。"""
        broken = b"\xff\xfe" + "正常文字".encode("utf-8")
        result = _extract_text("broken.txt", broken)
        # 不崩溃就算通过，正常文字部分应该还在
        assert isinstance(result, str)

    def test_pdf_未安装pypdf时给出友好报错(self, monkeypatch):
        """模拟 pypdf 没装的情况，应该抛出带说明的 RuntimeError，而不是 ImportError。

        monkeypatch 是 pytest 内置的工具，可以临时替换某个东西，测完自动还原。
        这里用它来模拟"import pypdf 失败"的场景。
        """
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pypdf":
                raise ImportError("no module named pypdf")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        with pytest.raises(RuntimeError, match="pypdf 未安装"):
            _extract_text("文件.pdf", b"%PDF-1.4 fake content")


# ── _chunk_text 测试 ───────────────────────────────────────────────────────


class TestChunkText:
    """测试文本切片函数。"""

    def test_短文本不切片(self):
        """文本总长度小于 CHUNK_SIZE，应该只返回一个 chunk。"""
        text = "这是一段很短的文字。"
        result = _chunk_text(text)
        assert len(result) == 1
        assert result[0] == text

    def test_空文本返回空列表(self):
        """空文本不能返回乱七八糟的东西，应该是空列表。"""
        result = _chunk_text("")
        assert result == []

    def test_纯空白返回空列表(self):
        """全是空格换行的文本也应该是空列表。"""
        result = _chunk_text("   \n\n   \n\n   ")
        assert result == []

    def test_每个chunk不超过最大长度(self):
        """任何情况下，每个切片的长度都不能超过 CHUNK_SIZE 的两倍。
        （有重叠所以可能略超，但不能无限制地大）
        """
        # 造一段很长的文本，没有段落分隔
        long_text = "字" * 3000
        result = _chunk_text(long_text)
        for chunk in result:
            assert len(chunk) <= CHUNK_SIZE * 2, f"chunk 太长了：{len(chunk)} 字"

    def test_按段落切分(self):
        """有多个段落时，应该切成多个 chunk，不能全挤在一起。"""
        # 造 10 个段落，每个 100 字，总长 1000 字，超过一个 chunk
        paragraphs = ["第{}段：".format(i) + "内容" * 40 for i in range(10)]
        text = "\n\n".join(paragraphs)
        result = _chunk_text(text)
        assert len(result) > 1, "长文本应该被切成多个 chunk"

    def test_切片结果不包含空字符串(self):
        """切片结果里不能有空字符串或纯空白的 chunk。"""
        text = "段落一\n\n\n\n段落二\n\n\n\n段落三"
        result = _chunk_text(text)
        for chunk in result:
            assert chunk.strip() != "", f"发现空 chunk：{repr(chunk)}"

    def test_所有内容都被保留(self):
        """切完之后，原始文本里的关键词应该还能在某个 chunk 里找到。

        这个测试验证切片没有把内容搞丢。
        """
        text = "关键词甲很重要\n\n关键词乙也很重要\n\n" + "填充内容。" * 200
        result = _chunk_text(text)
        all_text = " ".join(result)
        assert "关键词甲" in all_text, "关键词甲被切丢了"
        assert "关键词乙" in all_text, "关键词乙被切丢了"
