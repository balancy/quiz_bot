from functools import partial
import json
import logging
import random

from environs import Env
from redis import Redis
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from generate_quiz_list import extract_number_of_quizzes


KEYBOARD = [['Новый вопрос', 'Сдаться'], ['Мой счет']]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text(
        'Привет. Я бот для викторин!',
        reply_markup=ReplyKeyboardMarkup(KEYBOARD),
    )


def get_new_question(update, context, redis_db, quiz_list):
    quiz = random.choice(quiz_list)
    user_id = update.message.chat_id

    redis_db.set(
        user_id,
        quiz['question'],
    )

    update.message.reply_text(
        redis_db.get(user_id).decode(),
        reply_markup=ReplyKeyboardMarkup(KEYBOARD),
    )


def main():
    env = Env()
    env.read_env()

    tg_bot_token = env.str('TG_BOT_TOKEN')
    redis_endpoint = env.str('REDIS_ENDPOINT')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')

    redis_db = Redis(
        host=redis_endpoint,
        port=redis_port,
        password=redis_password,
    )

    quiz_list = extract_number_of_quizzes(number=5)

    updater = Updater(tg_bot_token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(
        MessageHandler(
            Filters.regex('^(Новый вопрос)$'),
            partial(get_new_question, redis_db=redis_db, quiz_list=quiz_list),
        )
    )

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
