"""Tests for src/gen_sudoku.py"""

import pytest
from gen_sudoku import gen_sudoku


def test_returns_two_strings():
    puzzle, solution = gen_sudoku()
    assert isinstance(puzzle, str)
    assert isinstance(solution, str)


def test_puzzle_and_solution_are_not_empty():
    puzzle, solution = gen_sudoku()
    assert len(puzzle) > 0
    assert len(solution) > 0


def test_solution_contains_all_digits():
    _, solution = gen_sudoku()
    for digit in "123456789":
        assert digit in solution, f"Digit {digit} missing from solution"


def test_puzzle_differs_from_solution():
    # With any non-zero difficulty, some cells are removed
    puzzle, solution = gen_sudoku(difficulty=0.5)
    assert puzzle != solution


def test_invalid_max_retries_raises():
    with pytest.raises(RuntimeError):
        # max_retries=0 means no attempts are made, so it must raise
        gen_sudoku(max_retries=0)
