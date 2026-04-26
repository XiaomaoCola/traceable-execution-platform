"""workflow/variable.py 的单元测试。

测试重点：
  - build_variable() 工厂根据 Python 原生类型正确路由到子类
  - bool 在 int 之前判断（bool 是 int 的子类，顺序错了会路由错）
  - Variable.text property 在各类型下的字符串化行为
"""

from backend.app.workflow.variable import (
    ArrayVariable,
    BooleanVariable,
    FloatVariable,
    IntegerVariable,
    NoneVariable,
    ObjectVariable,
    StringVariable,
    build_variable,
)
from backend.app.workflow.types import SegmentType


class TestBuildVariable:
    """build_variable() 工厂函数：根据原生值自动选择正确的 Variable 子类。"""

    def test_字符串(self):
        var = build_variable(["node1", "x"], "hello")
        assert isinstance(var, StringVariable)
        assert var.value == "hello"
        assert var.value_type == SegmentType.STRING

    def test_整数(self):
        var = build_variable(["node1", "x"], 42)
        assert isinstance(var, IntegerVariable)
        assert var.value == 42

    def test_浮点数(self):
        var = build_variable(["node1", "x"], 3.14)
        assert isinstance(var, FloatVariable)
        assert var.value == 3.14

    def test_bool必须在int之前判断(self):
        # bool 是 int 的子类：isinstance(True, int) == True
        # build_variable 内部必须先判断 bool，否则 True 会被识别为 IntegerVariable(value=1)
        var = build_variable(["node1", "x"], True)
        assert isinstance(var, BooleanVariable), "True 应路由到 BooleanVariable，不是 IntegerVariable"
        assert var.value is True

        var_false = build_variable(["node1", "x"], False)
        assert isinstance(var_false, BooleanVariable)
        assert var_false.value is False

    def test_None(self):
        var = build_variable(["node1", "x"], None)
        assert isinstance(var, NoneVariable)
        assert var.value is None

    def test_字典(self):
        var = build_variable(["node1", "x"], {"key": "val"})
        assert isinstance(var, ObjectVariable)
        assert var.value == {"key": "val"}

    def test_列表(self):
        var = build_variable(["node1", "x"], [1, 2, 3])
        assert isinstance(var, ArrayVariable)
        assert var.value == [1, 2, 3]

    def test_未知类型兜底为字符串(self):
        class Custom:
            def __str__(self):
                return "custom_repr"

        var = build_variable(["node1", "x"], Custom())
        assert isinstance(var, StringVariable)
        assert var.value == "custom_repr"

    def test_selector写入name和selector字段(self):
        var = build_variable(["my_node", "result"], "ok")
        assert var.name == "result"
        assert var.selector == ["my_node", "result"]


class TestVariableTextProperty:
    """Variable.text property：用于模板插值时的字符串化。"""

    def test_字符串直接返回(self):
        var = StringVariable(name="x", value="hello")
        assert var.text == "hello"

    def test_整数转字符串(self):
        var = IntegerVariable(name="x", value=42)
        assert var.text == "42"

    def test_浮点数转字符串(self):
        var = FloatVariable(name="x", value=1.5)
        assert var.text == "1.5"

    def test_布尔值转字符串(self):
        var = BooleanVariable(name="x", value=True)
        assert var.text == "True"

    def test_None返回空字符串(self):
        var = NoneVariable(name="x")
        assert var.text == ""

    def test_字典转字符串(self):
        var = ObjectVariable(name="x", value={"a": 1})
        assert var.text == "{'a': 1}"

    def test_空字符串(self):
        var = StringVariable(name="x", value="")
        assert var.text == ""


class TestVariableIdentity:
    """Variable 的 id 字段：每次创建应该是唯一的 UUID。"""

    def test_两个变量id不同(self):
        v1 = StringVariable(name="x", value="a")
        v2 = StringVariable(name="x", value="a")
        assert v1.id != v2.id

    def test_id是字符串(self):
        var = StringVariable(name="x", value="a")
        assert isinstance(var.id, str)
        assert len(var.id) == 36  # UUID4 标准格式
