# region Импорты и константы

import asyncio
import os
import random

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from CONFIG import *
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from database_metods import Database
from other import *

form_router = Router()
bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(form_router)

db = Database()


@logger.catch
def is_admin(message: types.Message):
    if type(ADMIN_TG_USER_ID) is list:
        return str(message.from_user.id) in ADMIN_TG_USER_ID
    elif type(ADMIN_TG_USER_ID) is str:
        return str(message.from_user.id) == ADMIN_TG_USER_ID


@logger.catch
def is_private(message: types.Message):
    return message.chat.type == 'private'


# endregion
class FSM(StatesGroup):
    get_group = State()
    get_message = State()
    start_buttons = State()
    get_button_name = State()
    get_button_url = State()
    end_buttons = State()
    will_pin_message = State()
    will_delete_old_message = State()
    will_add_tags = State()
    amount_of_tags = State()
    tag_everyone = State()
    timer = State()
    end = State()


class FSM_STOP(StatesGroup):
    get_group = State()


@form_router.message(Command('start'))
@logger.catch
async def cmd_start(message: types.Message):
    if is_private(message):
        await message.reply("Привет! Я бот для периодического закрепления сообщений.\n\nкоманда для закрепления "
                            "сообщений /add")


@form_router.message(Command('add'))
@logger.catch
async def add_group(message: types.Message, state: FSMContext):
    if not is_admin(message):
        await message.answer('Вы не являетесь администратором')
        return
    delete_cache(message)
    builder = []
    for i in db.get_all_groups():
        builder.append([InlineKeyboardButton(text=i["group_name"], callback_data=i['group_id'])])
    kb = InlineKeyboardMarkup(inline_keyboard=builder)
    await message.answer('Выбери группу', reply_markup=kb)
    await state.set_state(FSM.get_group)


@form_router.callback_query(FSM.get_group)
@logger.catch
async def get_group_id(c_query: types.CallbackQuery, state: FSMContext):
    save_key_value(key=f'{c_query.message.chat.id}_group_id', value=c_query.data)
    await state.set_state(FSM.get_message)
    await bot.send_message(chat_id=c_query.message.chat.id, text='Отправь/перешли мне сообщение')


@form_router.message(FSM.get_message)
@logger.catch
async def get_message(message: types.Message, state: FSMContext):
    save_key_value(key=f'{message.chat.id}_caption_text', value=message.md_text)
    try:
        save_key_value(f'{message.chat.id}_message_photo', value=message.photo[0].file_id)
    except TypeError:
        save_key_value(f'{message.chat.id}_message_photo', value=None)

    await message.answer('Сообщение принято, будем добавлять кнопки?', reply_markup=yes_no_keyboard)
    await state.set_state(FSM.start_buttons)


@form_router.message(FSM.start_buttons)
@logger.catch
async def start_buttons(message: types.Message, state: FSMContext):
    if message.text == '✅Да':
        await state.set_state(FSM.get_button_name)
        await message.answer('Отправь мне название для кнопки')
    elif message.text == '❌нет':
        await state.set_state(FSM.will_pin_message)
        await message.answer('Закрепляем сообщение при работе?', reply_markup=yes_no_keyboard)


@form_router.message(FSM.get_button_name)
@logger.catch
async def get_button_name(message: types.Message, state: FSMContext):
    r = get_data_from_key(key=f'{message.chat.id}_buttons_names')
    if type(r) == list:
        r.append(message.text)
        save_key_value(key=f'{message.chat.id}_buttons_names', value=r)
    else:
        save_key_value(key=f'{message.chat.id}_buttons_names', value=[message.text])

    await message.answer('Отправь ссылку для кнопки')
    await state.set_state(FSM.get_button_url)


@form_router.message(FSM.get_button_url)
@logger.catch
async def get_button_url(message: types.Message, state: FSMContext):
    r = get_data_from_key(key=f'{message.chat.id}_buttons_urls')
    if type(r) == list:
        r.append(message.text)
        save_key_value(key=f'{message.chat.id}_buttons_urls', value=r)
    else:
        save_key_value(key=f'{message.chat.id}_buttons_urls', value=[message.text])
    await state.set_state(FSM.end_buttons)
    await message.answer('Будем добавлять ещё кнопки?', reply_markup=yes_no_keyboard)


@form_router.message(FSM.end_buttons)
@logger.catch
async def end_buttons(message: types.Message, state: FSMContext):
    if message.text == '✅Да':
        await state.set_state(FSM.get_button_name)
        await message.answer('Отправь мне название для кнопки')
    elif message.text == '❌нет':
        await state.set_state(FSM.will_pin_message)
        await message.answer('Закрепляем сообщение при работе?', reply_markup=yes_no_keyboard)


