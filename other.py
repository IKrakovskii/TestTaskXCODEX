import shelve
from typing import Any
from aiogram import types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from loguru import logger
from pyrogram import Client
from pyrogram.enums import UserStatus
from CONFIG import TOKEN

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


@logger.catch
def delete_cache(message: types.Message):
    delete_by_key(f'{message.chat.id}_group_id')
    delete_by_key(f'{message.chat.id}_caption_text')
    delete_by_key(f'{message.chat.id}_message_photo')
    delete_by_key(f'{message.chat.id}_buttons_names')
    delete_by_key(f'{message.chat.id}_buttons_urls')
    delete_by_key(f'{message.chat.id}_pin_message')
    delete_by_key(f'{message.chat.id}_delete_old_message')
    delete_by_key(f'{message.chat.id}_amount_of_tags')
    delete_by_key(f'{message.chat.id}_all_or_online_tags')
    delete_by_key(f'{message.chat.id}_timer')


@logger.catch
async def get_members_ids(chat_id, is_online):
    app = Client(name="my_bot", bot_token=TOKEN)
    await app.start()
    chat_members = []
    async for member in app.get_chat_members(int(chat_id)):

        if is_online:
            if member.user.status == UserStatus.ONLINE:
                chat_members.append(member.user.id)
        else:
            chat_members.append(member.user.id)

    await app.stop()
    return chat_members


kb = [
    [
        KeyboardButton(text='✅Да'),
        KeyboardButton(text='❌нет')
    ]
]
yes_no_keyboard = ReplyKeyboardMarkup(
    keyboard=kb,
    resize_keyboard=True,
    one_time_keyboard=True
)

kb = [
    [
        KeyboardButton(text='Всех'),
        KeyboardButton(text='Кто в онлайн')
    ]
]
all_or_online_keyboard = ReplyKeyboardMarkup(
    keyboard=kb,
    resize_keyboard=True,
    one_time_keyboard=True
)
