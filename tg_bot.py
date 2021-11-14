from functools import partial
import json
import logging
from random import randint

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

from solution_checking import check_solution


IDLE_STATE = 0


logger = logging.getLogger(__name__)


def start(update, context, db):
    """Handles start command from the user.

    Args:
        update, context: internal arguments of the bot

    Returns:
        state of the bot
    """

    keyboard = ReplyKeyboardMarkup([['Новый вопрос', 'Сдаться'], ['Мой счет']])

    update.message.reply_text('Приступим', reply_markup=keyboard)

    handle_question_request(update, context, db)

    return IDLE_STATE


def handle_question_request(update, context, db):
    """Handles question request from the bot. Sends a new question.

    Args:
        update, context: internal arguments of the bot

    Returns:
        state of the bot
    """

    user_id = update.message.chat_id

    number_of_questions = int(db.get('number_of_questions'))

    random_question = json.loads(
        db.get(f'question_{randint(1, number_of_questions)}'),
    )

    db.set(f'user_TG_{user_id}', random_question['answer'])

    update.message.reply_text(f'Вопрос: {random_question["question"]}')


def handle_solution_attempt(update, context, db):
    """Handles solution attempt from the user. Responds accordingly.

    Args:
        update, context: internal arguments of the bot
    """

    user_id = update.message.chat_id
    user_answer = update.message.text

    is_correct, message = check_solution(user_id, 'TG', user_answer, db)

    update.message.reply_text(message)

    if is_correct:
        handle_question_request(update, context, db)


def handle_giveup_request(update, context, db):
    """Handles a giveup request from the user. Sends the correct answer.

    Args:
        update, context: internal arguments of the bot
    """

    user_id = update.message.chat_id

    answer = f'Правильный ответ: {db.get(f"user_TG_{user_id}").decode()}'
    db.incr(f'user_TG_{user_id}_given_up')

    update.message.reply_text(answer)

    handle_question_request(update, context, db)


def handle_score_request(update, context, db):
    """Handles score request from the user. Sends the score.

    Args:
        update, context: internal arguments of the bot
    """

    template = f'user_TG_{update.message.chat_id}_'

    message = (
        f'Угадал раз: {int(db.get(f"{template}succeded") or 0)}\n'
        f'Неудачных попыток: {int(db.get(f"{template}failed") or 0)}\n'
        f'Сдался раз: {int(db.get(f"{template}given_up") or 0)}\n'
    )

    update.message.reply_text(message)


def cancel(update, context):
    update.message.reply_text('Пока! Надеемся тебя увидеть в будущем.')
    return ConversationHandler.END


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )

    env = Env()
    env.read_env()

    tg_bot_token = env.str('TG_BOT_TOKEN')
    redis_endpoint = env.str('REDIS_ENDPOINT')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')

    db = Redis(
        host=redis_endpoint,
        port=redis_port,
        password=redis_password,
    )

    updater = Updater(tg_bot_token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler('start', partial(start, db=db))],
            states={
                IDLE_STATE: [
                    MessageHandler(
                        Filters.regex('^(Новый вопрос)$'),
                        partial(handle_question_request, db=db),
                    ),
                    MessageHandler(
                        Filters.regex('^(Сдаться)$'),
                        partial(handle_giveup_request, db=db),
                    ),
                    MessageHandler(
                        Filters.regex('^(Мой счет)$'),
                        partial(handle_score_request, db=db),
                    ),
                    MessageHandler(
                        Filters.text,
                        partial(handle_solution_attempt, db=db),
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
