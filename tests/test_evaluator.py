from __future__ import annotations

import math

import pytest

from visitor_ast import (
    BinaryOp,
    EvaluatorVisitor,
    NumberLiteral,
    UnaryOp,
    VariableRef,
    evaluate,
)


def test_number_literal_evaluates_to_its_value():
    assert evaluate(NumberLiteral(7)) == 7.0
    assert evaluate(NumberLiteral(3.5)) == 3.5


def test_number_literal_result_is_float():
    result = evaluate(NumberLiteral(4))
    assert isinstance(result, float)


def test_unary_minus_negates_operand():
    assert evaluate(UnaryOp("-", NumberLiteral(9))) == -9.0


def test_unary_plus_is_identity():
    assert evaluate(UnaryOp("+", NumberLiteral(9))) == 9.0


def test_unary_minus_chains_back_to_positive():
    tree = UnaryOp("-", UnaryOp("-", NumberLiteral(5)))
    assert evaluate(tree) == 5.0


@pytest.mark.parametrize(
    ("op", "left", "right", "expected"),
    [
        ("+", 1, 2, 3.0),
        ("-", 10, 4, 6.0),
        ("*", 3, 5, 15.0),
        ("/", 9, 2, 4.5),
    ],
)
def test_each_binary_operator_computes_its_arithmetic(op, left, right, expected):
    tree = BinaryOp(op, NumberLiteral(left), NumberLiteral(right))
    assert evaluate(tree) == expected


def test_binary_division_returns_float_even_for_exact_quotient():
    assert evaluate(BinaryOp("/", NumberLiteral(8), NumberLiteral(2))) == 4.0


def test_division_by_zero_raises():
    tree = BinaryOp("/", NumberLiteral(1), NumberLiteral(0))
    with pytest.raises(ZeroDivisionError):
        evaluate(tree)


def test_variable_ref_resolves_through_environment():
    tree = VariableRef("x")
    assert evaluate(tree, {"x": 42}) == 42.0


def test_unknown_variable_raises_name_error():
    with pytest.raises(NameError, match="unbound variable"):
        evaluate(VariableRef("missing"), {"x": 1})


def test_empty_environment_still_rejects_variable():
    with pytest.raises(NameError):
        evaluate(VariableRef("x"))


def test_unsupported_unary_operator_raises_value_error():
    with pytest.raises(ValueError, match="unary operator"):
        evaluate(UnaryOp("~", NumberLiteral(1)))


def test_unsupported_binary_operator_raises_value_error():
    with pytest.raises(ValueError, match="binary operator"):
        evaluate(BinaryOp("%", NumberLiteral(1), NumberLiteral(2)))


def test_nested_expression_respects_arithmetic_meaning():
    # 1 + 2 * 3  →  7 (multiplication binds tighter via tree shape, not the
    # evaluator — the evaluator just walks what the parser built).
    tree = BinaryOp(
        "+",
        NumberLiteral(1),
        BinaryOp("*", NumberLiteral(2), NumberLiteral(3)),
    )
    assert evaluate(tree) == 7.0


def test_full_tree_with_variables_and_unary():
    # -(1 + (2 * x))  with x = 4   →  -(1 + 8)  →  -9
    tree = UnaryOp(
        "-",
        BinaryOp(
            "+",
            NumberLiteral(1),
            BinaryOp("*", NumberLiteral(2), VariableRef("x")),
        ),
    )
    assert evaluate(tree, {"x": 4}) == -9.0


def test_visitor_can_be_reused_across_trees_with_same_environment():
    visitor = EvaluatorVisitor({"a": 2, "b": 3})
    first = BinaryOp("+", VariableRef("a"), VariableRef("b")).accept(visitor)
    second = BinaryOp("*", VariableRef("a"), VariableRef("b")).accept(visitor)
    assert first == 5.0
    assert second == 6.0


def test_environment_is_not_required_for_pure_arithmetic():
    tree = BinaryOp("-", NumberLiteral(10), NumberLiteral(3))
    assert evaluate(tree) == 7.0


def test_evaluator_does_not_mutate_environment():
    env = {"x": 1.0}
    evaluate(BinaryOp("+", VariableRef("x"), NumberLiteral(2)), env)
    assert env == {"x": 1.0}


def test_float_precision_is_python_native():
    # 0.1 + 0.2 → the familiar IEEE-754 result; the evaluator does not
    # round, it just defers to Python float arithmetic.
    result = evaluate(BinaryOp("+", NumberLiteral(0.1), NumberLiteral(0.2)))
    assert math.isclose(result, 0.3, abs_tol=1e-9)
    assert result != 0.3
