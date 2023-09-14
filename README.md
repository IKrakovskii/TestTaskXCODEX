Вот примерный README.md файл для описанного задания:

# Телеграм бот для периодического закрепления сообщений

## Описание

Этот бот позволяет периодически закреплять и откреплять указанное сообщение в Telegram чате. 

Основные возможности:

- Закрепление сообщения с уведомлением участников
- Параллельная работа с множеством чатов
- Работа только с администратором

## Установка

Для работы бота нужен:

- Python 3.10 и выше
- Библиотека aiogram
- Токен для бота от @BotFather
- Вписанный токен и id админа в файл CONFIG.py

Установка зависимостей:

```
pip install -r requirements.txt 
```

## Использование

1. Добавить бота в чат с правами администратора и правами на закрепление сообщений
2. Выполнить команду /add_pin_message 
## Команды

- /add - добавить сообщение в работу
- /stop - убрать сообщение из работы





# Описание функций


### database_metods.py:

Database - класс для работы с базой данных SQLite. Содержит методы для создания таблицы groups, добавления/удаления групп, получения данных о группах.

joined_a_group - добавляет новую группу в БД при входе бота в чат

leaved_a_group - удаляет группу из БД при выходе бота из чата

set_lock - устанавливает параметр lock для группы

add_all_params - добавляет все параметры конфигурации сообщения для группы

get_all_groups - возвращает список всех групп из БД

get_group_by_id - возвращает данные о группе по ее ID


### main.py:


is_admin - проверяет, является ли пользователь админом

is_private - проверяет, является ли чат приватным

FSM - класс для хранения состояний конечного автомата

cmd_start - обработчик команды /start

add_group - начало добавления нового сообщения

get_group_id - получает ID группы от пользователя

get_message - получает текст и медиа для сообщения

start_buttons - начинает сбор кнопок для сообщения

get_button_name, get_button_url - получают название и ссылку для одной кнопки

end_buttons - завершает сбор кнопок

will_pin_message и т.д. - получают различные параметры конфигурации сообщения

timer - сохраняет таймер и завершает сбор параметров

work_with_message - отправляет сообщение в группу с заданными параметрами

stop - начало остановки отправки в группу

get_and_stop_group - останавливает отправку в выбранную группу

add_remove_group - обработчики добавления/удаления бота из групп


### other.py:

save_key_value, get_data_from_key и т.д. - вспомогательные функции для работы с "кешем" на основе shelve

get_members_usernames - получает список участников группы для тегов

keyboards - создание клавиатур для диалога с ботом
