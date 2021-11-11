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


class ScoreKeys(Enum):
    GIVEN_UP = 'given_up'
    FAILED = 'failed'
    SUCCEDED = 'succeded'


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


def get_correct_answer(user_id, messenger, db):
    """Gets the correct answer from the db.

    Args:
        user_id: user id
        messenger: type of messenger requesting function
        db: database to store the answer

    Returns:
        correct answer
    """

    correct_answer_with_comment = db.get(f'user_{messenger}_{user_id}')
    correct_answer = correct_answer_with_comment.decode().split('.')[0]

    return correct_answer


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

    correct_answer = get_correct_answer(user_id, messenger, db)

    accuracy = fuzz.token_set_ratio(user_answer, correct_answer)

    if is_correct := True if accuracy >= MIN_ACCURACY else False:
        response = 'Правильно! Поздравляю!'
        db.incr(f'user_{messenger}_{user_id}_{ScoreKeys.SUCCEDED}')
    else:
        response = 'Неправильно... Попробуешь еще раз?'
        db.incr(f'user_{messenger}_{user_id}_{ScoreKeys.FAILED}')

    return is_correct, response


def handle_giveup_logic(user_id, messenger, db):
    """Handles giveup logic. Returns the correct answer.

    Args:
        user_id: user id
        messenger: type of messenger requesting function
        db: database to store the answer

    Returns:
        correct answer
    """

    answer = get_correct_answer(user_id, messenger, db)
    db.incr(f'user_{messenger}_{user_id}_{ScoreKeys.GIVEN_UP}')

    return f'Правильный ответ: {answer}'


def handle_score_flush(user_id, messenger, db):
    """Handles score flush logic. Flushes the score for current user.

    Args:
        user_id: user id
        messenger: type of messenger requesting function
        db: database to store the score
    """

    template = f'user_{messenger}_{user_id}_'

    for key in ScoreKeys:
        db.set(f'{template}{key}', 0)


def handle_score_logic(user_id, messenger, db):
    """Handles score logic. Returns the score.

    Args:
        user_id: user id
        messenger: type of messenger requesting function
        db: database to store the score

    Returns:
        the score in formatted form
    """

    template = f'user_{messenger}_{user_id}_'

    score = {
        'failed': db.get(f'{template}{ScoreKeys.FAILED}'),
        'succeded': db.get(f'{template}{ScoreKeys.SUCCEDED}'),
        'given_up': db.get(f'{template}{ScoreKeys.GIVEN_UP}'),
    }

    for type, value in score.items():
        score[type] = 0 if value is None else value.decode()

    message = (
        f'Угадал раз: {score["succeded"]}\n'
        f'Неудачных попыток: {score["failed"]}\n'
        f'Сдался раз: {score["given_up"]}\n'
    )

    return message
