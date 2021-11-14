from enum import Enum

from thefuzz import fuzz

MIN_ACCURACY = 90


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

    correct_answer = db.get(f'user_{messenger}_{user_id}').decode()

    accuracy = fuzz.token_set_ratio(user_answer, correct_answer)

    if is_correct := True if accuracy >= MIN_ACCURACY else False:
        response = 'Правильно! Поздравляю!'
        db.incr(f'user_{messenger}_{user_id}_succeded')
    else:
        response = 'Неправильно... Попробуешь еще раз?'
        db.incr(f'user_{messenger}_{user_id}_failed')

    return is_correct, response
