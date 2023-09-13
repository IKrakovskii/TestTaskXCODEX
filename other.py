import shelve
from typing import Any
from loguru import logger
from pyrogram import Client
from CONFIG import TOKEN
from random import shuffle


logger.add(
    'logs/logs.log',
    format='{time} {level} {message}',
    level='DEBUG'
)

shelf = shelve.open('Database/cache')
shelf_arr = shelve.open('Database/array')


def save_key_value(key: str, value: Any):
    shelf[key] = value
    shelf.sync()


def get_data_from_key(key: str) -> Any | bool:
    try:
        return shelf[key]
    except KeyError:
        return False


def delete_by_key(key: str):
    shelf.pop(key)


async def get_members_usernames(chat_id):
    # app = Client(name="my_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)
    app = Client(name="my_bot", bot_token=TOKEN, api_id=None, api_hash=None)
    await app.start()
    chat_members = []

    async for member in app.get_chat_members(chat_id):
        r = (await app.get_chat_member(user_id=member.user.id, chat_id=chat_id)).user.username
        if r is not None:
            chat_members.append(f'@{r}')
        save_key_value(key='members_usernames', value=chat_members)
    await app.stop()
    return chat_members

'''
невидимые теги

await bot.send_photo(
        chat_id=message.chat.id,
        photo=message.photo[0].file_id,
        caption=f'{message.caption if message.text is None else message.text}'
                f'\n[ ᅠ ]({teg1})[ ᅠ ]({teg2})[ ᅠ ]({teg3})[ ᅠ ]({teg4})[ ᅠ ]({teg5})',
        parse_mode='Markdown'
    )

'''
