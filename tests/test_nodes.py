from __future__ import annotations

import pytest

from visitor_ast import BinaryOp, Node, NumberLiteral, UnaryOp, VariableRef


def test_number_literal_holds_value():
    node = NumberLiteral(value=3.5)
    assert node.value == 3.5
    assert isinstance(node, Node)


def test_variable_ref_holds_name():
    node = VariableRef(name="x")
    assert node.name == "x"
    assert isinstance(node, Node)


def test_unary_op_wraps_operand():
    inner = NumberLiteral(value=7)
    node = UnaryOp(op="-", operand=inner)
    assert node.op == "-"
    assert node.operand is inner
    assert isinstance(node.operand, Node)


def test_binary_op_holds_left_and_right():
    left = NumberLiteral(value=1)
    right = VariableRef(name="y")
    node = BinaryOp(op="+", left=left, right=right)
    assert node.op == "+"
    assert node.left is left
    assert node.right is right


def test_nodes_are_frozen():
    node = NumberLiteral(value=1)
    with pytest.raises(Exception):
        node.value = 2  # type: ignore[misc]


def test_nodes_compose_into_a_tree():
    # Represent: -(1 + (2 * x))
    inner_mul = BinaryOp(op="*", left=NumberLiteral(2), right=VariableRef("x"))
    inner_add = BinaryOp(op="+", left=NumberLiteral(1), right=inner_mul)
    tree = UnaryOp(op="-", operand=inner_add)

    assert isinstance(tree, UnaryOp)
    assert isinstance(tree.operand, BinaryOp)
    assert isinstance(tree.operand.right, BinaryOp)
    assert tree.operand.right.right.name == "x"


def test_node_is_abstract():
    from abc import ABC

    assert issubclass(Node, ABC)


def test_equality_is_structural():
    a = BinaryOp(op="+", left=NumberLiteral(1), right=NumberLiteral(2))
    b = BinaryOp(op="+", left=NumberLiteral(1), right=NumberLiteral(2))
    assert a == b
