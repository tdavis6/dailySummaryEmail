import random

from word_search_generator import WordSearch

from gen_sudoku import gen_sudoku


def get_puzzles():
    puzzles_string = ""
    puzzles_ans_string = ""

    puzzles_string += "\n\n# Puzzles"
    puzzles_ans_string += "\n\n# Answers for Puzzles"

    sudoku_string, sudoku_ans_string = gen_sudoku(3,(random.randint(40, 61)/100))

    puzzles_string += "\n\n## Sudoku" + "\n```" + sudoku_string + "\n" + "```"
    puzzles_ans_string += "\n\n## Sudoku" + "\n```" + sudoku_ans_string + "\n" + "```"

    word_search = WordSearch()
    word_search.random_words(10, secret=True, reset_size=True)
    word_search_string = ""
    word_search_ans_string = ""

    for line in word_search.puzzle:
        for word in line:
            word_search_string += word + ""
        word_search_string += "\n"
    for word in word_search.words:
        word_search_ans_string += f"{word.text.capitalize()} ({word.coordinates[0]}, {word.direction.name}) "

    puzzles_string += "\n\n## Word Search" + "\n```" + word_search_string + "\n" + "```"
    puzzles_ans_string += "\n\n## Word Search" + "\n```" + word_search_ans_string + "\n" + "```"

    return puzzles_string, puzzles_ans_string