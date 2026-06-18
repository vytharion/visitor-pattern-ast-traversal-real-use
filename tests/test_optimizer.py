from __future__ import annotations

import pytest

from visitor_ast import (
    BinaryOp,
    NumberLiteral,
    OptimizerVisitor,
    UnaryOp,
    VariableRef,
    evaluate,
    optimize,
)


def test_number_literal_is_returned_unchanged():
    node = NumberLiteral(7)
    assert optimize(node) is node


def test_variable_ref_is_returned_unchanged():
    node = VariableRef("x")
    assert optimize(node) is node


def test_unary_minus_on_literal_folds_to_negated_literal():
    assert optimize(UnaryOp("-", NumberLiteral(5))) == NumberLiteral(-5)


def test_unary_plus_collapses_to_operand():
    assert optimize(UnaryOp("+", VariableRef("x"))) == VariableRef("x")


def test_unary_plus_on_literal_returns_same_literal():
    assert optimize(UnaryOp("+", NumberLiteral(3))) == NumberLiteral(3)


def test_double_negation_collapses_to_inner_operand():
    tree = UnaryOp("-", UnaryOp("-", VariableRef("x")))
    assert optimize(tree) == VariableRef("x")


def test_double_negation_on_literal_folds_through():
    tree = UnaryOp("-", UnaryOp("-", NumberLiteral(4)))
    assert optimize(tree) == NumberLiteral(4)


@pytest.mark.parametrize(
    ("op", "left", "right", "expected"),
    [
        ("+", 1, 2, 3),
        ("-", 10, 4, 6),
        ("*", 3, 5, 15),
        ("/", 9, 3, 3.0),
    ],
)
def test_binary_op_on_two_literals_folds(op, left, right, expected):
    tree = BinaryOp(op, NumberLiteral(left), NumberLiteral(right))
    assert optimize(tree) == NumberLiteral(expected)


def test_addition_with_zero_on_right_drops_to_left():
    tree = BinaryOp("+", VariableRef("x"), NumberLiteral(0))
    assert optimize(tree) == VariableRef("x")


def test_addition_with_zero_on_left_drops_to_right():
    tree = BinaryOp("+", NumberLiteral(0), VariableRef("y"))
    assert optimize(tree) == VariableRef("y")


def test_subtraction_of_zero_drops_to_left():
    tree = BinaryOp("-", VariableRef("x"), NumberLiteral(0))
    assert optimize(tree) == VariableRef("x")


def test_multiplication_by_one_drops_to_other_side():
    assert optimize(BinaryOp("*", VariableRef("x"), NumberLiteral(1))) == VariableRef("x")
    assert optimize(BinaryOp("*", NumberLiteral(1), VariableRef("y"))) == VariableRef("y")


def test_multiplication_by_zero_collapses_to_literal_zero():
    assert optimize(BinaryOp("*", VariableRef("x"), NumberLiteral(0))) == NumberLiteral(0)
    assert optimize(BinaryOp("*", NumberLiteral(0), VariableRef("y"))) == NumberLiteral(0)


def test_division_by_one_drops_to_left():
    tree = BinaryOp("/", VariableRef("x"), NumberLiteral(1))
    assert optimize(tree) == VariableRef("x")


def test_division_by_zero_literal_is_preserved():
    # Folding would silently swallow the ZeroDivisionError that the evaluator
    # must keep raising — leave the node alone so semantics match the input.
    tree = BinaryOp("/", NumberLiteral(1), NumberLiteral(0))
    assert optimize(tree) == tree


def test_nested_constant_subtree_folds_under_variable_operation():
    # x + (2 * 3) → x + 6
    tree = BinaryOp(
        "+",
        VariableRef("x"),
        BinaryOp("*", NumberLiteral(2), NumberLiteral(3)),
    )
    assert optimize(tree) == BinaryOp("+", VariableRef("x"), NumberLiteral(6))


def test_full_tree_folds_through_multiple_levels():
    # -(1 + (2 * 3)) → -7
    tree = UnaryOp(
        "-",
        BinaryOp(
            "+",
            NumberLiteral(1),
            BinaryOp("*", NumberLiteral(2), NumberLiteral(3)),
        ),
    )
    assert optimize(tree) == NumberLiteral(-7)


def test_identity_chain_eliminates_entire_arithmetic_skeleton():
    # ((x + 0) * 1) - 0  →  x
    tree = BinaryOp(
        "-",
        BinaryOp(
            "*",
            BinaryOp("+", VariableRef("x"), NumberLiteral(0)),
            NumberLiteral(1),
        ),
        NumberLiteral(0),
    )
    assert optimize(tree) == VariableRef("x")


def test_multiplication_by_zero_short_circuits_a_variable_subtree():
    # (x + y) * 0  →  0
    tree = BinaryOp(
        "*",
        BinaryOp("+", VariableRef("x"), VariableRef("y")),
        NumberLiteral(0),
    )
    assert optimize(tree) == NumberLiteral(0)


def test_optimizer_does_not_mutate_input_tree():
    inner = BinaryOp("*", NumberLiteral(2), NumberLiteral(3))
    tree = BinaryOp("+", VariableRef("x"), inner)
    optimize(tree)
    assert tree == BinaryOp(
        "+",
        VariableRef("x"),
        BinaryOp("*", NumberLiteral(2), NumberLiteral(3)),
    )


def test_optimised_tree_evaluates_to_same_value_as_original():
    # The whole point of constant folding: same observable behaviour.
    tree = BinaryOp(
        "+",
        VariableRef("x"),
        BinaryOp("*", NumberLiteral(2), NumberLiteral(3)),
    )
    env = {"x": 4.0}
    assert evaluate(optimize(tree), env) == evaluate(tree, env)


def test_optimised_tree_preserves_zero_division_runtime_error():
    tree = BinaryOp("/", VariableRef("x"), NumberLiteral(0))
    optimised = optimize(tree)
    with pytest.raises(ZeroDivisionError):
        evaluate(optimised, {"x": 1.0})


def test_optimize_helper_matches_visitor_result():
    visitor = OptimizerVisitor()
    tree = BinaryOp("+", NumberLiteral(1), NumberLiteral(2))
    assert optimize(tree) == tree.accept(visitor)


def test_node_classes_were_not_modified_to_add_this_operation():
    # The whole point of the visitor pattern: adding a new operation only
    # required a new visitor. Each node type exposes exactly the same
    # surface — `accept` — that it did before the optimiser existed.
    for node_cls in (NumberLiteral, VariableRef, UnaryOp, BinaryOp):
        public_methods = {
            name for name in vars(node_cls) if callable(vars(node_cls)[name]) and not name.startswith("_")
        }
        assert public_methods == {"accept"}, (
            f"{node_cls.__name__} grew a non-accept method — open/closed broken"
        )


def test_visitor_can_be_reused_across_trees():
    visitor = OptimizerVisitor()
    first = BinaryOp("+", NumberLiteral(1), NumberLiteral(2)).accept(visitor)
    second = BinaryOp("*", NumberLiteral(3), NumberLiteral(4)).accept(visitor)
    assert first == NumberLiteral(3)
    assert second == NumberLiteral(12)


def test_unknown_operator_is_left_intact():
    # An operator the optimiser doesn't recognise must round-trip unchanged
    # so the evaluator's later error message stays accurate.
    tree = BinaryOp("%", NumberLiteral(5), NumberLiteral(2))
    assert optimize(tree) == tree
