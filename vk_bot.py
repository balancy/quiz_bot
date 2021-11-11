import logging

from environs import Env
from redis import Redis
import vk_api as vk
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id as get_id

from utils import (
    BotStates,
    From,
    check_solution,
    get_correct_answer,
    handle_question_logic,
)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def handle_question_request(event, api, db):
    """Handles question request from the user. Sends a new question.

    Args:
        event: bot event
        api: bot api
        db: db to store correct answer
    """

    user_id = event.user_id

    question = handle_question_logic(user_id, From.VK, db)

    api.messages.send(peer_id=user_id, message=question, random_id=get_id())


def handle_random_user_input(event, api, keyboard):
    """Handles random user input. Sends a message how to start the quiz.

    Args:
        event: bot event
        api: bot api
        keyboard: keyboard to display to the user
    """

    api.messages.send(
        peer_id=event.user_id,
        message='Для старта викторины нажимай "Новый вопрос"',
        keyboard=keyboard.get_keyboard(),
        random_id=get_id(),
    )


def handle_solution_attempt(event, api, db):
    """Handles solution attempt from the user. Responds accordingly.

    Args:
        event: bot event
        api: bot api
        db: db to store correct answer
    """

    user_id = event.user_id
    user_answer = event.text

    is_correct, message = check_solution(user_id, From.VK, user_answer, db)

    api.messages.send(peer_id=user_id, message=message, random_id=get_id())

    if is_correct:
        handle_question_request(event, api, db)


def handle_giveup_request(event, api, db):
    """Handles a giveup request from the user. Sends the correct answer.

    Args:
        event: bot event
        api: bot api
        db: db to store correct answer
    """

    user_id = event.user_id
    correct_answer = get_correct_answer(user_id, From.VK, db)
    message = f'Правильный ответ: {correct_answer}'

    api.messages.send(peer_id=user_id, message=message, random_id=get_id())

    handle_question_request(event, api, db)


if __name__ == "__main__":
    env = Env()
    env.read_env()

    vk_bot_token = env.str('VK_BOT_TOKEN')
    redis_endpoint = env.str('REDIS_ENDPOINT')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')

    db = Redis(host=redis_endpoint, port=redis_port, password=redis_password)
    bot_state = BotStates.QUESTION

    vk_session = vk.VkApi(token=vk_bot_token)
    vk_api = vk_session.get_api()

    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос')
    keyboard.add_button('Сдаться')
    keyboard.add_line()
    keyboard.add_button('Мой счет')

    for event in VkLongPoll(vk_session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if bot_state == BotStates.QUESTION:
                if event.text == 'Новый вопрос':
                    handle_question_request(event, vk_api, db)
                    bot_state = BotStates.ANSWER
                else:
                    handle_random_user_input(event, vk_api, keyboard)
            else:
                if event.text == 'Сдаться':
                    handle_giveup_request(event, vk_api, db)
                else:
                    handle_solution_attempt(event, vk_api, db)
