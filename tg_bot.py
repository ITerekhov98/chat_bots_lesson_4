import logging
import random
from functools import partial

import redis
from environs import Env
from enum import Enum
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, \
    Filters, ConversationHandler, RegexHandler

from quiz_bots_functions import format_answer, get_dict_with_quiz_batch


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


def handle_new_question_request(bot, update, quiz_batch, redis_db):
    question = random.choice(list(quiz_batch))
    redis_db.set(update.message.from_user.id, question)
    update.message.reply_text(text=question)

    return BotStates.ATTEMPT


def handle_solution_attempt(bot, update, quiz_batch, redis_db):
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


def give_up(bot, update, quiz_batch, redis_db):
    question = redis_db.get(update.message.from_user.id)
    correct_answer = quiz_batch[question]
    update.message.reply_text(
        text=f'Правильный ответ: {correct_answer}'
    )

    return handle_new_question_request(bot, update, quiz_batch, redis_db)


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
    )
    env = Env()
    env.read_env()
    quiz_batch = get_dict_with_quiz_batch(
        env.str('PATH_TO_FILE_WITH_QUIZ_QUESTIONS')
    )
    redis_db = redis.StrictRedis(
        host=env.str('REDIS_HOST'),
        port=env.int('REDIS_PORT'),
        password=env.str('REDIS_PASSWORD'),
        charset="utf-8",
        decode_responses=True
    )
    updater = Updater(env.str('TG_BOT_TOKEN'))
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BotStates.ATTEMPT: [
                MessageHandler(
                    Filters.text,
                    partial(
                        handle_solution_attempt,
                        quiz_batch=quiz_batch,
                        redis_db=redis_db
                    )
                )
            ],
            BotStates.QUESTION: [
                RegexHandler(
                    '^(Новый вопрос)$',
                    partial(
                        handle_new_question_request,
                        quiz_batch=quiz_batch,
                        redis_db=redis_db
                    )
                ),
                RegexHandler(
                    '^(Сдаться)$',
                    partial(
                        give_up, 
                        quiz_batch=quiz_batch,
                        redis_db=redis_db
                    )
                ),
                MessageHandler(
                    Filters.text,
                    partial(
                        handle_solution_attempt,
                        quiz_batch=quiz_batch,
                        redis_db=redis_db
                    )
                )
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
