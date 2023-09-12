import asyncio

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

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
    will_pin_be_used = State()
    timer = State()


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
async def pin_unpin_message(chat_id, message_id, timer, message):
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


@form_router.message(Command('add_tagged_message'))
@logger.catch
async def add_group(message: types.Message, state: FSMContext):
    await message.answer('Добавьте меня в группу и отправьте мне ссылку на любое сообщение')
    await state.set_state(GetGroupStates.waiting_for_group_link)


@form_router.message(GetGroupStates.waiting_for_group_link)
@logger.catch
async def get_group_link(message: types.Message, state: FSMContext):
    data = message.text.split('/')
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
        await message.answer('Неправильная ссылка')

    save_key_value(key='group_id', value=chat_id)
    await message.answer('Ссылка принята. Теперь отправь мне сообщение, которое нужно перезакреплять')
    await state.set_state(GetGroupStates.get_message)


@form_router.message(GetGroupStates.get_message)
@logger.catch
async def get_message(message: types.Message, state: FSMContext):
    save_key_value('caption_text', value=message.text)
    try:
        save_key_value('message_photo', value=message.photo[0].file_id)
    except TypeError:
        save_key_value('message_photo', value=None)

    kb = [
        [
            KeyboardButton(text='✅Да'),
            KeyboardButton(text='❌нет')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder='Нужно тегать людей?'
    )
    # kb.button('✅Да')
    # kb.button('❌нет')
    # kb.adjust(2, 1)
    # kb.add(KeyboardButton('✅Да'))
    # kb.add(KeyboardButton('❌нет'))
    await message.answer('Сообщение принято', reply_markup=keyboard)
    await state.set_state(GetGroupStates.will_pin_be_used)


@form_router.message(GetGroupStates.will_pin_be_used)
@logger.catch
async def will_teg_be_used(message: types.Message, state: FSMContext):
    if message.text == '✅Да':
        save_key_value('will_teg_be_used", value=', value=True)
    elif message.text == '❌нет':
        save_key_value('will_teg_be_used', value=False)
    await message.answer('Отправь время, через которое нужно перезакреплять сообщения( в минутах). \n\n'
                         'Можно написать целое число или через точку, например, 0.5',
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(GetGroupStates.timer)


@form_router.message(GetGroupStates.timer)
@logger.catch
async def timer(message: types.Message, state: FSMContext):
    save_key_value('timer', value=float(message.text))
    await message.answer('Начинаю цикличное перезакрепление сообщения. \n\n'
                         'Для завершения напишите /stop_tagged')
    await state.clear()
    if get_data_from_key(will_teg_be_used):
        tegs = (1, 2, 3, 4, 5)
    else:
        tegs = ('https://google.com/' for _ in range(5))

    while True:
        await send_message_with_tags(tegs)
        await bot.pin_chat_message(
            chat_id=get_data_from_key('group_id'),
            message_id=get_data_from_key('message_id_from_pin')
        )
        await asyncio.sleep(get_data_from_key('timer'))
        await bot.delete_message(
            chat_id=get_data_from_key('group_id'),
            message_id=get_data_from_key('message_id_from_pin'))


@logger.catch
async def send_message_with_tags(teg_5_in_tuple):
    teg1, teg2, teg3, teg4, teg5 = teg_5_in_tuple
    if get_data_from_key('message_photo'):
        msg = await bot.send_photo(
            chat_id=get_data_from_key('group_id'),
            photo=get_data_from_key('message_photo'),
            caption=f'{get_data_from_key("caption_text")}'
                    f'\n[ ᅠ ]({teg1})[ ᅠ ]({teg2})[ ᅠ ]({teg3})[ ᅠ ]({teg4})[ ᅠ ]({teg5})',
            parse_mode='Markdown',
            disable_notification=True
        )
        save_key_value(key=f'message_id_from_pin', value=msg.message_id)
    else:
        msg = await bot.send_message(
            chat_id=get_data_from_key('group_id'),
            text=f'{get_data_from_key("caption_text")}'
                 f'\n[ ᅠ ]({teg1})[ ᅠ ]({teg2})[ ᅠ ]({teg3})[ ᅠ ]({teg4})[ ᅠ ]({teg5})',
            parse_mode='Markdown',
            disable_notification=True
        )
        save_key_value(key=f'message_id_from_pin', value=msg.message_id)


# Для ответа на незапланированные сценарии
@form_router.message()
@logger.catch
async def other(message: types.Message):
    if message.chat.type == 'private':
        await message.reply('Команда не распознана')

    await bot.get_users()


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
