import argparse
import glob
import json
import re
import sys


def extract_quiz_list_from_file(filename: str) -> list:
    with open(filename, mode='r', encoding='KOI8-R') as file:
        file_content = file.read().replace('\n\n', '\n').replace('\n', ' ')

    quiz_items = re.findall(
        r'Вопрос \d+: (.+?) Ответ: (.+?) Автор:',
        file_content,
    )

    return [
        {'question': question, 'answser': answer}
        for (question, answer) in quiz_items
    ]


def extract_full_quiz_list():
    quiz_list = []

    for filename in list(glob.glob('quiz_textfiles/*.txt'))[:5]:
        next_piece_of_quiz_list = extract_quiz_list_from_file(filename)
        quiz_list.extend(next_piece_of_quiz_list)

    return quiz_list


if __name__ == '__main__':
    default_quiz_textfile_name = 'quiz_textfiles/1vs1200.txt'

    parser = argparse.ArgumentParser(
        description=('Generate quiz list based on given quiz textfile.')
    )
    parser.add_argument(
        '-f',
        '--file',
        type=str,
        default=default_quiz_textfile_name,
        help='local path to textfile with quiz',
    )
    args = parser.parse_args()
    textfile_name = args.file

    try:
        quiz = extract_quiz_list_from_file(textfile_name)
    except FileNotFoundError:
        sys.exit(f'Couldn\'t find the file "{textfile_name}"')
    else:
        with open('quiz.json', 'w', encoding='utf-8') as fw:
            json.dump(quiz, fw, ensure_ascii=False, indent=4)
