import logging
import random
import time

import redis
from environs import Env
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from quiz_bots_functions import format_answer, get_dict_with_quiz_batch


logger = logging.getLogger(__name__)


def get_quiz_keyboard():
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.POSITIVE)

    keyboard.add_line()
    keyboard.add_button('Счёт', color=VkKeyboardColor.POSITIVE)

    return keyboard


def start(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        message='Привет! Я бот для викторин!',
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def handle_new_question_request(event, vk_api):
    question = random.choice(list(quiz_batch))
    redis_db.set(event.user_id, question)
    vk_api.messages.send(
        user_id=event.user_id,
        message=question,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def handle_solution_attempt(event, vk_api):
    user_answer = event.text.lower()
    question = redis_db.get(event.user_id)
    correct_answer = format_answer(quiz_batch[question])
    if user_answer.lower() in correct_answer.lower():
        text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
    else:
        text = 'Неправильно… Попробуешь ещё раз?'
    vk_api.messages.send(
        user_id=event.user_id,
        message=text,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def give_up(event, vk_api):
    question = redis_db.get(event.user_id)
    correct_answer = quiz_batch[question]
    vk_api.messages.send(
        user_id=event.user_id,
        message=f'Правильный ответ: {correct_answer}',
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )
    return handle_new_question_request(event, vk_api)


def main():
    logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
    )
    env = Env()
    env.read_env()
    global keyboard
    keyboard = get_quiz_keyboard()
    global quiz_batch
    quiz_batch = get_dict_with_quiz_batch(
        env.str('PATH_TO_FILE_WITH_QUIZ_QUESTIONS')
    )
    global redis_db
    redis_db = redis.StrictRedis(
        host=env.str('REDIS_HOST'),
        port=env.int('REDIS_PORT'),
        password=env.str('REDIS_PASSWORD'),
        charset="utf-8",
        decode_responses=True
    )
    vk_session = vk.VkApi(token=env.str('VK_API_TOKEN'))
    vk_api = vk_session.get_api()
    while True:
        try:
            longpoll = VkLongPoll(vk_session)
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if event.text == 'старт' or event.text == 'Старт':
                        start(event, vk_api)
                    elif event.text == 'Новый вопрос':
                        handle_new_question_request(event, vk_api)
                    elif event.text == 'Сдаться':
                        give_up(event, vk_api)
                    else:
                        handle_solution_attempt(event, vk_api)
        except Exception as error:
            logger.exception(error)
            time.sleep(60)


if __name__ == "__main__":
    main()
