import logging

from environs import Env
from telegram.bot import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text('Привет. Я бот для викторин!')


def echo(update, context):
    update.message.reply_text(update.message.text)


def main():
    env = Env()
    env.read_env()

    token = env.str('TG_BOT_TOKEN')
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, echo))
    # dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
