import argparse
import json

from environs import Env
from redis import Redis

from quizzes_extraction import extract_quizzes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Populate db with a given number of quizzes.')
    )
    parser.add_argument(
        '--number',
        type=int,
        default=10,
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

    new_dict = dict()
    for index, (question, answer) in enumerate(quizzes.items(), 1):
        new_dict[f'question_{index}'] = json.dumps(
            {'question': question, 'answer': answer}, ensure_ascii=False
        )

    new_dict['total_questions'] = len(quizzes)

    db.mset(quizzes)
    print(f'Number of DB records is {len(db.keys())}')
