import asyncio

from CONFIG import *
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from other import *

form_router = Router()
bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(form_router)


# Проверка на админа
def is_admin(message: types.Message):
    if type(ADMIN_TG_USER_ID) is list:
        return str(message.from_user.id) in ADMIN_TG_USER_ID
    elif type(ADMIN_TG_USER_ID) is str:
        return str(message.from_user.id) == ADMIN_TG_USER_ID


def is_private(message: types.Message):
    return message.chat.type == 'private'


# Состояния конечного автомата
class PinStates(StatesGroup):
    waiting_for_message_link = State()
    waiting_for_timer = State()


class GetGroupStates(StatesGroup):
    start_get_group = State()
    waiting_for_group_link = State()
    get_message = State()
    will_tags_be_used = State()


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
        if get_data_from_key(f'{message.chat.id}_message_pin'):
            await message.answer('Вы уже закрепили одно сообщение')
            return
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
    url = get_data_from_key(f'{message.chat.id}_message_link')
    data = url.split('/')
    if len(data) < 2:
        await message.reply('неправильная ссылка!')
        return
    try:
        chat_id, message_id = f'-100{data[-2]}', data[-1]
    except IndexError:
        await message.reply('Неправильная ссылка')
        return

    try:
        chat_id = int(chat_id)
    except ValueError:
        chat_id = f"@{chat_id.replace('-100', '')}"
    except Exception as e:
        logger.error(e)

    delete_by_key(f'{message.chat.id}_message_link')
    timer = message.text
    await state.clear()
    save_key_value(key=f'{message.chat.id}_message_pin', value=url)

    r = await pin_unpin_message(
        chat_id=chat_id,
        message_id=message_id,
        timer=timer,
        id_for_positive_request=message.chat.id,
        message=message
    )
    if r:
        await bot.send_message(message.from_user.id, 'Произошла ошибка, бот не состоит в этом чате или не является '
                                                     'администратором')


# завершение закрепления сообщения
@form_router.message(Command('stop'))
@logger.catch
async def stop_pin(message: types.Message):
    delete_by_key(f'{message.chat.id}_message_pin')
    await message.answer('Сообщение перестало закрепляться')


# закрепляет сообщение на определённый срок(в минутах)
@logger.catch
async def pin_unpin_message(chat_id, message_id, timer, id_for_positive_request, message):
    # цикличное закрепление
    while True:

        if not get_data_from_key(f'{message.chat.id}_message_pin'):
            break
        await bot.pin_chat_message(
            message_id=message_id,
            chat_id=chat_id,
            disable_notification=False
        )
        await asyncio.sleep(int(timer) * 60)
        await bot.unpin_chat_message(
            message_id=message_id,
            chat_id=chat_id
        )
        await asyncio.sleep(10)


@form_router.message(Command('add_group'), GetGroupStates.start_get_group)
@logger.catch
async def add_group(message: types.Message, state: FSMContext):
    await message.answer('Добавьте меня в группу и отправьте мне ссылку на группу')
    await state.set_state(GetGroupStates.waiting_for_group_link)


@form_router.message(GetGroupStates.waiting_for_group_link)
@logger.catch
async def get_group_link(message: types.Message, state: FSMContext):
    save_key_value(key='group', value=message.text)
    await state.set_state(GetGroupStates.get_message)


@form_router.message(GetGroupStates.get_message)
@logger.catch
async def get_message(message: types.Message, state: FSMContext):
    save_key_value(key='message', value=message)


# Для ответа на незапланированные сценарии
@form_router.message()
@logger.catch
async def other(message: types.Message, teg_5_in_tuple: tuple):
    # if message.chat.type == 'private':
    #     await message.reply('Команда не распознана')
    # await bot.copy_message(chat_id=message.chat.id, from_chat_id=message.chat.id, message_id=message.message_id)
    # await message.model_copy(update=(message.text+'@ivkrak'))
    logger.info(f'{message=}')
    teg1, teg2, teg3, teg4, teg5 = teg_5_in_tuple
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=message.photo[0].file_id,
        caption=f'{message.caption if message.text is None else message.text}'
                f'\n[ ᅠ ]({teg1})[ ᅠ ]({teg2})[ ᅠ ]({teg3})[ ᅠ ]({teg4})[ ᅠ ]({teg5})',
        parse_mode='Markdown'
    )
    # " ᅠ "
    # await message.send_copy(chat_id=message.chat.id)

# region запуск бота
async def main():
    # if get_data_from_key('groups'):
    #     save_key_value(key='groups', value=[])
    # if get_data_from_key('message'):
    #     save_key_value(key='message', value=[])
    await dp.start_polling(bot)


if __name__ == '__main__':
    logger.info('Бот запущен')
    asyncio.run(main())

# endregion
