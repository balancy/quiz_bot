from enum import Enum
import random

from thefuzz import fuzz

from generate_quizzes import extract_quizzes


MIN_ACCURACY = 90
QUIZ_LIST = extract_quizzes()


class BotStates(Enum):
    QUESTION = 1
    ANSWER = 2


def handle_question_logic(user_id, db):
    """Handles question logic. Generates random question-answer, writes the
    answer to the db and returns the question.

    Args:
        user_id: user id
        db: database to store the answer

    Returns:
        quiz question
    """

    quiz = random.choice(QUIZ_LIST)

    db.set(user_id, quiz['answer'])

    return quiz['question']


def check_solution(user_id, user_answer, db):
    """Handles solution check logic. Checks the accuracy of user answer.
    answer to the db and returns the question.

    Args:
        user_id: user id
        user_answer: user answer
        db: database to store the answer

    Returns:
        is user answer correct
        response to the bot
    """

    correct_answer_with_comments = db.get(user_id).decode()
    correct_answer = correct_answer_with_comments.split('.')[0]

    accuracy = fuzz.token_set_ratio(user_answer, correct_answer)

    if is_correct := True if accuracy >= MIN_ACCURACY else False:
        response = 'Правильно! Поздравляю!'
    else:
        response = 'Неправильно... Попробуешь еще раз?'

    return is_correct, response


def get_correct_answer(user_id, db):
    """Gets the correct answer from the db

    Args:
        user_id: user id
        db: database to store the answer

    Returns:
        correct answer
    """

    return db.get(user_id).decode().split('.')[0]
