import logging
import random

from environs import Env
from enum import Enum
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, \
    Filters, ConversationHandler, RegexHandler

from common_utils import quiz_batch, redis_db, format_answer


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)
logger = logging.getLogger(__name__)


class BotStates(Enum):
    ATTEMPT = 1
    QUESTION = 2


def start(bot, update):
    greeting = 'Привет! Я бот для викторин!'
    custom_keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счёт']
    ]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(
        text=greeting,
        reply_markup=reply_markup
    )
    return BotStates.QUESTION


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def handle_new_question_request(bot, update):
    question = random.choice(list(quiz_batch))
    redis_db.set(update.message.from_user.id, question)
    update.message.reply_text(text=question)

    return BotStates.ATTEMPT


def handle_solution_attempt(bot, update):
    user_answer = update.message.text
    question = redis_db.get(update.message.from_user.id)
    correct_answer = format_answer(quiz_batch[question])
    if user_answer.lower() in correct_answer.lower():
        update.message.reply_text(
            text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
        )
    else:
        update.message.reply_text(
            text='Неправильно… Попробуешь ещё раз?'
        )

    return BotStates.QUESTION


def give_up(bot, update):
    question = redis_db.get(update.message.from_user.id)
    correct_answer = quiz_batch[question]
    update.message.reply_text(
        text=f'Правильный ответ: {correct_answer}'
    )

    return handle_new_question_request(bot, update)


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    env = Env()
    env.read_env()
    updater = Updater(env.str('TG_BOT_TOKEN'))
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BotStates.ATTEMPT: [
                MessageHandler(Filters.text, handle_solution_attempt)
            ],

            BotStates.QUESTION: [
                RegexHandler('^(Новый вопрос)$', handle_new_question_request),
                RegexHandler('^(Сдаться)$', give_up),
                MessageHandler(Filters.text, handle_solution_attempt)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
