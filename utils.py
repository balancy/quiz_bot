from enum import Enum

from thefuzz import fuzz

MIN_ACCURACY = 90
USER_KEY = b'user'


class BotStates(Enum):
    QUESTION = 1
    ANSWER = 2


class From(Enum):
    TG = 'tg'
    VK = 'vk'


def handle_question_logic(user_id, messenger, db):
    """Handles question logic. Gets random question-answer pair from db,
    writes the answer for the user to the db and returns the question.

    Args:
        user_id: user id
        messenger: type of messenger requesting function
        db: database to store the correct answer

    Returns:
        quiz question
    """

    question = USER_KEY
    while question.startswith(USER_KEY):
        question = db.randomkey()

    answer = db.get(question)

    db.set(f'user_{messenger}_{user_id}', answer)

    return question.decode()


def check_solution(user_id, messenger, user_answer, db):
    """Handles solution check logic. Checks the accuracy of the user answer.
    Returns if the user was correct and according response.

    Args:
        user_id: user id
        messenger: type of messenger requesting function
        user_answer: user answer
        db: database to store the answer

    Returns:
        is_correct: is user answer correct
        response: response to the bot
    """

    correct_answer_with_comment = db.get(f'user_{messenger}_{user_id}')
    correct_answer = correct_answer_with_comment.decode().split('.')[0]

    accuracy = fuzz.token_set_ratio(user_answer, correct_answer)

    if is_correct := True if accuracy >= MIN_ACCURACY else False:
        response = 'Правильно! Поздравляю!'
    else:
        response = 'Неправильно... Попробуешь еще раз?'

    return is_correct, response


def get_correct_answer(user_id, messenger, db):
    """Gets the correct answer from the db

    Args:
        user_id: user id
        messenger: type of messenger requesting function
        db: database to store the answer

    Returns:
        correct answer
    """

    return db.get(f'user_{messenger}_{user_id}').decode().split('.')[0]
