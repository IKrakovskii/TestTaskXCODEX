import asyncio
import os
import random

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

from CONFIG import *
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from other import *
from pyrogram import Client, filters

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
                            "сообщений /add_tagged_message")


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
    await message.answer('Добавьте меня в группу и отправьте мне ссылку на любое сообщение из этой группы')
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
    save_key_value('caption_text', value=message.caption if message.caption is not None else message.text)
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
    await message.answer('Сообщение принято, будем тегать?', reply_markup=keyboard)
    await state.set_state(GetGroupStates.will_pin_be_used)


@form_router.message(GetGroupStates.will_pin_be_used)
@logger.catch
async def will_teg_be_used(message: types.Message, state: FSMContext):
    if message.text == '✅Да':
        save_key_value('will_teg_be_used', value=True)
        await get_members_usernames(get_data_from_key('group_id'))
    elif message.text == '❌нет':
        save_key_value('will_teg_be_used', value=False)
    await message.answer('Отправь время, через которое нужно перезакреплять сообщения( в минутах). \n\n'
                         'Можно написать целое число или через точку, например, 0.5',
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(GetGroupStates.timer)


@form_router.message(GetGroupStates.timer)
@logger.catch
async def timer(message: types.Message, state: FSMContext):

    await message.answer('Начинаю цикличное перезакрепление сообщения. \n\n'
                         'Для завершения напишите /stop_tagged')
    await state.clear()

    save_key_value(f'{get_data_from_key("group_id")}_stop_tagged', 'True')
    r = await infinity_tags(get_data_from_key('group_id'))


@form_router.message(Command('stop_tagged'))
@logger.catch
async def stop_tagged(message: types.Message):
    delete_by_key(f'{get_data_from_key("group_id")}_stop_tagged')


@logger.catch
async def infinity_tags(chat_id, number_of_tags):
    while True:
        if get_data_from_key('will_teg_be_used'):
            members_usernames = get_data_from_key('members_usernames')
            tegs = tuple(random.sample(members_usernames, int(number_of_tags)))
            logger.debug(f'{tegs=}')

        else:
            tegs = ['1' for i in range(5)]
        if not get_data_from_key(f'{chat_id}_stop_tagged'):
            break
        await send_message_with_tags(tegs)
        r = await bot.pin_chat_message(
            chat_id=get_data_from_key('group_id'),
            message_id=get_data_from_key('message_id_from_pin')
        )
        await asyncio.sleep(get_data_from_key('timer') * 60)
        await bot.delete_message(
            chat_id=get_data_from_key('group_id'),
            message_id=get_data_from_key('message_id_from_pin'))
    await bot.send_message(chat_id=chat_id, text='Цикличное закрепление с тегированием завершено')


@logger.catch
async def send_message_with_tags(tegs_in_tuple, buttons=None):
    builder = InlineKeyboardBuilder()
    if buttons is not None:
        for i in buttons:
            builder.row(
                text=i['name'],
                url=i['URL']
            )

    if get_data_from_key('message_photo'):
        msg = await bot.send_photo(
            chat_id=get_data_from_key('group_id'),
            photo=get_data_from_key('message_photo'),
            caption=f"{get_data_from_key('caption_text')}\n{''.join(f'[ ᅠ ]({tag})' for tag in tegs_in_tuple)}",
            parse_mode='Markdown',
            disable_notification=True,
            reply_markup=builder.as_markup()
        )
        save_key_value(key=f'message_id_from_pin', value=msg.message_id)
    else:
        msg = await bot.send_message(
            chat_id=get_data_from_key('group_id'),
            text=f'{get_data_from_key("caption_text")}'
                 f"{get_data_from_key('caption_text')}\n{''.join(f'[ ᅠ ]({tag})' for tag in tegs_in_tuple)}",
            parse_mode='Markdown',
            disable_notification=True,
            reply_markup=builder.as_markup()
        )
        save_key_value(key=f'message_id_from_pin', value=msg.message_id)


# Для ответа на незапланированные сценарии
# @app.on_message(filters.me in filters.new_chat_members)
# async def add_group(message: types.Message):
#     logger.info(f'ID чата: {message.chat.id}\nНазвание чата {message.chat.title}')


@form_router.message()
@logger.catch
async def other(message: types.Message):
    if message.chat.type == 'private':
        await message.reply('Команда не распознана')
    else:
        if message.pinned_message and message.from_user.username == (await bot.get_me()).username:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


# region запуск бота
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

# endregion
