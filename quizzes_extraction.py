import glob
import random
import re


def extract_quiz_from_file(filename: str) -> dict:
    """Generates a list of pairs question-answser from a text file

    Args:
        filename (str): filename of text file to generate quiz from

    Returns:
        dict with {question: answer} pair
    """

    with open(filename, mode='r', encoding='KOI8-R') as file:
        content = file.read().replace('\n\n', '\n').replace('\n', ' ')

    quiz_items = re.findall(
        r'Вопрос \d+: (.+?) Ответ: (.+?) (Автор|Источник|Комментарий|Зачет):',
        content,
    )

    return {question: answer for question, answer, _ in quiz_items}


def extract_quizzes(number: int = 5) -> dict:
    """Extract a certain number of quizzes from random files

    Args:
        number (int, optional): number of files to extract quizzes from

    Returns:
        dict with {question: answer} pair
    """

    quizzes = dict()

    quiz_files = glob.glob('quiz_textfiles/*.txt')
    random.shuffle(quiz_files)

    for filename in quiz_files[:number]:
        quizzes.update(extract_quiz_from_file(filename))

    return quizzes


if __name__ == '__main__':
    print(len(extract_quizzes()))
