import redis
from environs import Env


env = Env()
env.read_env()

def format_answer(answer):
    if '.' in answer:
        return answer.split('.')[0]
    if '(' in answer:
        return answer.split('(')[0]
    return answer


def get_dict_with_quiz_batch(path_to_file):
    with open(path_to_file, 'r', encoding='KOI8-R') as f:
        raw_text = f.read().split('\n\n')

    questions = []
    answers = []
    for row in raw_text:
        if row.startswith(('Вопрос', '\nВопрос')):
            questions.append(row)
        elif row.startswith(('Ответ', '\nОтвет')):
            answers.append(row)

    quiz_batch = {}
    for question, answer in zip(questions, answers):
        quiz_batch[question] = answer
    return quiz_batch


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
