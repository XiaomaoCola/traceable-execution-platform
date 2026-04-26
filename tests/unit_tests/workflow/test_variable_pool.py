"""workflow/variable_pool.py 的单元测试。

VariablePool 是 workflow 引擎的核心数据结构，节点之间所有数据都通过它传递。
测试覆盖：add / get / remove / resolve_template / system_variables / snapshot。
"""

import pytest

from backend.app.workflow.variable import StringVariable
from backend.app.workflow.variable_pool import VariablePool


# ── add / get ─────────────────────────────────────────────────────────────


class TestAddAndGet:
    def test_写入后能读取(self):
        pool = VariablePool()
        pool.add(["node1", "output"], "hello")
        var = pool.get(["node1", "output"])
        assert var is not None
        assert var.value == "hello"

    def test_get_value直接返回原始值(self):
        pool = VariablePool()
        pool.add(["node1", "count"], 42)
        assert pool.get_value(["node1", "count"]) == 42

    def test_覆盖写入(self):
        pool = VariablePool()
        pool.add(["node1", "x"], "first")
        pool.add(["node1", "x"], "second")
        assert pool.get_value(["node1", "x"]) == "second"

    def test_传入Variable实例直接存储(self):
        pool = VariablePool()
        var = StringVariable(name="x", value="direct")
        pool.add(["node1", "x"], var)
        assert pool.get_value(["node1", "x"]) == "direct"

    def test_不存在的变量返回None(self):
        pool = VariablePool()
        assert pool.get(["missing", "var"]) is None

    def test_get_value不存在返回None(self):
        pool = VariablePool()
        assert pool.get_value(["missing", "var"]) is None

    def test_不同节点的同名变量互不干扰(self):
        pool = VariablePool()
        pool.add(["node1", "x"], "from_node1")
        pool.add(["node2", "x"], "from_node2")
        assert pool.get_value(["node1", "x"]) == "from_node1"
        assert pool.get_value(["node2", "x"]) == "from_node2"

    def test_selector长度不对时抛ValueError(self):
        pool = VariablePool()
        with pytest.raises(ValueError):
            pool.add(["only_one_segment"], "value")
        with pytest.raises(ValueError):
            pool.add(["a", "b", "c"], "value")


# ── remove ────────────────────────────────────────────────────────────────


class TestRemove:
    def test_删除单个变量(self):
        pool = VariablePool()
        pool.add(["node1", "x"], 1)
        pool.remove(["node1", "x"])
        assert pool.get(["node1", "x"]) is None

    def test_删除后同节点其他变量不受影响(self):
        pool = VariablePool()
        pool.add(["node1", "x"], 1)
        pool.add(["node1", "y"], 2)
        pool.remove(["node1", "x"])
        assert pool.get_value(["node1", "y"]) == 2

    def test_删除整个节点命名空间(self):
        pool = VariablePool()
        pool.add(["node1", "x"], 1)
        pool.add(["node1", "y"], 2)
        pool.remove(["node1"])
        assert pool.get(["node1", "x"]) is None
        assert pool.get(["node1", "y"]) is None

    def test_删除不存在的变量不报错(self):
        pool = VariablePool()
        pool.remove(["ghost", "var"])  # 不抛异常即通过

    def test_空selector不操作(self):
        pool = VariablePool()
        pool.add(["node1", "x"], 1)
        pool.remove([])
        assert pool.get_value(["node1", "x"]) == 1


# ── resolve_template ──────────────────────────────────────────────────────


class TestResolveTemplate:
    def test_替换已知变量(self):
        pool = VariablePool()
        pool.add(["node1", "name"], "world")
        result = pool.resolve_template("Hello, {{node1.name}}!")
        assert result == "Hello, world!"

    def test_未知引用原样保留(self):
        pool = VariablePool()
        result = pool.resolve_template("{{missing.var}}")
        assert result == "{{missing.var}}"

    def test_多个占位符同时替换(self):
        pool = VariablePool()
        pool.add(["a", "x"], "foo")
        pool.add(["b", "y"], "bar")
        result = pool.resolve_template("{{a.x}} and {{b.y}}")
        assert result == "foo and bar"

    def test_无占位符原样返回(self):
        pool = VariablePool()
        result = pool.resolve_template("plain text, no templates")
        assert result == "plain text, no templates"

    def test_整数变量插值(self):
        pool = VariablePool()
        pool.add(["node1", "count"], 99)
        result = pool.resolve_template("total: {{node1.count}}")
        assert result == "total: 99"

    def test_空模板字符串(self):
        pool = VariablePool()
        assert pool.resolve_template("") == ""

    def test_同一占位符出现两次(self):
        pool = VariablePool()
        pool.add(["n", "v"], "X")
        result = pool.resolve_template("{{n.v}} and {{n.v}}")
        assert result == "X and X"


# ── system_variables ──────────────────────────────────────────────────────


class TestSystemVariables:
    def test_构造时传入系统变量可读取(self):
        pool = VariablePool(system_variables={"run_id": "abc-123"})
        assert pool.get_value(["sys", "run_id"]) == "abc-123"

    def test_多个系统变量(self):
        pool = VariablePool(system_variables={"run_id": "r1", "user_id": "u1"})
        assert pool.get_value(["sys", "run_id"]) == "r1"
        assert pool.get_value(["sys", "user_id"]) == "u1"

    def test_系统变量存在sys命名空间(self):
        pool = VariablePool(system_variables={"k": "v"})
        var = pool.get(["sys", "k"])
        assert var is not None

    def test_不传system_variables时sys命名空间为空(self):
        pool = VariablePool()
        assert pool.get(["sys", "anything"]) is None


# ── user_inputs ───────────────────────────────────────────────────────────


class TestUserInputs:
    def test_user_inputs可访问(self):
        pool = VariablePool(user_inputs={"query": "what is AI?"})
        assert pool.user_inputs["query"] == "what is AI?"

    def test_不传user_inputs时为空字典(self):
        pool = VariablePool()
        assert pool.user_inputs == {}


# ── snapshot ──────────────────────────────────────────────────────────────


class TestSnapshot:
    def test_快照包含所有节点和变量(self):
        pool = VariablePool()
        pool.add(["node1", "x"], "hello")
        pool.add(["node1", "y"], 42)
        pool.add(["node2", "z"], True)
        snap = pool.snapshot()
        assert snap["node1"]["x"] == "hello"
        assert snap["node1"]["y"] == 42
        assert snap["node2"]["z"] is True

    def test_空pool快照为空字典(self):
        pool = VariablePool()
        assert pool.snapshot() == {}

    def test_快照是值的副本不影响pool(self):
        pool = VariablePool()
        pool.add(["node1", "x"], "original")
        snap = pool.snapshot()
        snap["node1"]["x"] = "modified"
        # pool 内的值不受 snap 修改影响
        assert pool.get_value(["node1", "x"]) == "original"
