from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from visitor_ast.visitor import Visitor

T = TypeVar("T")


class Node(ABC):
    """Abstract base for every AST node.

    Concrete nodes carry data only; the only behaviour they own is
    `accept(visitor)`, which performs the double-dispatch handshake
    that selects the right `visit_*` method on the visitor.
    """

    __slots__ = ()

    @abstractmethod
    def accept(self, visitor: Visitor[T]) -> T: ...


@dataclass(frozen=True)
class NumberLiteral(Node):
    value: float

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_number_literal(self)


@dataclass(frozen=True)
class VariableRef(Node):
    name: str

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_variable_ref(self)


@dataclass(frozen=True)
class UnaryOp(Node):
    op: str
    operand: Node

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_unary_op(self)


@dataclass(frozen=True)
class BinaryOp(Node):
    op: str
    left: Node
    right: Node

    def accept(self, visitor: Visitor[T]) -> T:
        return visitor.visit_binary_op(self)
