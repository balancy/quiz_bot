import random

from environs import Env
import vk_api as vk
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType


def echo(event, vk_api, keyboard):
    vk_api.messages.send(
        peer_id=event.user_id,
        message=event.text,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000),
    )


if __name__ == "__main__":
    env = Env()
    env.read_env()

    vk_session = vk.VkApi(token=env.str('VK_BOT_TOKEN'))
    vk_api = vk_session.get_api()

    keyboard = VkKeyboard()
    keyboard.add_button('Новый вопрос')
    keyboard.add_button('Сдаться')
    keyboard.add_line()
    keyboard.add_button('Мой счет')

    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            echo(event, vk_api, keyboard)
