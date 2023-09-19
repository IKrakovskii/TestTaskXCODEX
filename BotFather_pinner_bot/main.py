import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup

from BotFather_pinner_bot.utills import save_key_value, get_data_from_key, delete_by_key, logger

form_router = Router()
bot = Bot(token='6472526630:AAHJ5fgTRrn2JoV4zOUvNQIe4L_Bof-JsJk')
dp = Dispatcher()
dp.include_router(form_router)


class FSM(StatesGroup):
    get_bot_name = State()
    get_bot_token = State()


@form_router.message(Command('start'))
@logger.catch
async def start(message: Message, state: FSMContext):
    await state.set_state(FSM.get_bot_name)
    await message.answer('Привет, я бот, который поможет тебе получить доступ к pinner боту'
                         '(бот для перезакрепа сообщений')
    builder = [[InlineKeyboardButton(text='Команды для управления ботом', callback_data='None')]]
    kb = InlineKeyboardMarkup(inline_keyboard=builder)

    r = await message.answer('/create_bot - создать бота\n'
                             '/admin - для администрирования', reply_markup=kb)
    await bot.pin_chat_message(chat_id=message.chat.id, message_id=r.message_id)
    # await message.answer('Отправь мне ссылку на бота, которого ты создал через @BotFather'
    #                     '\n\nСсылка должна быть в формате: t.me/ExampleBot')


@form_router.message(FSM.get_bot_name)
@logger.catch
async def get_bot_name(message: Message, state: FSMContext):
    # save_key_value(key=f'{message.from_user.id}_bot_name', value=message.text)
    await state.set_state(FSM.get_bot_token)
    await message.answer('Теперь отправь token для бота')


@form_router.message(FSM.get_bot_token)
@logger.catch
async def get_bot_token(message: Message, state: FSMContext):
    # save_key_value(key=f'{message.from_user.id}_bot_name', value=message.text)
    await state.clear()
    await message.answer('Бот разворачивается...')


@form_router.message()
@logger.catch
async def other(message: Message):
    # for i in message:
    #     print(f'{i}')
    # print(f'\n{"_"*20}\n')
    logger.debug(f'{message.md_text=}')
    await message.answer('Спасибо')
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    logger.info('Бот запущен')
    asyncio.run(main())
