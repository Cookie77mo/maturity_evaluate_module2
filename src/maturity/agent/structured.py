"""研判结果的强类型 schema。

为什么不再让模型"自由输出 JSON"：

  手写 ``json.loads`` 只能发现"不是 JSON"，发现不了"字段缺失 / 类型不对"。
  把 schema 交给 LangChain 的 ``with_structured_output`` 后，端点会按 schema
  约束输出；不支持的端点则由 ``call_structured`` 退化为 JSON + Pydantic 校验，
  两种情况拿到的都是同一份 :class:`JudgeResponse`。

  校验通过不代表结论可信 —— 节点/边是否真实存在仍由 ``CitationValidator``
  在纯代码里判定，schema 只负责"形状"。
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EdgeRef(BaseModel):
    """一条被引用的边。"""

    source: str = Field(description="边的起点节点 id")
    target: str = Field(description="边的终点节点 id")
    relation: str = Field(default="", description="关系类型，如 CALLS / DEPENDS_ON")


class Finding(BaseModel):
    """一条语义研判结论。"""

    statement: str = Field(default="", description="一句话说明问题，避免泛泛而谈")
    node_ids: list[str] = Field(
        default_factory=list,
        description="支持该结论的节点 id，必须来自上下文中真实出现过的节点",
    )
    edges: list[EdgeRef] = Field(
        default_factory=list,
        description="支持该结论的边，必须来自上下文中真实出现过的边",
    )
    confidence: float = Field(default=0.7, description="0 到 1 之间的置信度")


class ToolCall(BaseModel):
    """模型请求执行的一次只读查询。"""

    name: str = Field(description="工具名，必须是可用工具列表中的名字")
    args: dict[str, Any] = Field(default_factory=dict, description="工具参数")


class JudgeResponse(BaseModel):
    """单轮研判的完整输出：要么继续查工具，要么给出结论。"""

    tool_calls: list[ToolCall] = Field(
        default_factory=list,
        description="需要更多信息时填写；与 findings 二选一，两者不要同时非空",
    )
    findings: list[Finding] = Field(
        default_factory=list,
        description="给出结论时填写；证据不足时保持为空",
    )