@form_router.message(FSM.will_pin_message)
@logger.catch
async def will_pin_message(message: types.Message, state: FSMContext):
    if message.text == '✅Да':
        save_key_value(f'{message.chat.id}_pin_message', value=1)
    elif message.text == '❌нет':
        save_key_value(f'{message.chat.id}_pin_message', value=0)
    await state.set_state(FSM.will_delete_old_message)
    await message.answer('Удаляем старые сообщения?', reply_markup=yes_no_keyboard)


@form_router.message(FSM.will_delete_old_message)
@logger.catch
async def will_delete_old_message(message: types.Message, state: FSMContext):
    if message.text == '✅Да':
        save_key_value(f'{message.chat.id}_delete_old_message', value=1)
    elif message.text == '❌нет':
        save_key_value(f'{message.chat.id}_delete_old_message', value=0)
    await state.set_state(FSM.will_add_tags)
    await message.answer('Тегируем?', reply_markup=yes_no_keyboard)


@form_router.message(FSM.will_add_tags)
@logger.catch
async def will_add_tags(message: types.Message, state: FSMContext):
    if message.text == '✅Да':
        await state.set_state(FSM.amount_of_tags)
        await message.answer('Сколько людей будем тегать?\n\n'
                             'Напишите число от 1 до 8', reply_markup=ReplyKeyboardRemove())
    elif message.text == '❌нет':
        save_key_value(f'{message.chat.id}_amount_of_tags', value=0)
        await state.set_state(FSM.timer)
        await message.answer('Отправь время, через которое нужно перезакреплять сообщения( в минутах). \n\n'
                             'Можно написать целое число или через точку, например, 0.5',
                             reply_markup=ReplyKeyboardRemove())


