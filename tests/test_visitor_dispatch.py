from __future__ import annotations

from abc import ABC

import pytest

from visitor_ast import (
    BinaryOp,
    NumberLiteral,
    UnaryOp,
    VariableRef,
    Visitor,
)


class _RecordingVisitor(Visitor[str]):
    """Records the order of visits and returns a pseudo s-expression."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def visit_number_literal(self, node: NumberLiteral) -> str:
        self.calls.append(f"num:{node.value}")
        return f"N({node.value})"

    def visit_variable_ref(self, node: VariableRef) -> str:
        self.calls.append(f"var:{node.name}")
        return f"V({node.name})"

    def visit_unary_op(self, node: UnaryOp) -> str:
        self.calls.append(f"unary:{node.op}")
        inner = node.operand.accept(self)
        return f"U({node.op},{inner})"

    def visit_binary_op(self, node: BinaryOp) -> str:
        self.calls.append(f"binary:{node.op}")
        left = node.left.accept(self)
        right = node.right.accept(self)
        return f"B({node.op},{left},{right})"


def test_number_literal_dispatches_to_visit_number_literal():
    visitor = _RecordingVisitor()
    result = NumberLiteral(3.5).accept(visitor)
    assert result == "N(3.5)"
    assert visitor.calls == ["num:3.5"]


def test_variable_ref_dispatches_to_visit_variable_ref():
    visitor = _RecordingVisitor()
    result = VariableRef("x").accept(visitor)
    assert result == "V(x)"
    assert visitor.calls == ["var:x"]


def test_unary_op_dispatches_and_recurses_into_operand():
    visitor = _RecordingVisitor()
    result = UnaryOp("-", NumberLiteral(7)).accept(visitor)
    assert result == "U(-,N(7))"
    assert visitor.calls == ["unary:-", "num:7"]


def test_binary_op_visits_left_subtree_before_right_subtree():
    visitor = _RecordingVisitor()
    tree = BinaryOp("+", NumberLiteral(1), VariableRef("y"))
    result = tree.accept(visitor)
    assert result == "B(+,N(1),V(y))"
    assert visitor.calls == ["binary:+", "num:1", "var:y"]


def test_full_tree_walks_in_preorder():
    # -(1 + (2 * x))
    tree = UnaryOp(
        "-",
        BinaryOp(
            "+",
            NumberLiteral(1),
            BinaryOp("*", NumberLiteral(2), VariableRef("x")),
        ),
    )
    visitor = _RecordingVisitor()
    tree.accept(visitor)
    assert visitor.calls == [
        "unary:-",
        "binary:+",
        "num:1",
        "binary:*",
        "num:2",
        "var:x",
    ]


def test_visitor_is_abstract():
    assert issubclass(Visitor, ABC)


def test_visitor_subclass_without_all_methods_cannot_be_instantiated():
    class HalfBuiltVisitor(Visitor[int]):
        def visit_number_literal(self, node: NumberLiteral) -> int:
            return 0

    with pytest.raises(TypeError):
        HalfBuiltVisitor()  # type: ignore[abstract]


def test_two_visitors_over_same_tree_do_not_share_state():
    tree = BinaryOp("+", NumberLiteral(1), NumberLiteral(2))
    a = _RecordingVisitor()
    b = _RecordingVisitor()
    tree.accept(a)
    tree.accept(b)
    assert a.calls == b.calls
    assert a is not b
