import asyncio
import os
import random
from aiogram.filters import Command, IS_MEMBER, IS_NOT_MEMBER
from aiogram.filters import ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

from CONFIG import *
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from pyrogram import Client, filters
from pyrogram.types import Chat, Dialog
from pyrogram.enums import ChatType

from database_metods import Database
from other import *

form_router = Router()
bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(form_router)

app = Client(name="my_bot", bot_token=TOKEN, api_id=None, api_hash=None)
app.start()
db = Database()


def is_admin(message: types.Message):
    if type(ADMIN_TG_USER_ID) is list:
        return str(message.from_user.id) in ADMIN_TG_USER_ID
    elif type(ADMIN_TG_USER_ID) is str:
        return str(message.from_user.id) == ADMIN_TG_USER_ID


def is_private(message: types.Message):
    return message.chat.type == 'private'


class GetGroupStates(StatesGroup):
    send_groups = State()


@form_router.message(Command('start'))
@logger.catch
async def cmd_start(message: types.Message):
    if is_private(message):
        await message.reply("Привет! Я бот для периодического закрепления сообщений.\n\nкоманда для закрепления "
                            "сообщений /add")


@form_router.message(Command('add'))
@logger.catch
async def add_group(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for i in db.get_all_groups():
        logger.info(f'{i["group_name"]}')
        logger.info(f'{i["group_name"]}')

        # builder.row(
        #     [InlineKeyboardButton(f'{i["group_name"]}')],
        #             [InlineKeyboardButton(f'{i["group_name"]}')]
        # )
    await message.answer('Выбери группу')
    await bot.send_message()
    # await state.set_state(GetGroupStates.waiting_for_group_link)


# @form_router.message()
# async def add_new_group(message: types.Message):
#     get_me_coro = await bot.get_me()
#     bots_username = get_me_coro.username
#     if
#     if bots_username == message.new_chat_members[0].username:
#         logger.info(f'{message.chat.id}')
#
#
# @form_router.message()
# async def remove_old_group(message: types.Message):
#     get_me_coro = await bot.get_me()
#     bots_username = get_me_coro.username
#
#     if bots_username == message.left_chat_member[0].username:
#         logger.info(f'{message.chat.id}')


def build_session():
    if os.path.exists('my_bot.session') > 0:
        print('Сессия существует')
    else:
        print('Введите данные')
        api_id = input('API_ID - ')
        api_hash = input('API_HASH - ')

        async def start(api_id, api_hash):
            app = Client(name="my_bot", bot_token=TOKEN, api_id=api_id, api_hash=api_hash)
            await app.start()
            await app.get_me()
            await app.stop()

        asyncio.run(start(api_id=api_id, api_hash=api_hash))


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    # build_session()
    logger.info('Бот запущен')
    asyncio.run(main())
