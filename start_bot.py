import asyncio
import os
import random

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from CONFIG import *
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F
from aiogram.filters import Command, IS_MEMBER, IS_NOT_MEMBER
from aiogram.filters import ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated
from other import *
from pyrogram import Client, filters
from pyrogram.types import Chat, Dialog
from pyrogram.enums import ChatType

form_router = Router()
bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(form_router)

group = []

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
    await message.answer('Выбери группу')
    await bot.send_message()
    # await state.set_state(GetGroupStates.waiting_for_group_link)

@form_router.message(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def add_new_group(event: ChatMemberUpdated):
    global group
    get_me_coro = await bot.get_me()
    bots_username = get_me_coro.username

    if bots_username == event.from_user.username:
        group.append(f'{event.chat.id}')

@form_router.message(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def remove_old_group(event: ChatMemberUpdated):
    global group
    get_me_coro = await bot.get_me()
    bots_username = get_me_coro.username

    if bots_username == event.from_user.username:
        group.pop(group.index(f'{event.chat.id}'))




