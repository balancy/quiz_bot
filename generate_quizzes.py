import argparse
import glob
import json
import random
import re


def extract_quiz_from_file(filename: str) -> list:
    """Generates a list of pairs question-answser from a text file

    Args:
        filename (str): filename of text file to generate quiz from

    Returns:
        list of pairs question-answer
    """

    with open(filename, mode='r', encoding='KOI8-R') as file:
        content = file.read().replace('\n\n', '\n').replace('\n', ' ')

    quiz_items = re.findall(r'Вопрос \d+: (.+?) Ответ: (.+?) Автор:', content)

    return [
        {'question': question, 'answer': answer}
        for (question, answer) in quiz_items
    ]


def extract_quizzes(number: int = 5) -> list:
    """Extract a certain number of quizzes from random files

    Args:
        number (int, optional): number of files to extract quizzes from

    Returns:
        quizzes_list: list of quizzes generated from files
    """

    quizzes_list = []

    list_of_quiz_files = glob.glob('quiz_textfiles/*.txt')
    random.shuffle(list_of_quiz_files)

    for filename in list_of_quiz_files[:number]:
        quizzes_list.extend(extract_quiz_from_file(filename))

    return quizzes_list


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Generate quiz based on given number of quiz textfiles.')
    )
    parser.add_argument(
        '-n',
        '--number',
        type=int,
        default=5,
        help='precise the number of quiz files to extract quizzes from',
    )
    args = parser.parse_args()
    number = args.number

    quizzes = extract_quizzes(number)
    with open('quiz.json', 'w', encoding='utf-8') as fw:
        json.dump(quizzes, fw, ensure_ascii=False, indent=4)
