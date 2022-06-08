## Vk и TG боты для викторины

### Ссылки на работающих ботов:
- [VK](https://vk.com/club213637331)
- [TG](https://t.me/test_devman_api_bot)


### Установка и запуск:
Для оперативного получения данных бот использует базу данных Redis. Зарегистрироваться можно [здесь](https://redislabs.com/).
Скачайте репозиторий с кодом, создайте  файл `.env` и наполните его необходимыми данными, в формате `KEY=VALUE`. Ожидаются следующие параметры:
- `TG_BOT_TOKEN` - токен вашего бота в тг
- `REDIS_HOST` - хост вашей базы данных в Redis
- `REDIS_PORT` - порт вашей базы данных  
- `REDIS_PASSWORD` - пароль от вашей базы данных
- `VK` - Токен, выданный VK API, для доступа бота к сообщениям. Получить его можно открыв *Ваша группа -> Настройки -> Работа с API*
- `PATH_TO_FILE_WITH_QUIZ_QUESTIONS` - путь к файлу с вопросами для викторины. Чтобы использовать тестовые данные, подставьте значение `1vs1200.txt`


Далее из терминала запускайте скрипты:
```
python vk_bot.py & python tg_bot.py
```