from functools import partial
import logging

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


def start(update, context):
    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]

    update.message.reply_text(
        'Привет. Я бот для викторин! Начинай, нажав на кнопку "Новый вопрос"',
        reply_markup=ReplyKeyboardMarkup(keyboard),
    )

    return BotStates.QUESTION


def handle_question_request(update, context, redis_db):
    user_id = update.message.chat_id

    question, bot_state = handle_question_logic(user_id, redis_db)

    update.message.reply_text(question)

    return bot_state


def handle_random_user_input(update, context):
    update.message.reply_text('Ожидаем, что нажмешь "Новый вопрос"')


def handle_solution_attempt(update, context, redis_db):
    user_id = update.message.chat_id
    user_answer = update.message.text

    response, bot_state = handle_solution_analyse_logic(
        user_id,
        user_answer,
        redis_db,
    )

    update.message.reply_text(response)

    return bot_state


def handle_giveup_request(update, context, redis_db):
    user_id = update.message.chat_id
    correct_answer = redis_db.get(user_id).decode().split('.')[0]

    update.message.reply_text(f'Правильный ответ: {correct_answer}')

    return handle_question_request(update, context, redis_db)


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

    updater = Updater(tg_bot_token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                BotStates.QUESTION: [
                    MessageHandler(
                        Filters.regex('^(Новый вопрос)$'),
                        partial(handle_question_request, redis_db=redis_db),
                    ),
                    MessageHandler(Filters.text, handle_random_user_input),
                ],
                BotStates.ANSWER: [
                    MessageHandler(
                        Filters.regex('^(Сдаться)$'),
                        partial(handle_giveup_request, redis_db=redis_db),
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
