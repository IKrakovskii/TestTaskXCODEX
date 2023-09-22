import os

if not os.path.exists('Database'):
    os.mkdir('Database')

import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import Message
from CONFIG import TOKEN, SUPER_ADMINS
from utills import save_key_value, get_data_from_key, logger, Database

db = Database()

form_router = Router()
bot = Bot(TOKEN)
dp = Dispatcher()
dp.include_router(form_router)


@logger.catch
def is_super_admin(message: Message):
    return str(message.from_user.id) in SUPER_ADMINS


@logger.catch
def is_admin(message: Message):
    ADMINS = db.get_admins()
    return str(message.from_user.id) in ADMINS


@logger.catch
def is_private(message: Message):
    return message.chat.type == 'private'


class FSM(StatesGroup):
    get_bot_name = State()
    get_bot_token = State()
    get_admins = State()
    get_admins_for_new_bot = State()
    get_admins_for_remove = State()


@form_router.message(Command('panel'))
@logger.catch
async def panel(message: Message):
    if is_super_admin(message):
        await message.answer('Добро пожаловать в панель администратора'
                             '\nhttp://178.253.40.252:9000'
                             '\nlogin: admin'
                             '\npassword: admin228228228')
    else:
        await message.answer('Ты не администратор')


@form_router.message(Command('add_admin'))
@logger.catch
async def add_admin(message: Message, state: FSMContext):
    if is_super_admin(message):
        await state.set_state(FSM.get_admins)
        await message.answer('Отправь мне tg_user_id админа')


@form_router.message(FSM.get_admins)
@logger.catch
async def get_admin(message: Message, state: FSMContext):
    db.add_admin(message.text)
    await state.clear()
    await message.answer('Администратор добавлен')


@form_router.message(Command('get_admins'))
@logger.catch
async def get_admins(message: Message):
    if is_super_admin(message):
        admins = db.get_admins()
        if admins is None:
            await message.answer('Спиооа админов пуст')
            return
        s = ''
        for admin in admins:
            print(admin)
            s += f'{admin}\n'
        await message.answer(s)
    else:
        await message.answer('Ты не администратор')


@form_router.message(Command('delete_admins'))
@logger.catch
async def delete_admins(message: Message, state: FSMContext):
    if is_super_admin(message):
        await state.set_state(FSM.get_admins_for_remove)
        await message.answer('Отправь мне tg_user_id админа')
    else:
        await message.answer('Ты не администратор')


@form_router.message(FSM.get_admins_for_remove)
@logger.catch
async def get_admin_for_remove(message: Message, state: FSMContext):
    db.delete_admin(message.text)
    await state.clear()
    await message.answer('Администратор удален')


@form_router.message(Command('start'))
@logger.catch
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Привет, я бот, который поможет тебе получить доступ к pinner'
                         'боту (бот для перезакрепа сообщений')

    if is_super_admin(message):
        r = await message.answer('/create_bot - создать бота'
                                 '\n/add_admin - добавить админа'
                                 '\n/get_admins - получить спиcок админовов'
                                 '\n/delete_admins - удалить админа'
                                 '\n/panel - панель администратора')
        await bot.pin_chat_message(chat_id=message.chat.id, message_id=r.message_id)
    elif is_admin(message) or is_super_admin(message):
        r = await message.answer('/create_bot - создать бота')
        await bot.pin_chat_message(chat_id=message.chat.id, message_id=r.message_id)


@form_router.message(Command('create_bot'))
@logger.catch
async def create_bot(message: Message, state: FSMContext):
    if is_super_admin(message) or is_admin(message):

        await state.set_state(FSM.get_bot_name)
        await message.answer('Отправь мне ссылку на бота\n\nСсылка должна быть в формате: t.me/ExampleBot')
    else:
        await message.answer('Ты не администратор')


@form_router.message(FSM.get_bot_name)
@logger.catch
async def get_bot_name(message: Message, state: FSMContext):
    save_key_value(key=f'{message.from_user.id}_bot_name', value=message.text.split('/')[-1])
    await state.set_state(FSM.get_bot_token)
    await message.answer('Теперь отправь token для бота')


@form_router.message(FSM.get_bot_token)
@logger.catch
async def get_bot_token(message: Message, state: FSMContext):
    save_key_value(key=f'{message.from_user.id}_bot_token', value=message.text)
    await state.set_state(FSM.get_admins_for_new_bot)
    await message.answer('Теперь отправь мне администраторов через запятую')


@form_router.message(FSM.get_admins_for_new_bot)
@logger.catch
async def get_admins_for_new_bot(message: Message, state: FSMContext):
    save_key_value(key=f'{message.from_user.id}_admins', value=message.text.replace(' ', ''))
    await state.clear()
    await message.answer('Спасибо, бот запускается')
    # logger.info(f'docker run -d --name {get_data_from_key(f"{message.from_user.id}_bot_name")}_pinner_bot -e token={get_data_from_key(f"{message.from_user.id}_bot_token")} -e ids={get_data_from_key(f"{message.from_user.id}_admins")} pinner_bot')
    os.system(
        f'docker run -d --name {get_data_from_key(f"{message.from_user.id}_bot_name")}_pinner_bot -e token={get_data_from_key(f"{message.from_user.id}_bot_token")} -e ids={get_data_from_key(f"{message.from_user.id}_admins")} pinner_bot')
    # docker run -d --name pinner_bot88 -e token=6654710163:AAEU7WzGSTSUpYuRIm_7vdRP51e9Ea1g11w -e ids='351162658,1111111111' pinner_bot


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    logger.info('Бот запущен')
    asyncio.run(main())
