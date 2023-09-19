import shelve
from typing import Any

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from loguru import logger

logger.add(
    'logs/logs.log',
    format='{time} {level} {message}',
    level='DEBUG'
)

shelf = shelve.open('Database/cache')


@logger.catch
def save_key_value(key: str, value: Any):
    shelf[key] = value
    shelf.sync()


@logger.catch
def get_data_from_key(key: str) -> Any | bool:
    try:
        return shelf[key]
    except KeyError:
        return False


@logger.catch
def delete_by_key(key: str):
    try:
        shelf.pop(key)
    except KeyError:
        return False


yes_no_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='✅Да'), KeyboardButton(text='❌нет')]],
    resize_keyboard=True,
    one_time_keyboard=True
)
continue_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='✅Продолжить')]],
        resize_keyboard=True,
        one_time_keyboard=True
    )