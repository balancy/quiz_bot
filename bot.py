import logging
import random

from environs import Env
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from generate_quiz_list import extract_full_quiz_list


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

KEYBOARD = [
    ['Новый вопрос', 'Сдаться'],
    ['Мой счет'],
]
QUIZ_LIST = extract_full_quiz_list()


def start(update, context):
    update.message.reply_text(
        'Привет. Я бот для викторин!',
        reply_markup=ReplyKeyboardMarkup(KEYBOARD),
    )


def get_new_question(update, context):
    quiz_element = random.choice(QUIZ_LIST)

    update.message.reply_text(
        quiz_element['question'],
        reply_markup=ReplyKeyboardMarkup(KEYBOARD),
    )


def echo(update, context):
    update.message.reply_text(update.message.text)


def main():
    env = Env()
    env.read_env()

    token = env.str('TG_BOT_TOKEN')
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(
        MessageHandler(Filters.regex('^(Новый вопрос)$'), get_new_question)
    )
    dp.add_handler(MessageHandler(Filters.text, echo))
    # dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
