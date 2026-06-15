from __future__ import annotations

from typing import Callable, Mapping

from visitor_ast.nodes import BinaryOp, Node, NumberLiteral, UnaryOp, VariableRef
from visitor_ast.visitor import Visitor

# Dispatch tables keep operator handling flat — one dict lookup per node
# instead of an if/elif ladder that would push past the 2-level nesting cap.
_UNARY_OPS: dict[str, Callable[[float], float]] = {
    "+": lambda x: +x,
    "-": lambda x: -x,
}

_BINARY_OPS: dict[str, Callable[[float, float], float]] = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
}


class EvaluatorVisitor(Visitor[float]):
    """Compute the numeric value of an arithmetic AST.

    Variable references are resolved against the environment passed in at
    construction time. Unknown variables raise `NameError`; unknown
    operators raise `ValueError`; division by zero raises `ZeroDivisionError`
    (let Python's float arithmetic speak for itself).
    """

    def __init__(self, environment: Mapping[str, float] | None = None) -> None:
        self._env: Mapping[str, float] = environment if environment is not None else {}

    def visit_number_literal(self, node: NumberLiteral) -> float:
        return float(node.value)

    def visit_variable_ref(self, node: VariableRef) -> float:
        if node.name not in self._env:
            raise NameError(f"unbound variable: {node.name!r}")
        return float(self._env[node.name])

    def visit_unary_op(self, node: UnaryOp) -> float:
        handler = _UNARY_OPS.get(node.op)
        if handler is None:
            raise ValueError(f"unsupported unary operator: {node.op!r}")
        return handler(node.operand.accept(self))

    def visit_binary_op(self, node: BinaryOp) -> float:
        handler = _BINARY_OPS.get(node.op)
        if handler is None:
            raise ValueError(f"unsupported binary operator: {node.op!r}")
        left = node.left.accept(self)
        right = node.right.accept(self)
        return handler(left, right)


def evaluate(node: Node, environment: Mapping[str, float] | None = None) -> float:
    """Convenience wrapper that constructs a visitor and evaluates `node`."""
    return node.accept(EvaluatorVisitor(environment))
