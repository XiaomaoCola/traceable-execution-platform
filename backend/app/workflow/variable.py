from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .types import Selector, SegmentType

# Dify 将 Segment 和 Variable 分成两个独立的类层级：
#   Segment（有 value_type + value，负责值的存储和序列化）
#   VariableBase(Segment)（加上 id / name / selector，负责变量身份）
#   Variable = VariableBase + Segment 的 discriminated union（用于 Pydantic 序列化）
#
# 这种分离的好处是 Segment 可以脱离 Variable 独立使用（比如模板解析时的临时片段）。
# 我们把两者合并成单一的 Variable 类，直接带 id / name / selector，
# 去掉 SegmentGroup（Dify 用来拼接模板片段，我们 resolve_template 直接返回 str）。
# 类型安全通过子类 + build_variable() 工厂保证，不需要 discriminated union。


class Variable(BaseModel):
    """所有变量的基类，对应 Dify 的 VariableBase + Segment 合并体。"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    value_type: SegmentType
    value: Any
    selector: list[str] = Field(default_factory=list)
    description: str = ""

    @property
    def text(self) -> str:
        """用于模板插值的字符串表示。Dify 在 Segment 上同样有 text property。"""
        if self.value is None:
            return ""
        return str(self.value)


class StringVariable(Variable):
    value_type: SegmentType = SegmentType.STRING
    value: str = ""


class IntegerVariable(Variable):
    value_type: SegmentType = SegmentType.INTEGER
    value: int = 0


class FloatVariable(Variable):
    value_type: SegmentType = SegmentType.FLOAT
    value: float = 0.0


class BooleanVariable(Variable):
    value_type: SegmentType = SegmentType.BOOLEAN
    value: bool = False


class ObjectVariable(Variable):
    value_type: SegmentType = SegmentType.OBJECT
    value: dict[str, Any] = Field(default_factory=dict)


class ArrayVariable(Variable):
    value_type: SegmentType = SegmentType.ARRAY
    value: list[Any] = Field(default_factory=list)


class NoneVariable(Variable):
    value_type: SegmentType = SegmentType.NONE
    value: None = None


def build_variable(selector: Selector, value: Any) -> Variable:
    """根据 Python 原生类型自动构造对应的 Variable 子类。

    Dify 把这个逻辑拆进了独立的 variable_factory 模块（segment_to_variable + build_segment），
    并且通过 discriminated union 支持 Pydantic 的自动反序列化。
    我们内联在这里，逻辑等价，不需要额外的工厂模块。
    """
    var_name = selector[1]
    base = {"name": var_name, "selector": list(selector)}

    if value is None:
        return NoneVariable(**base)
    if isinstance(value, bool):
        # bool 必须在 int 之前判断，因为 bool 是 int 的子类
        return BooleanVariable(**base, value=value)
    if isinstance(value, int):
        return IntegerVariable(**base, value=value)
    if isinstance(value, float):
        return FloatVariable(**base, value=value)
    if isinstance(value, str):
        return StringVariable(**base, value=value)
    if isinstance(value, dict):
        return ObjectVariable(**base, value=value)
    if isinstance(value, list):
        return ArrayVariable(**base, value=value)

    # 兜底：转成字符串，Dify 遇到未知类型也会尽量 fallback 而不是抛异常
    return StringVariable(**base, value=str(value))
