import logging

from environs import Env
from redis import Redis
import vk_api as vk
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from utils import (
    BotStates,
    handle_question_logic,
    handle_solution_analyse_logic,
)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def handle_question_request(event, vk_api, keyboard, redis_db):
    user_id = event.user_id

    question, bot_state = handle_question_logic(user_id, redis_db)

    vk_api.messages.send(
        peer_id=user_id,
        message=question,
        keyboard=keyboard.get_keyboard(),
        random_id=get_random_id(),
    )

    return bot_state


def handle_random_user_input(event, vk_api):
    user_id = event.user_id

    vk_api.messages.send(
        peer_id=user_id,
        message='Ожидаем, что нажмешь "Новый вопрос"',
        random_id=get_random_id(),
    )


def handle_solution_attempt(event, vk_api, redis_db):
    user_id = event.user_id
    user_answer = event.text

    response, bot_state = handle_solution_analyse_logic(
        user_id,
        user_answer,
        redis_db,
    )

    vk_api.messages.send(
        peer_id=user_id,
        message=response,
        random_id=get_random_id(),
    )

    return bot_state


def handle_giveup_request(event, vk_api, keyboard, redis_db):
    user_id = event.user_id
    correct_answer = redis_db.get(user_id).decode().split('.')[0]

    vk_api.messages.send(
        peer_id=user_id,
        message=f'Правильный ответ: {correct_answer}',
        random_id=get_random_id(),
    )

    return handle_question_request(
        event,
        vk_api,
        keyboard,
        redis_db,
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

    vk_session = vk.VkApi(token=vk_bot_token)
    vk_api = vk_session.get_api()

    keyboard = VkKeyboard(one_time=False)
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
                    bot_state = handle_question_request(
                        event,
                        vk_api,
                        keyboard,
                        redis_db,
                    )
                else:
                    handle_random_user_input(event, vk_api)
            else:
                if event.text == 'Сдаться':
                    bot_state = handle_giveup_request(
                        event,
                        vk_api,
                        keyboard,
                        redis_db,
                    )
                else:
                    bot_state = handle_solution_attempt(
                        event,
                        vk_api,
                        redis_db,
                    )
