from gen_sudoku import gen_sudoku

def get_puzzles():
    puzzles_string = ""
    puzzles_ans_string = ""

    puzzles_string += "\n\n# Puzzles"
    puzzles_ans_string += "\n\n# Answers for Puzzles"

    sudoku_string, sudoku_ans_string = gen_sudoku(3,0.5)
    puzzles_string += "\n```" + sudoku_string + "\n" + "```"
    puzzles_ans_string += "\n```" + sudoku_ans_string + "\n" + "```"

    return puzzles_string, puzzles_ans_string