@form_router.message(FSM.amount_of_tags)
@logger.catch
async def amount_of_tags(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        save_key_value(f'{message.chat.id}_amount_of_tags', value=amount)
        await state.set_state(FSM.tag_everyone)
        await message.answer('Всех тегаем или тех, кто онлайн?', reply_markup=all_or_online_keyboard)

    except ValueError:
        await message.answer('Неправильное значение')
    except Exception as e:
        logger.error(e)


@form_router.message(FSM.tag_everyone)
@logger.catch
async def tag_everyone(message: types.Message, state: FSMContext):
    if message.text == 'Всех':
        save_key_value(f'{message.chat.id}_all_or_online_tags', value=0)
    elif message.text == 'Кто в онлайн':
        save_key_value(f'{message.chat.id}_all_or_online_tags', value=1)
    await state.set_state(FSM.timer)
    await message.answer('Отправь время, через которое нужно перезакреплять сообщения( в минутах). \n\n'
                         'Можно написать целое число или через точку, например, 0.5',
                         reply_markup=ReplyKeyboardRemove())


@form_router.message(FSM.timer)
@logger.catch
async def timer(message: types.Message, state: FSMContext):
    try:
        save_key_value(f'{message.chat.id}_timer', value=max(0.2, float(message.text)))
    except ValueError:
        await message.answer('Вы неправильно напечатали число\n\n'
                             'Отправь время, через которое нужно перезакреплять сообщения( в минутах). \n\n'
                             'Можно написать целое число, или через точку, например, 0.5')
        return
    except Exception as e:
        logger.error(e)
    await state.clear()
    buttons = []
    if get_data_from_key(f'{message.chat.id}_buttons_names') and get_data_from_key(f'{message.chat.id}_buttons_urls'):

        for name, url in zip(
                get_data_from_key(f'{message.chat.id}_buttons_names'),
                get_data_from_key(f'{message.chat.id}_buttons_urls')):
            buttons.append({'name': name, 'url': url})
    else:

        buttons = None

    db.add_all_params(
        group_id=get_data_from_key(f'{message.chat.id}_group_id'),
        lock=0,
        message_text=get_data_from_key(f'{message.chat.id}_caption_text'),
        message_photo_id=get_data_from_key(f'{message.chat.id}_message_photo'),
        buttons=str(buttons),
        will_pin=get_data_from_key(f'{message.chat.id}_pin_message'),
        delete_previous_messages=get_data_from_key(f'{message.chat.id}_delete_old_message'),
        will_add_tags=0 if get_data_from_key(f'{message.chat.id}_amount_of_tags') == 0 else 1,
        amount_of_tags=get_data_from_key(f'{message.chat.id}_amount_of_tags'),
        tag_everyone=not get_data_from_key(f'{message.chat.id}_all_or_online_tags'),
        currently_in_use=1,
        timer=get_data_from_key(f'{message.chat.id}_timer'))
    group_id = get_data_from_key(f'{message.chat.id}_group_id')
    delete_cache(message)

    await message.answer('Сообщение добавлено в работу, для остановки нажмите /stop')
    await work_with_message(group_id=group_id)


@logger.catch
async def work_with_message(group_id):
    while True:
        data = db.get_group_by_id(group_id=group_id)
        if not data["currently_in_use"]:
            break

        chat_id = data["group_id"]
        message_text = data["message_text"]
        message_photo_id = data["message_photo_id"] if data["message_photo_id"] != '' or data[
            "message_photo_id"] is not None else None
        buttons = data["buttons"]
        will_pin = bool(data["will_pin"])
        delete_previous_messages = bool(data["delete_previous_messages"])
        will_add_tags = bool(data["will_add_tags"])
        amount_of_tags = int(data["amount_of_tags"])
        tag_everyone = bool(data["tag_everyone"])
        timer = float(data["timer"])

        if will_add_tags:
            tags = await get_members_usernames(chat_id=chat_id, is_online=(not tag_everyone))
            await asyncio.sleep(1)
            if tags is None:
                tags = ['test']
            for i in range(amount_of_tags - len(tags)):
                tags.append('test')
            tags_string = '\n' + ''.join([f'[ ᅠ ]({tag})' for tag in random.sample(tags, amount_of_tags)])
        else:
            tags_string = ''

        if buttons == '' or buttons is None:
            keyboard = None
        else:
            builder = []
            for button in buttons:
                builder.append([InlineKeyboardButton(text=button["name"], url=button['url'])])
            keyboard = InlineKeyboardMarkup(inline_keyboard=builder)

        if message_photo_id is None:
            result = await bot.send_message(chat_id=chat_id,
                                            text=f'{message_text}\n{tags_string}',
                                            parse_mode="MarkdownV2",
                                            reply_markup=keyboard)
        else:
            result = await bot.send_photo(photo=message_photo_id,
                                          chat_id=chat_id,
                                          caption=f'{message_text}\n{tags_string}',
                                          parse_mode="MarkdownV2",
                                          reply_markup=keyboard)
        if will_pin:
            await bot.pin_chat_message(chat_id=chat_id, message_id=result.message_id)

        await asyncio.sleep(timer * 60)

        if will_pin:
            await bot.unpin_chat_message(chat_id=chat_id, message_id=result.message_id)

        if delete_previous_messages:
            await bot.delete_message(chat_id=chat_id, message_id=result.message_id)


@form_router.message(Command('stop'))
@logger.catch
async def stop(message: types.Message, state: FSMContext):
    if not is_admin(message):
        await message.answer('Вы не являетесь администратором')
        return
    delete_cache(message)
    builder = []
    for i in db.get_all_groups():
        builder.append([InlineKeyboardButton(text=i["group_name"], callback_data=i['group_id'])])
    kb = InlineKeyboardMarkup(inline_keyboard=builder)
    await message.answer('Выбери группу', reply_markup=kb)
    await state.set_state(FSM_STOP.get_group)


@form_router.callback_query(FSM_STOP.get_group)
@logger.catch
async def get_and_stop_group(c_query: types.CallbackQuery, state: FSMContext):
    data = db.get_group_by_id(c_query.data)
    db.leaved_a_group(data["group_id"])
    db.joined_a_group(group_id=data["group_id"], group_name=data["group_name"])
    await state.clear()
    await bot.send_message(chat_id=c_query.message.chat.id,
                           text='Работа с сообщением приостановлена')


@form_router.message()
@logger.catch
async def add_remove_group(message: types.Message):

    if message.new_chat_members is not None:
        get_me_coro = await bot.get_me()
        bots_username = get_me_coro.username
        usernames = [i.username for i in message.new_chat_members]
        if bots_username in usernames:
            if message.chat.type == 'supergroup':
                db.joined_a_group(group_id=message.chat.id, group_name=f'@{message.chat.username}')
            else:
                db.joined_a_group(group_id=message.chat.id, group_name=message.chat.title)

    if message.left_chat_member is not None:
        get_me_coro = await bot.get_me()
        bots_username = get_me_coro.username

        if bots_username == message.left_chat_member.username:
            db.leaved_a_group(group_id=message.chat.id)

    if message.chat.type == 'private':
        await message.reply('Команда не распознана')
    else:
        if message.pinned_message and message.from_user.username == (await bot.get_me()).username:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


@logger.catch
def build_session():
    if os.path.exists('my_bot.session'):
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
    build_session()
    logger.info('Бот запущен')
    asyncio.run(main())
