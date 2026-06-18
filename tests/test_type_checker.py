from __future__ import annotations

import pytest

from visitor_ast import (
    BinaryOp,
    NumberLiteral,
    Type,
    TypeCheckerVisitor,
    UnaryOp,
    VariableRef,
    type_check,
)


def test_integer_valued_literal_is_integer_type():
    assert type_check(NumberLiteral(7)) is Type.INTEGER
    assert type_check(NumberLiteral(7.0)) is Type.INTEGER


def test_non_integer_literal_is_number_type():
    assert type_check(NumberLiteral(3.5)) is Type.NUMBER


def test_unary_minus_preserves_integer_type():
    assert type_check(UnaryOp("-", NumberLiteral(5))) is Type.INTEGER


def test_unary_plus_preserves_number_type():
    assert type_check(UnaryOp("+", NumberLiteral(1.5))) is Type.NUMBER


def test_unary_on_boolean_variable_raises_type_error():
    tree = UnaryOp("-", VariableRef("flag"))
    with pytest.raises(TypeError, match="numeric"):
        type_check(tree, {"flag": Type.BOOLEAN})


def test_unsupported_unary_operator_raises_type_error():
    with pytest.raises(TypeError, match="unary operator"):
        type_check(UnaryOp("~", NumberLiteral(1)))


def test_integer_plus_integer_stays_integer():
    tree = BinaryOp("+", NumberLiteral(1), NumberLiteral(2))
    assert type_check(tree) is Type.INTEGER


def test_integer_plus_float_widens_to_number():
    tree = BinaryOp("+", NumberLiteral(1), NumberLiteral(1.5))
    assert type_check(tree) is Type.NUMBER


def test_division_always_widens_to_number():
    tree = BinaryOp("/", NumberLiteral(8), NumberLiteral(2))
    assert type_check(tree) is Type.NUMBER


def test_multiplication_of_integers_stays_integer():
    tree = BinaryOp("*", NumberLiteral(3), NumberLiteral(4))
    assert type_check(tree) is Type.INTEGER


def test_subtraction_of_integer_and_float_widens():
    tree = BinaryOp("-", NumberLiteral(2.5), NumberLiteral(1))
    assert type_check(tree) is Type.NUMBER


def test_unknown_variable_raises_name_error():
    with pytest.raises(NameError, match="untyped variable"):
        type_check(VariableRef("missing"))


def test_empty_environment_still_rejects_variable():
    with pytest.raises(NameError):
        type_check(VariableRef("x"))


def test_variable_type_resolves_from_environment():
    assert type_check(VariableRef("x"), {"x": Type.INTEGER}) is Type.INTEGER
    assert type_check(VariableRef("y"), {"y": Type.NUMBER}) is Type.NUMBER


def test_boolean_right_operand_raises_type_error_with_right_marker():
    tree = BinaryOp("+", NumberLiteral(1), VariableRef("flag"))
    with pytest.raises(TypeError, match="right"):
        type_check(tree, {"flag": Type.BOOLEAN})


def test_boolean_left_operand_raises_type_error_with_left_marker():
    tree = BinaryOp("+", VariableRef("flag"), NumberLiteral(1))
    with pytest.raises(TypeError, match="left"):
        type_check(tree, {"flag": Type.BOOLEAN})


def test_unsupported_binary_operator_raises_type_error():
    with pytest.raises(TypeError, match="binary operator"):
        type_check(BinaryOp("%", NumberLiteral(1), NumberLiteral(2)))


def test_full_tree_with_float_variable_widens_to_number():
    # -(1 + (2 * x))  with x: NUMBER  →  NUMBER
    tree = UnaryOp(
        "-",
        BinaryOp(
            "+",
            NumberLiteral(1),
            BinaryOp("*", NumberLiteral(2), VariableRef("x")),
        ),
    )
    assert type_check(tree, {"x": Type.NUMBER}) is Type.NUMBER


def test_full_tree_with_only_integers_stays_integer():
    tree = UnaryOp(
        "-",
        BinaryOp(
            "+",
            NumberLiteral(1),
            BinaryOp("*", NumberLiteral(2), VariableRef("x")),
        ),
    )
    assert type_check(tree, {"x": Type.INTEGER}) is Type.INTEGER


def test_division_widens_a_subtree_under_addition():
    # 1 + (4 / 2)  →  INTEGER + NUMBER  →  NUMBER
    tree = BinaryOp(
        "+",
        NumberLiteral(1),
        BinaryOp("/", NumberLiteral(4), NumberLiteral(2)),
    )
    assert type_check(tree) is Type.NUMBER


def test_visitor_can_be_reused_across_trees_with_same_environment():
    visitor = TypeCheckerVisitor({"a": Type.INTEGER, "b": Type.NUMBER})
    first = BinaryOp("+", VariableRef("a"), VariableRef("a")).accept(visitor)
    second = BinaryOp("+", VariableRef("a"), VariableRef("b")).accept(visitor)
    assert first is Type.INTEGER
    assert second is Type.NUMBER


def test_environment_is_not_required_for_pure_arithmetic():
    tree = BinaryOp("-", NumberLiteral(10), NumberLiteral(3))
    assert type_check(tree) is Type.INTEGER


def test_type_checker_does_not_mutate_environment():
    env = {"x": Type.INTEGER}
    type_check(BinaryOp("+", VariableRef("x"), NumberLiteral(2)), env)
    assert env == {"x": Type.INTEGER}


def test_type_check_helper_matches_visitor_result():
    visitor = TypeCheckerVisitor()
    tree = BinaryOp("+", NumberLiteral(1), NumberLiteral(2))
    assert type_check(tree) is tree.accept(visitor)


def test_chained_unary_preserves_inner_type():
    tree = UnaryOp("-", UnaryOp("-", NumberLiteral(2.5)))
    assert type_check(tree) is Type.NUMBER


def test_boolean_in_nested_subtree_still_raises():
    # (1 + flag) * 2 — the inner addition fails before the outer * runs.
    tree = BinaryOp(
        "*",
        BinaryOp("+", NumberLiteral(1), VariableRef("flag")),
        NumberLiteral(2),
    )
    with pytest.raises(TypeError, match="numeric"):
        type_check(tree, {"flag": Type.BOOLEAN})
