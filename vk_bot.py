from enum import Enum
import random

from environs import Env
from redis import Redis
from thefuzz import fuzz
import vk_api as vk
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType

from generate_quizzes import extract_quizzes


MIN_ACCURACY = 90


class BotStates(Enum):
    QUESTION = 1
    ANSWER = 2


def handle_new_question_request(event, vk_api, keyboard, redis_db, quiz_list):
    user_id = event.user_id
    quiz = random.choice(quiz_list)

    redis_db.set(user_id, quiz['answer'])

    vk_api.messages.send(
        peer_id=user_id,
        message=quiz['question'],
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000),
    )

    return BotStates.ANSWER


def handle_random_user_input(event, vk_api, keyboard):
    user_id = event.user_id

    vk_api.messages.send(
        peer_id=user_id,
        message='Ожидаем, что нажмешь "Новый вопрос"',
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000),
    )


def handle_solution_attempt(event, vk_api, keyboard, redis_db):
    user_id = event.user_id
    user_answer = event.text

    correct_answer = redis_db.get(user_id).decode().split('.')[0]
    accuracy = fuzz.token_set_ratio(user_answer, correct_answer)

    if accuracy >= MIN_ACCURACY:
        response = 'Правильно! Поздравляю!'
        status = BotStates.QUESTION
    else:
        response = 'Неправильно... Попробуешь еще раз?'
        status = BotStates.ANSWER

    vk_api.messages.send(
        peer_id=user_id,
        message=response,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000),
    )

    return status


def handle_giveup(event, vk_api, keyboard, redis_db, quiz_list):
    user_id = event.user_id
    correct_answer = redis_db.get(user_id).decode().split('.')[0]

    vk_api.messages.send(
        peer_id=user_id,
        message=f'Правильный ответ: {correct_answer}',
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000),
    )

    return handle_new_question_request(
        event,
        vk_api,
        keyboard,
        redis_db,
        quiz_list,
    )


if __name__ == "__main__":
    env = Env()
    env.read_env()

    vk_bot_token = env.str('VK_BOT_TOKEN')
    redis_endpoint = env.str('REDIS_ENDPOINT')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')

    redis_db = Redis(
        host=redis_endpoint,
        port=redis_port,
        password=redis_password,
    )

    quiz_list = extract_quizzes()

    vk_session = vk.VkApi(token=vk_bot_token)
    vk_api = vk_session.get_api()

    keyboard = VkKeyboard()
    keyboard.add_button('Новый вопрос')
    keyboard.add_button('Сдаться')
    keyboard.add_line()
    keyboard.add_button('Мой счет')

    bot_state = BotStates.QUESTION
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if bot_state == BotStates.QUESTION:
                if event.text == 'Новый вопрос':
                    bot_state = handle_new_question_request(
                        event,
                        vk_api,
                        keyboard,
                        redis_db,
                        quiz_list,
                    )
                else:
                    handle_random_user_input(event, vk_api, keyboard)
            else:
                if event.text == 'Сдаться':
                    bot_state = handle_giveup(
                        event,
                        vk_api,
                        keyboard,
                        redis_db,
                        quiz_list,
                    )
                else:
                    bot_state = handle_solution_attempt(
                        event,
                        vk_api,
                        keyboard,
                        redis_db,
                    )
