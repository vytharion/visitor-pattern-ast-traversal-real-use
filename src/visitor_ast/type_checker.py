from __future__ import annotations

from enum import Enum
from typing import Mapping

from visitor_ast.nodes import BinaryOp, Node, NumberLiteral, UnaryOp, VariableRef
from visitor_ast.visitor import Visitor


class Type(Enum):
    """Result of static type inference over an AST node."""

    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"


_NUMERIC: frozenset[Type] = frozenset({Type.INTEGER, Type.NUMBER})
_UNARY_OPS: frozenset[str] = frozenset({"+", "-"})
_BINARY_OPS: frozenset[str] = frozenset({"+", "-", "*", "/"})


class TypeCheckerVisitor(Visitor[Type]):
    """Infer + validate types across an arithmetic AST.

    Two failure modes are surfaced: structural (an operator the language
    does not define) and semantic (an operand whose type does not satisfy
    the operator's signature). Numeric literals are classified as INTEGER
    when their value is integer-valued, NUMBER otherwise. Variable types
    come from a static type environment; references to unbound variables
    raise NameError so the failure mode mirrors the evaluator.
    """

    def __init__(self, environment: Mapping[str, Type] | None = None) -> None:
        self._env: Mapping[str, Type] = environment if environment is not None else {}

    def visit_number_literal(self, node: NumberLiteral) -> Type:
        if float(node.value).is_integer():
            return Type.INTEGER
        return Type.NUMBER

    def visit_variable_ref(self, node: VariableRef) -> Type:
        if node.name not in self._env:
            raise NameError(f"untyped variable: {node.name!r}")
        return self._env[node.name]

    def visit_unary_op(self, node: UnaryOp) -> Type:
        if node.op not in _UNARY_OPS:
            raise TypeError(f"unsupported unary operator: {node.op!r}")
        operand_type = node.operand.accept(self)
        _require_numeric(node.op, "operand", operand_type)
        return operand_type

    def visit_binary_op(self, node: BinaryOp) -> Type:
        if node.op not in _BINARY_OPS:
            raise TypeError(f"unsupported binary operator: {node.op!r}")
        left_type = node.left.accept(self)
        right_type = node.right.accept(self)
        _require_numeric(node.op, "left", left_type)
        _require_numeric(node.op, "right", right_type)
        return _combine(node.op, left_type, right_type)


def _require_numeric(op: str, position: str, t: Type) -> None:
    if t in _NUMERIC:
        return
    raise TypeError(f"{op!r} expects numeric {position}, got {t.value}")


def _combine(op: str, left: Type, right: Type) -> Type:
    # Division always widens to NUMBER because integer-valued operands
    # can still produce a non-integer quotient (e.g. 1 / 2).
    if op == "/":
        return Type.NUMBER
    if left is Type.INTEGER and right is Type.INTEGER:
        return Type.INTEGER
    return Type.NUMBER


def type_check(node: Node, environment: Mapping[str, Type] | None = None) -> Type:
    """Convenience wrapper that constructs a visitor and returns the inferred type."""
    return node.accept(TypeCheckerVisitor(environment))
