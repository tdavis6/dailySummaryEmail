import logging

from sudoku import Sudoku
from sudoku.sudoku import UnsolvableSudoku


def gen_sudoku(n=3, difficulty=0.5):
    puzzle, solution = None, None
    while True:
        try:
            puzzle = Sudoku(n).difficulty(difficulty)
            solution = puzzle.solve(assert_solvable=True)
            break
        except UnsolvableSudoku:
            logging.debug("Regenerating sudoku puzzle due to no solutions found")
            continue

    sudoku_string = str(puzzle).strip()
    sudoku_ans_string = str(solution).strip()

    return sudoku_string, sudoku_ans_string
