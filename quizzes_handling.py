import argparse
import glob
import json
import random
import re

from environs import Env
from redis import Redis


def extract_quiz_from_file(filename: str) -> dict:
    """Generates a list of pairs question-answser from a text file

    Args:
        filename (str): filename of text file to generate quiz from

    Returns:
        dict with {question: answer} pair
    """

    with open(filename, mode='r', encoding='KOI8-R') as file:
        content = file.read().replace('\n\n', '\n').replace('\n', ' ')

    quiz_items = re.findall(r'Вопрос \d+: (.+?) Ответ: (.+?) Автор:', content)

    return {question: answer for question, answer in quiz_items}


def extract_quizzes(number: int = 5) -> dict:
    """Extract a certain number of quizzes from random files

    Args:
        number (int, optional): number of files to extract quizzes from

    Returns:
        dict with {question: answer} pair
    """

    quizzes = dict()

    list_of_quiz_files = glob.glob('quiz_textfiles/*.txt')
    random.shuffle(list_of_quiz_files)

    for filename in list_of_quiz_files[:number]:
        quizzes.update(extract_quiz_from_file(filename))

    return quizzes


def populate_db(db, quizzes):
    """Populate db with given quizzes

    Args:
        db: database to populate
        quizzes (dict): quizzes to populate database with
    """

    # Attention. You must not flush the db if it already has active users
    db.flushdb()

    db.mset(quizzes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Populate db with a given number of quizzes.')
    )
    parser.add_argument(
        '--number',
        type=int,
        default=5,
        help='precise the number of quizzes to populate DB with',
    )
    args = parser.parse_args()
    number = args.number

    env = Env()
    env.read_env()

    redis_endpoint = env.str('REDIS_ENDPOINT')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')

    db = Redis(
        host=redis_endpoint,
        port=redis_port,
        password=redis_password,
    )

    quizzes = extract_quizzes(number)
    populate_db(db, quizzes)
