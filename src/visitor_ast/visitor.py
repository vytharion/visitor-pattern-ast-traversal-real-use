from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from visitor_ast.nodes import BinaryOp, NumberLiteral, UnaryOp, VariableRef

T = TypeVar("T")


class Visitor(ABC, Generic[T]):
    """Double-dispatch target for AST traversal.

    Each concrete node calls back into exactly one `visit_*` method,
    parameterised by the result type `T`. New operations over the tree
    are added by writing a new Visitor subclass — the node classes
    stay closed for modification.
    """

    @abstractmethod
    def visit_number_literal(self, node: NumberLiteral) -> T: ...

    @abstractmethod
    def visit_variable_ref(self, node: VariableRef) -> T: ...

    @abstractmethod
    def visit_unary_op(self, node: UnaryOp) -> T: ...

    @abstractmethod
    def visit_binary_op(self, node: BinaryOp) -> T: ...
