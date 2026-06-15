from __future__ import annotations

from visitor_ast.nodes import BinaryOp, NumberLiteral, UnaryOp, VariableRef
from visitor_ast.visitor import Visitor

# Precedence used to decide where parentheses are needed so the rendered
# string parses back to the same tree shape. Higher number binds tighter.
_BINARY_PRECEDENCE: dict[str, int] = {
    "+": 1,
    "-": 1,
    "*": 2,
    "/": 2,
}


class PrettyPrinterVisitor(Visitor[str]):
    """Render an AST back to a source-like string.

    The visitor returns the textual form bottom-up. Parentheses are
    inserted only where precedence (or right-associativity of `-` / `/`)
    would otherwise change the tree's meaning.
    """

    def visit_number_literal(self, node: NumberLiteral) -> str:
        return _format_number(node.value)

    def visit_variable_ref(self, node: VariableRef) -> str:
        return node.name

    def visit_unary_op(self, node: UnaryOp) -> str:
        inner = node.operand.accept(self)
        if isinstance(node.operand, BinaryOp):
            return f"{node.op}({inner})"
        return f"{node.op}{inner}"

    def visit_binary_op(self, node: BinaryOp) -> str:
        parent_prec = _BINARY_PRECEDENCE.get(node.op, 0)
        left = self._wrap_if_needed(node.left, parent_prec, on_left=True)
        right = self._wrap_if_needed(node.right, parent_prec, on_left=False)
        return f"{left} {node.op} {right}"

    def _wrap_if_needed(self, child, parent_prec: int, *, on_left: bool) -> str:
        rendered = child.accept(self)
        if not isinstance(child, BinaryOp):
            return rendered
        child_prec = _BINARY_PRECEDENCE.get(child.op, 0)
        if _needs_parens(child_prec, parent_prec, on_left=on_left):
            return f"({rendered})"
        return rendered


def _needs_parens(child_prec: int, parent_prec: int, *, on_left: bool) -> bool:
    if child_prec < parent_prec:
        return True
    # Left-associative operators: equal precedence on the right needs parens
    # so `1 - (2 - 3)` does not collapse to `1 - 2 - 3`.
    return child_prec == parent_prec and not on_left


def _format_number(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return str(value)


def pretty_print(node) -> str:
    """Convenience wrapper that constructs a visitor and renders `node`."""
    return node.accept(PrettyPrinterVisitor())
