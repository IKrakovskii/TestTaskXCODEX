import shelve
from typing import Any
from aiogram import types
from aiogram.exceptions import TelegramBadRequest
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

    try:
        chat_id = int(chat_id)
    except ValueError:
        chat_id = await app.get_chat(chat_id)
        chat_id = int(chat_id.id)
    chat_members = []
    async for member in app.get_chat_members(chat_id):
        if is_online:
            if member.user.status == UserStatus.ONLINE:
                chat_members.append(member.user.id)
        else:
            chat_members.append(member.user.id)

    await app.stop()
    return chat_members


@logger.catch
async def get_chat_id(chat_username):
    app = Client(name="my_bot", bot_token=TOKEN)
    await app.start()
    try:
        chat_id = int(chat_username)
    except ValueError:
        chat_id = await app.get_chat(chat_username)
        chat_id = int(chat_id.id)
    await app.stop()
    return chat_id


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

kb = [
    [
        KeyboardButton(text='🔒Закрепить'),
        KeyboardButton(text='🔁Репост')
    ]
]
pin_or_repost_kb = ReplyKeyboardMarkup(
    keyboard=kb,
    resize_keyboard=True,
    one_time_keyboard=True
)


async def bot_consist_in_group(bot, group_id):
    try:
        get_me = await bot.get_me()
        r = await bot.get_chat_member(group_id, get_me.id)
        return True
    except TelegramBadRequest:
        return False
