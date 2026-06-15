from __future__ import annotations

import pytest

from visitor_ast import (
    BinaryOp,
    NumberLiteral,
    PrettyPrinterVisitor,
    UnaryOp,
    VariableRef,
    pretty_print,
)


def render(node) -> str:
    return node.accept(PrettyPrinterVisitor())


def test_integer_valued_number_drops_decimal_point():
    assert render(NumberLiteral(7)) == "7"
    assert render(NumberLiteral(7.0)) == "7"


def test_non_integer_number_keeps_decimal_point():
    assert render(NumberLiteral(3.5)) == "3.5"


def test_variable_ref_renders_its_name():
    assert render(VariableRef("alpha")) == "alpha"


def test_unary_on_atom_has_no_parentheses():
    assert render(UnaryOp("-", VariableRef("x"))) == "-x"
    assert render(UnaryOp("-", NumberLiteral(4))) == "-4"


def test_unary_on_binary_wraps_operand_in_parentheses():
    tree = UnaryOp("-", BinaryOp("+", NumberLiteral(1), VariableRef("x")))
    assert render(tree) == "-(1 + x)"


def test_binary_atoms_render_with_spaced_operator():
    assert render(BinaryOp("+", NumberLiteral(1), VariableRef("y"))) == "1 + y"
    assert render(BinaryOp("*", NumberLiteral(2), VariableRef("x"))) == "2 * x"


def test_higher_precedence_child_omits_parens():
    # 1 + (2 * x)  →  the multiplication binds tighter than the addition,
    # so the source-like form does not need the inner parens.
    tree = BinaryOp(
        "+",
        NumberLiteral(1),
        BinaryOp("*", NumberLiteral(2), VariableRef("x")),
    )
    assert render(tree) == "1 + 2 * x"


def test_lower_precedence_child_on_left_gets_parens():
    # (1 + 2) * 3  →  the addition binds looser than the multiplication,
    # so it must stay parenthesised to preserve meaning.
    tree = BinaryOp(
        "*",
        BinaryOp("+", NumberLiteral(1), NumberLiteral(2)),
        NumberLiteral(3),
    )
    assert render(tree) == "(1 + 2) * 3"


def test_lower_precedence_child_on_right_gets_parens():
    tree = BinaryOp(
        "*",
        NumberLiteral(3),
        BinaryOp("+", NumberLiteral(1), NumberLiteral(2)),
    )
    assert render(tree) == "3 * (1 + 2)"


def test_left_associative_same_precedence_left_child_skips_parens():
    # (1 - 2) - 3  →  left-assoc, no parens needed on the left.
    tree = BinaryOp(
        "-",
        BinaryOp("-", NumberLiteral(1), NumberLiteral(2)),
        NumberLiteral(3),
    )
    assert render(tree) == "1 - 2 - 3"


def test_left_associative_same_precedence_right_child_keeps_parens():
    # 1 - (2 - 3)  →  must stay parenthesised; dropping parens would change
    # the meaning to (1 - 2) - 3.
    tree = BinaryOp(
        "-",
        NumberLiteral(1),
        BinaryOp("-", NumberLiteral(2), NumberLiteral(3)),
    )
    assert render(tree) == "1 - (2 - 3)"


def test_full_canonical_tree_renders_source_like():
    # -(1 + (2 * x))  — the multiplication binds tighter than the addition,
    # so the inner parens collapse; the outer unary keeps its parens.
    tree = UnaryOp(
        "-",
        BinaryOp(
            "+",
            NumberLiteral(1),
            BinaryOp("*", NumberLiteral(2), VariableRef("x")),
        ),
    )
    assert render(tree) == "-(1 + 2 * x)"


def test_pretty_print_helper_matches_visitor():
    tree = BinaryOp("+", NumberLiteral(1), VariableRef("y"))
    assert pretty_print(tree) == render(tree)


def test_visitor_is_stateless_across_calls():
    visitor = PrettyPrinterVisitor()
    tree_a = BinaryOp("+", NumberLiteral(1), NumberLiteral(2))
    tree_b = BinaryOp("*", VariableRef("x"), NumberLiteral(3))
    first = tree_a.accept(visitor)
    second = tree_b.accept(visitor)
    assert first == "1 + 2"
    assert second == "x * 3"
    # Re-render to confirm no accumulated state.
    assert tree_a.accept(visitor) == "1 + 2"


@pytest.mark.parametrize(
    ("op", "expected"),
    [
        ("+", "1 + 2"),
        ("-", "1 - 2"),
        ("*", "1 * 2"),
        ("/", "1 / 2"),
    ],
)
def test_known_binary_operators_render_with_their_symbol(op, expected):
    assert render(BinaryOp(op, NumberLiteral(1), NumberLiteral(2))) == expected
