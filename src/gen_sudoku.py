import logging
import random

from sudoku import Sudoku
from sudoku.sudoku import UnsolvableSudoku


def gen_sudoku(n=3, difficulty=0.5, max_retries=100):
    """
    Generate a Sudoku puzzle with a unique solution.

    Args:
        n (int): Base size of the Sudoku puzzle (default is 3 for a 9x9 grid).
        difficulty (float): Difficulty level of the puzzle (0.0 to 1.0).
        max_retries (int): Maximum number of attempts to generate a valid puzzle.

    Returns:
        tuple: A tuple containing the puzzle string and the solution string.

    Raises:
        RuntimeError: If a valid puzzle cannot be generated after max_retries attempts.
    """
    retries = 0
    total_cells = n * n * n * n  # Total cells in the board
    blanks_to_remove = int(total_cells * difficulty)  # Number of cells to remove

    while retries < max_retries:
        retries += 1
        try:
            # Step 1: Generate a fully solved Sudoku puzzle
            solved_puzzle = Sudoku(n)
            solution = solved_puzzle.solve()

            # Step 2: Create a copy of the solved board
            puzzle_board = Sudoku._copy_board(solution.board)

            # Step 3: Randomly remove cells to create the puzzle
            cells = [(row, col) for row in range(n * n) for col in range(n * n)]
            random.shuffle(cells)
            removed_cells = 0

            for row, col in cells:
                if removed_cells >= blanks_to_remove:
                    break
                original_value = puzzle_board[row][col]
                puzzle_board[row][col] = Sudoku._empty_cell_value

                # Verify uniqueness after removal
                test_puzzle = Sudoku(n, board=puzzle_board)
                if test_puzzle.has_multiple_solutions():
                    puzzle_board[row][col] = original_value  # Restore cell value if uniqueness fails
                else:
                    removed_cells += 1

            # Step 4: Create a Sudoku instance from the modified board
            puzzle = Sudoku(n, board=puzzle_board)

            # Return the puzzle and solution as strings
            logging.debug(f"Puzzle generated successfully after {retries} attempts.")
            return str(puzzle).strip(), str(solution).strip()

        except UnsolvableSudoku:
            logging.debug(f"Attempt {retries}: Puzzle generation failed, retrying...")

    # If the loop completes without success, raise an error
    raise RuntimeError(f"Failed to generate a valid Sudoku puzzle after {max_retries} attempts.")
