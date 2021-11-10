from functools import partial
import json
import logging
import random

from environs import Env
from redis import Redis
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from thefuzz import fuzz

from generate_quizzes import extract_quizzes


KEYBOARD = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
MIN_ACCURACY = 90

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


def send_question(update, context, redis_db, quiz_list):
    user_id = update.message.chat_id
    quiz = random.choice(quiz_list)

    redis_db.set(user_id, json.dumps(quiz, ensure_ascii=False))

    update.message.reply_text(
        json.loads(redis_db.get(user_id))['question'],
        reply_markup=ReplyKeyboardMarkup(KEYBOARD),
    )


def check_answer(update, context, redis_db):
    user_id = update.message.chat_id
    user_answer = update.message.text

    correct_answer = json.loads(redis_db.get(user_id))['answer'].split('.')[0]
    accuracy = fuzz.token_set_ratio(user_answer, correct_answer)

    response_to_bot = (
        'Правильно! Поздравляю!'
        if accuracy >= MIN_ACCURACY
        else 'Неправильно... Попробуешь еще раз?'
    )

    update.message.reply_text(
        response_to_bot,
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

    quiz_list = extract_quizzes()

    updater = Updater(tg_bot_token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(
        MessageHandler(
            Filters.regex('^(Новый вопрос)$'),
            partial(send_question, redis_db=redis_db, quiz_list=quiz_list),
        )
    )
    dp.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command,
            partial(check_answer, redis_db=redis_db),
        ),
    )

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
