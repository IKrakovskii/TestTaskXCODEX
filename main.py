import asyncio

from aiogram.types import MessageEntity

from CONFIG import *
from loguru import logger
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from other import *

logger.add(
    'logs/logs.log',
    format='{time} {level} {message}',
    level='DEBUG'
)

form_router = Router()
bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(form_router)


# Проверка на админа
def is_admin(message: types.Message):
    if type(ADMIN_TG_USER_ID) is list:
        logger.debug('list')
        return str(message.from_user.id) in ADMIN_TG_USER_ID
    elif type(ADMIN_TG_USER_ID) is str:
        logger.debug('str')
        return str(message.from_user.id) == ADMIN_TG_USER_ID


def is_private(message: types.Message):
    return message.chat.type == 'private'


# Состояния конечного автомата
class PinStates(StatesGroup):
    waiting_for_message_link = State()
    waiting_for_timer = State()


# стартовая функция(доступна всем)
@form_router.message(Command('start'))
@logger.catch
async def cmd_start(message: types.Message):
    if is_private(message):
        await message.reply("Привет! Я бот для периодического закрепления сообщений.\n\nкоманда для закрепления "
                            "сообщений /add_pin_message")


# начальная функция для закрепления сообщения если человек не проходит проверку на админа, она не запускает туннель
@form_router.message(Command('add_pin_message'))
@logger.catch
async def start_pin_message(message: types.Message, state: FSMContext):
    if is_admin(message) and is_private(message):
        await message.reply('Отправь мне ссылку на сообщение')
        await state.set_state(PinStates.waiting_for_message_link)
    else:
        await message.reply('У вас недостаточно прав, для использования этой функции')


# функция для получения ссылки, берёт из неё chat_id и message_id
@form_router.message(PinStates.waiting_for_message_link)
@logger.catch
async def get_chat_link(message: types.Message, state: FSMContext):
    save_key_value(key=f'{message.chat.id}_message_link', value=message.text)
    await message.reply('Теперь отправь мне время, на которое нужно закрепить(в минутах)')
    await state.set_state(PinStates.waiting_for_timer)


# функция для получения таймера и дальнейшего закрепления сообщения на
@form_router.message(PinStates.waiting_for_timer)
@logger.catch
async def get_timer(message: types.Message, state: FSMContext):
    data = get_data_from_key(f'{message.chat.id}_message_link').split('/')
    chat_id, message_id = f'-100{data[-2]}', data[-1]
    try:
        chat_id = int(chat_id)
    except ValueError:
        chat_id = f"@{chat_id.replace('-100', '')}"
    except Exception as e:
        logger.error(e)

    delete_by_key(f'{message.chat.id}_message_link')
    timer = message.text
    await state.clear()
    r = await pin_unpin_message(
        chat_id=chat_id,
        message_id=message_id,
        timer=timer,
        id_for_positive_request=message.chat.id
    )
    if r:
        await bot.send_message(message.from_user.id, 'Произошла ошибка, бот не состоит в этом чате или не является '
                                                     'администратором')


# закрепляет сообщение на определённый срок(в минутах)
@logger.catch
async def pin_unpin_message(chat_id, message_id, timer, id_for_positive_request):
    try:
        await bot.pin_chat_message(
            message_id=message_id,
            chat_id=chat_id,
            disable_notification=False
        )
        await bot.send_message(id_for_positive_request, f'Сообщение закреплено на {timer} минут')
        await asyncio.sleep(int(timer) * 60)
        await bot.unpin_chat_message(
            message_id=message_id,
            chat_id=chat_id
        )
        return False
    except:
        return True


# Для ответа на незапланированные сценарии
@form_router.message()
@logger.catch
async def other(message: types.Message):
    if message.chat.type == 'private':
        await message.reply('Команда не распознана')


# region запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    logger.info('Бот запущен')
    asyncio.run(main())

# endregion
