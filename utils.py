from enum import Enum
import random

from thefuzz import fuzz

from generate_quizzes import extract_quizzes


MIN_ACCURACY = 90
QUIZ_LIST = extract_quizzes()


class BotStates(Enum):
    QUESTION = 1
    ANSWER = 2


def handle_question_logic(user_id, redis_db):
    quiz = random.choice(QUIZ_LIST)

    redis_db.set(user_id, quiz['answer'])

    return quiz['question'], BotStates.ANSWER


def handle_solution_analyse_logic(user_id, user_answer, redis_db):
    correct_answer_with_comments = redis_db.get(user_id).decode()
    correct_answer = correct_answer_with_comments.split('.')[0]
    accuracy = fuzz.token_set_ratio(user_answer, correct_answer)

    if accuracy >= MIN_ACCURACY:
        response = 'Правильно! Поздравляю!'
        bot_state = BotStates.QUESTION
    else:
        response = 'Неправильно... Попробуешь еще раз?'
        bot_state = BotStates.ANSWER

    return response, bot_state
