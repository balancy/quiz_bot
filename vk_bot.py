import json
import logging
from random import randint

from environs import Env
from redis import Redis
import vk_api as vk
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id as get_id

from string_functions import check_strings_similarity


logger = logging.getLogger(__name__)


def start(event, api):
    """Handles conversation start with the user.

    Args:
        event: bot event
        api: bot api
        keyboard: keyboard to display to the user
    """

    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос')
    keyboard.add_button('Сдаться')
    keyboard.add_line()
    keyboard.add_button('Мой счет')

    api.messages.send(
        peer_id=event.user_id,
        message='Приступим',
        random_id=get_id(),
        keyboard=keyboard.get_keyboard(),
    )

    handle_question_request(event, api, db)


def handle_question_request(event, api, db):
    """Handles question request from the user. Sends a new question.

    Args:
        event: bot event
        api: bot api
        db: db to store correct answer
    """

    user_id = event.user_id

    number_of_questions = int(db.get('number_of_questions'))

    random_question = json.loads(
        db.get(f'question_{randint(1, number_of_questions)}'),
    )

    db.set(f'user_VK_{user_id}', random_question['answer'])

    api.messages.send(
        peer_id=user_id,
        message=f'Вопрос: {random_question["question"]}',
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
    db_key_template = f'user_VK_{user_id}'

    correct_answer = db.get(db_key_template).decode()
    is_answer_correct = check_strings_similarity(user_answer, correct_answer)

    if is_answer_correct:
        db.incr(f'{db_key_template}_succeded')
        api.messages.send(
            peer_id=user_id,
            message='Правильно! Поздравляю!',
            random_id=get_id(),
        )
        handle_question_request(event, api, db)
    else:
        db.incr(f'{db_key_template}_failed')
        api.messages.send(
            peer_id=user_id,
            message='Неправильно... Попробуешь еще раз?',
            random_id=get_id(),
        )


def handle_giveup_request(event, api, db):
    """Handles a giveup request from the user. Sends the correct answer.

    Args:
        event: bot event
        api: bot api
        db: db to store correct answer
    """

    user_id = event.user_id

    answer = f'Правильный ответ: {db.get(f"user_VK_{user_id}").decode()}'
    db.incr(f'user_VK_{user_id}_given_up')

    api.messages.send(peer_id=user_id, message=answer, random_id=get_id())

    handle_question_request(event, api, db)


def handle_score_request(event, api, db):
    """Handles score request from the user. Sends the score.

    Args:
        event: bot event
        api: bot api
        db: db to store the score
    """

    user_id = event.user_id
    template = f'user_VK_{user_id}_'

    message = (
        f'Угадал раз: {int(db.get(f"{template}succeded") or 0)}\n'
        f'Неудачных попыток: {int(db.get(f"{template}failed") or 0)}\n'
        f'Сдался раз: {int(db.get(f"{template}given_up") or 0)}\n'
    )

    api.messages.send(peer_id=user_id, message=message, random_id=get_id())


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )

    env = Env()
    env.read_env()

    vk_bot_token = env.str('VK_BOT_TOKEN')
    redis_endpoint = env.str('REDIS_ENDPOINT')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')

    db = Redis(host=redis_endpoint, port=redis_port, password=redis_password)

    vk_session = vk.VkApi(token=vk_bot_token)
    vk_api = vk_session.get_api()

    for event in VkLongPoll(vk_session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if not db.get(f'user_VK_{event.user_id}'):
                start(event, vk_api, db)
            if event.text == 'Новый вопрос':
                handle_question_request(event, vk_api, db)
            elif event.text == 'Сдаться':
                handle_giveup_request(event, vk_api, db)
            elif event.text == 'Мой счет':
                handle_score_request(event, vk_api, db)
            else:
                handle_solution_attempt(event, vk_api, db)
