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
    check_solution,
    get_correct_answer,
    handle_question_logic,
)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def start(update, context):
    """Handles start command from the user.

    Args:
        update, context: internal arguments of the bot

    Returns:
        state of the bot
    """

    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]

    update.message.reply_text(
        'Я бот для викторин! Начинай, нажав на кнопку "Новый вопрос"',
        reply_markup=ReplyKeyboardMarkup(keyboard),
    )

    return BotStates.QUESTION


def handle_question_request(update, context, db):
    """Handles question request from the bot. Sends a new question.

    Args:
        update, context: internal arguments of the bot

    Returns:
        state of the bot
    """

    question = handle_question_logic(update.message.chat_id, db)

    update.message.reply_text(question)

    return BotStates.ANSWER


def handle_random_user_input(update, context):
    """Handles random user input. Sends a message how to start the quiz.

    Args:
        update, context: internal arguments of the bot
    """

    update.message.reply_text('Для старта викторины нажимай "Новый вопрос"')


def handle_solution_attempt(update, context, db):
    """Handles solution attempt from the user. Responds accordingly.

    Args:
        update, context: internal arguments of the bot
    """

    user_id = update.message.chat_id
    user_answer = update.message.text

    is_correct, message = check_solution(user_id, user_answer, db)

    update.message.reply_text(message)

    if is_correct:
        handle_question_request(update, context, db)


def handle_giveup_request(update, context, db):
    """Handles a giveup request from the user. Sends the correct answer.

    Args:
        update, context: internal arguments of the bot
    """

    correct_answer = get_correct_answer(update.message.chat_id, db)

    update.message.reply_text(f'Правильный ответ: {correct_answer}')

    handle_question_request(update, context, db)


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

    db = Redis(
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
                        partial(handle_question_request, db=db),
                    ),
                    MessageHandler(Filters.text, handle_random_user_input),
                ],
                BotStates.ANSWER: [
                    MessageHandler(
                        Filters.regex('^(Сдаться)$'),
                        partial(handle_giveup_request, db=db),
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
