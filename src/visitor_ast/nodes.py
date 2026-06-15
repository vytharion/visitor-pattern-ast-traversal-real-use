from __future__ import annotations

from abc import ABC
from dataclasses import dataclass


class Node(ABC):
    """Abstract base for every AST node.

    Concrete nodes are intentionally behavior-free: they carry data only.
    The `accept(visitor)` dispatch method arrives in step 2; declaring it
    here would force a circular dependency on the Visitor interface before
    that interface exists, so we keep step 1 strictly about shape.
    """

    __slots__ = ()


@dataclass(frozen=True)
class NumberLiteral(Node):
    value: float


@dataclass(frozen=True)
class VariableRef(Node):
    name: str


@dataclass(frozen=True)
class UnaryOp(Node):
    op: str
    operand: Node


@dataclass(frozen=True)
class BinaryOp(Node):
    op: str
    left: Node
    right: Node
