from enum import Enum
from functools import partial
import logging
import random

from environs import Env
from redis import Redis
from telegram import ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)
from thefuzz import fuzz

from generate_quizzes import extract_quizzes


KEYBOARD = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
MIN_ACCURACY = 90

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class BotStates(Enum):
    QUESTION = 1
    ANSWER = 2


def start(update, context):
    update.message.reply_text(
        'Привет. Я бот для викторин! Начинай, нажав на кнопку "Новый вопрос"',
        reply_markup=ReplyKeyboardMarkup(KEYBOARD),
    )

    return BotStates.QUESTION


def handle_new_question_request(update, context, redis_db, quiz_list):
    user_id = update.message.chat_id
    quiz = random.choice(quiz_list)

    redis_db.set(user_id, quiz['answer'])

    update.message.reply_text(
        quiz['question'],
        reply_markup=ReplyKeyboardMarkup(KEYBOARD),
    )

    return BotStates.ANSWER


def handle_solution_attempt(update, context, redis_db):
    user_id = update.message.chat_id
    user_answer = update.message.text

    correct_answer = redis_db.get(user_id).decode().split('.')[0]
    accuracy = fuzz.token_set_ratio(user_answer, correct_answer)

    if accuracy >= MIN_ACCURACY:
        response = 'Правильно! Поздравляю!'
        status = BotStates.QUESTION
    else:
        response = 'Неправильно... Попробуешь еще раз?'
        status = BotStates.ANSWER

    update.message.reply_text(
        response,
        reply_markup=ReplyKeyboardMarkup(KEYBOARD),
    )

    return status


def handle_giveup(update, context, redis_db, quiz_list):
    user_id = update.message.chat_id
    correct_answer = redis_db.get(user_id).decode().split('.')[0]

    update.message.reply_text(
        f'Правильный ответ: {correct_answer}',
        reply_markup=ReplyKeyboardMarkup(KEYBOARD),
    )

    handle_new_question_request(update, context, redis_db, quiz_list)


def handle_random_user_input(update, context):
    update.message.reply_text(
        'Ожидаем, что нажмешь "Новый вопрос"',
        reply_markup=ReplyKeyboardMarkup(KEYBOARD),
    )


def cancel(update, context):
    update.message.reply_text('Пока! Надеемся тебя увидеть в будущем.')
    return ConversationHandler.END


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

    dp.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                BotStates.QUESTION: [
                    MessageHandler(
                        Filters.regex('^(Новый вопрос)$'),
                        partial(
                            handle_new_question_request,
                            redis_db=redis_db,
                            quiz_list=quiz_list,
                        ),
                    ),
                    MessageHandler(Filters.text, handle_random_user_input),
                ],
                BotStates.ANSWER: [
                    MessageHandler(
                        Filters.regex('^(Сдаться)$'),
                        partial(
                            handle_giveup,
                            redis_db=redis_db,
                            quiz_list=quiz_list,
                        ),
                    ),
                    MessageHandler(
                        Filters.text,
                        partial(handle_solution_attempt, redis_db=redis_db),
                    ),
                ],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )
    )

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
