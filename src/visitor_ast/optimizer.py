from __future__ import annotations

from typing import Callable

from visitor_ast.nodes import BinaryOp, Node, NumberLiteral, UnaryOp, VariableRef
from visitor_ast.visitor import Visitor

# Constant-fold tables mirror the evaluator's: a single dict lookup keeps the
# per-operator branch out of the visit methods and below the nesting cap.
_UNARY_FOLD: dict[str, Callable[[float], float]] = {
    "+": lambda x: +x,
    "-": lambda x: -x,
}

_BINARY_FOLD: dict[str, Callable[[float, float], float]] = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
}


class OptimizerVisitor(Visitor[Node]):
    """Rewrite an AST into an equivalent, smaller one.

    Two flavours of rewrite run together:

    * **Constant folding** — sub-trees whose operands are all literals
      collapse to a single `NumberLiteral`.
    * **Algebraic identities** — `x + 0`, `x - 0`, `x * 1`, `x / 1`, `x * 0`,
      `+x`, and `--x` simplify even when one side is a variable reference.

    The visitor returns a new `Node` rather than mutating the input, so the
    original tree is safe to reuse. Division is never folded when the
    denominator is zero, so the optimised tree still raises at evaluation
    time exactly where the original would.
    """

    def visit_number_literal(self, node: NumberLiteral) -> Node:
        return node

    def visit_variable_ref(self, node: VariableRef) -> Node:
        return node

    def visit_unary_op(self, node: UnaryOp) -> Node:
        operand = node.operand.accept(self)
        identity = _simplify_unary(node.op, operand)
        if identity is not None:
            return identity
        if isinstance(operand, NumberLiteral) and node.op in _UNARY_FOLD:
            return NumberLiteral(_UNARY_FOLD[node.op](operand.value))
        return UnaryOp(node.op, operand)

    def visit_binary_op(self, node: BinaryOp) -> Node:
        left = node.left.accept(self)
        right = node.right.accept(self)
        identity = _simplify_binary(node.op, left, right)
        if identity is not None:
            return identity
        folded = _fold_binary(node.op, left, right)
        if folded is not None:
            return folded
        return BinaryOp(node.op, left, right)


def _simplify_unary(op: str, operand: Node) -> Node | None:
    if op == "+":
        return operand
    if op == "-" and isinstance(operand, UnaryOp) and operand.op == "-":
        return operand.operand
    return None


def _simplify_binary(op: str, left: Node, right: Node) -> Node | None:
    handler = _BINARY_IDENTITIES.get(op)
    if handler is None:
        return None
    return handler(left, right)


def _fold_binary(op: str, left: Node, right: Node) -> Node | None:
    if not (isinstance(left, NumberLiteral) and isinstance(right, NumberLiteral)):
        return None
    if op == "/":
        return _fold_division(left.value, right.value)
    handler = _BINARY_FOLD.get(op)
    if handler is None:
        return None
    return NumberLiteral(handler(left.value, right.value))


def _fold_division(numerator: float, denominator: float) -> Node | None:
    # A zero denominator must be preserved so evaluation still raises
    # ZeroDivisionError — folding it away would silently change semantics.
    if denominator == 0:
        return None
    return NumberLiteral(numerator / denominator)


def _is_zero(node: Node) -> bool:
    return isinstance(node, NumberLiteral) and node.value == 0


def _is_one(node: Node) -> bool:
    return isinstance(node, NumberLiteral) and node.value == 1


def _identity_add(left: Node, right: Node) -> Node | None:
    if _is_zero(right):
        return left
    if _is_zero(left):
        return right
    return None


def _identity_sub(left: Node, right: Node) -> Node | None:
    if _is_zero(right):
        return left
    return None


def _identity_mul(left: Node, right: Node) -> Node | None:
    if _is_zero(left) or _is_zero(right):
        return NumberLiteral(0)
    if _is_one(right):
        return left
    if _is_one(left):
        return right
    return None


def _identity_div(left: Node, right: Node) -> Node | None:
    if _is_one(right):
        return left
    return None


_BINARY_IDENTITIES: dict[str, Callable[[Node, Node], "Node | None"]] = {
    "+": _identity_add,
    "-": _identity_sub,
    "*": _identity_mul,
    "/": _identity_div,
}


def optimize(node: Node) -> Node:
    """Convenience wrapper that constructs a visitor and returns the optimised tree."""
    return node.accept(OptimizerVisitor())
