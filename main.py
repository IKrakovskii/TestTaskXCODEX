# region Импорты и константы
import asyncio
import os
import random
import re
import time
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove

from CONFIG import *
from database_metods import Database
from other import *

# class Telegram_Bot:
form_router = Router()

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(form_router)

db = Database()


# form_router.message.register(cmd_start)
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
    get_group_link = State()
    get_group_name = State()
    get_group = State()
    use_old_settings = State()
    is_repost = State()
    get_repost_messages = State()
    get_repost_timer = State()
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
    if is_private(message) and is_admin(message):
        db.create_admin_table(table_name=message.from_user.id)
        await message.reply("Привет! Я бот для периодического закрепления сообщений.\n\nкоманда для закрепления "
                            "сообщений /add")
    else:
        await message.answer('К сожалению, это приватный бот')


@form_router.message(Command('add'))
@logger.catch
async def add_group(message: types.Message, state: FSMContext):
    if is_admin(message) and is_private(message):

        delete_cache(message)
        builder = []
        for i in db.get_all_groups(table_name=message.from_user.id):
            builder.append([InlineKeyboardButton(text=i["group_name"], callback_data=i['group_id'])])
        builder.append([InlineKeyboardButton(text='➕Добавить новую группу', callback_data='new_group')])
        kb = InlineKeyboardMarkup(inline_keyboard=builder)
        await message.answer('Выбери группу', reply_markup=kb)
        await state.set_state(FSM.get_group)
    else:
        await message.answer('Вы не являетесь администратором')


@form_router.callback_query(FSM.get_group)
@logger.catch
async def get_group_id(c_query: types.CallbackQuery, state: FSMContext):
    if c_query.data == 'new_group':
        await state.set_state(FSM.get_group_link)
        await bot.send_message(
            chat_id=c_query.message.chat.id,
            text='Отправь мне ссылку на любое сообщение из группы, которую ты хочешь добавить'
        )
        return

    save_key_value(key=f'{c_query.from_user.id}_group_id', value=c_query.data)
    data = db.get_group_by_id(group_id=c_query.data, table_name=c_query.from_user.id)
    if data['save']:
        await bot.send_message(chat_id=c_query.message.chat.id,
                               text='У вас есть сохранённое сообщение для данной группы:')
        await asyncio.sleep(0.3)

        buttons = data["buttons"]
        will_pin = bool(data["will_pin"])
        delete_previous_messages = bool(data["delete_previous_messages"])
        will_add_tags = bool(data["will_add_tags"])
        amount_of_tags = int(data["amount_of_tags"])
        tag_everyone = bool(data["tag_everyone"])
        timer = float(data["timer"])
        message_db = data['message']

        await bot.send_message(chat_id=c_query.message.chat.id,
                               text=f'Сообщение {"будет" if will_pin else "не будет"} закрепляться\n\n'
                                    f'{"Будут" if delete_previous_messages else "Не будут"} '
                                    f'удаляться предыдущие сообщения\n\n'
                                    f'{"Будут" if will_add_tags else "Не будут"} создаваться таги\n\n'
                                    f'За 1 раз будет упоминаться {amount_of_tags} людей\n\n'
                                    f'Буду тегаться {"все" if tag_everyone else "только кто в онлайн"}\n\n'
                                    f'Задержка между сообщениями будет {timer} минут'
                               )

        # Кнопки
        if buttons == '' or buttons is None:
            keyboard = None
        else:
            builder = []
            for button in buttons:
                builder.append([InlineKeyboardButton(text=button["name"], url=button['url'])])
            keyboard = InlineKeyboardMarkup(inline_keyboard=builder)
        message_text = message_db.md_text
        if message_text == '':
            message_text = None

        if message_db.text is not None:  # DONE
            await bot.send_message(chat_id=c_query.from_user.id,
                                   text=message_text,
                                   reply_markup=keyboard,
                                   parse_mode="MarkdownV2"
                                   )
        elif message_db.voice is not None:
            await bot.send_voice(chat_id=c_query.from_user.id,
                                 voice=message_db.voice.file_id,
                                 caption=message_text,
                                 reply_markup=keyboard,
                                 parse_mode="MarkdownV2"
                                 )
        elif message_db.photo is not None:  # DONE
            await bot.send_photo(chat_id=c_query.from_user.id,
                                 photo=message_db.photo[0].file_id,
                                 caption=message_text,
                                 reply_markup=keyboard,
                                 parse_mode="MarkdownV2"
                                 )

        elif message_db.video_note is not None:  # DONE
            await bot.send_video_note(chat_id=c_query.from_user.id,
                                      video_note=message_db.video_note.file_id,
                                      reply_markup=keyboard
                                      )
        elif message_db.animation is not None:  # DONE
            await bot.send_animation(chat_id=c_query.from_user.id,
                                     animation=message_db.animation.file_id,
                                     caption=message_text,
                                     reply_markup=keyboard,
                                     parse_mode="MarkdownV2"
                                     )
        elif message_db.document is not None:  # DONE
            await bot.send_document(chat_id=c_query.from_user.id,
                                    document=message_db.document.file_id,
                                    caption=message_text,
                                    reply_markup=keyboard,
                                    parse_mode="MarkdownV2"
                                    )
        elif message_db.video is not None:  # DONE
            await bot.send_video(chat_id=c_query.from_user.id,
                                 video=message_db.video.file_id,
                                 caption=message_text,
                                 reply_markup=keyboard,
                                 parse_mode="MarkdownV2"
                                 )
        elif message_db.poll is not None:  # DONE

            await bot.send_poll(chat_id=c_query.from_user.id,
                                question=message_db.poll.question,
                                options=[i.text for i in message_db.poll.options],
                                is_closed=message_db.poll.is_closed,
                                is_anonymous=message_db.poll.is_anonymous,
                                type=message_db.poll.type,
                                allows_multiple_answers=message_db.poll.allows_multiple_answers,
                                correct_option_id=message_db.poll.correct_option_id,
                                explanation=message_db.poll.explanation,
                                explanation_entities=message_db.poll.explanation_entities,
                                open_period=message_db.poll.open_period,
                                close_date=message_db.poll.close_date
                                )
        await state.set_state(FSM.use_old_settings)
        await bot.send_message(chat_id=c_query.message.chat.id,
                               text='Используем это сообщение?',
                               reply_markup=yes_no_keyboard)
    else:
        # await state.set_state(FSM.get_message)
        await state.set_state(FSM.is_repost)
        await bot.send_message(chat_id=c_query.message.chat.id, text='Это будет репост?', reply_markup=yes_no_keyboard)
        # await bot.send_message(chat_id=c_query.message.chat.id, text='Отправь/перешли мне сообщение')


@form_router.message(FSM.get_group_link)
@logger.catch
async def get_group_link(message: types.Message, state: FSMContext):
    data = str(message.text).split('/')
    if len(data) < 2:
        await message.reply('неправильная ссылка!')
        return
    try:
        if data[3] == 'c':
            chat_id, message_id = f'-100{data[4]}', data[-1]
        else:
            chat_id, message_id = f'-100{data[3]}', data[-1]
        group_name = None
        save_key_value(key=f'{message.from_user.id}_new_group_id', value=chat_id)
    except IndexError:
        await message.reply('Неправильная ссылка')
        return
    try:
        chat_id = int(chat_id)
    except ValueError:
        chat_id = f"{chat_id.replace('-100', '')}"
        group_name = f'@{chat_id}'
    except Exception as e:
        logger.error(e)
    if group_name is not None:
        db.joined_a_group(table_name=message.from_user.id, group_id=chat_id, group_name=group_name)
        await state.clear()
        await message.answer('Группа добавлена, чтобы добавить сообщение, отправь мне команду /add')
    else:
        await state.set_state(FSM.get_group_name)
        await message.answer('Отправь мне название для группы')


@form_router.message(FSM.get_group_name)
@logger.catch
async def get_group_name(message: types.Message, state: FSMContext):
    group_id = get_data_from_key(key=f'{message.from_user.id}_new_group_id')
    delete_by_key(key=f'{message.from_user.id}_new_group_id')
    group_name = message.text
    db.joined_a_group(table_name=message.from_user.id, group_id=group_id, group_name=group_name)
    await state.clear()
    await message.answer('Группа добавлена, чтобы добавить сообщение, отправь мне команду /add')


@form_router.message(FSM.use_old_settings)
@logger.catch
async def use_old_settings(message: types.Message, state: FSMContext):
    group_id = get_data_from_key(f'{message.from_user.id}_group_id')
    if message.text == '✅Да':
        db.run_send_messages(table_name=message.from_user.id, group_id=group_id)
        await state.clear()
        await message.answer('Сообщение добавлено в работу, для остановки нажмите /stop')
        asyncio.create_task(work_with_message(chat_id=group_id, table_name=message.from_user.id))
        return
    else:
        await state.set_state(FSM.get_group)
        db.set_remove(table_name=message.from_user.id, group_id=group_id)
        await bot.send_message(chat_id=message.chat.id, text='Старые настройки удалены')

        await state.set_state(FSM.is_repost)
        await bot.send_message(chat_id=message.chat.id, text='Это будет репост?', reply_markup=yes_no_keyboard)

        # await state.set_state(FSM.get_message)
        # await bot.send_message(chat_id=message.chat.id, text='Отправь/перешли мне сообщение')


@form_router.message(FSM.is_repost)
@logger.catch
async def is_repost(message: types.Message, state: FSMContext):
    if message.text == '✅Да':
        save_key_value(f'{message.from_user.id}_is_repost', value=True)
        # await state.set_state(FSM.will_pin_message)
        # await message.answer('Закрепляем сообщение при работе?', reply_markup=yes_no_keyboard)
    else:
        save_key_value(f'{message.from_user.id}_is_repost', value=False)
    await state.set_state(FSM.get_message)
    await bot.send_message(chat_id=message.chat.id, text='Отправь/перешли мне сообщение')


@form_router.message(FSM.get_message)
@logger.catch
async def get_message(message: types.Message, state: FSMContext):
    save_key_value(key=f'{message.chat.id}_message', value=str(message.model_dump_json().encode("utf-8")))
    save_key_value(key=f'{message.chat.id}_caption_text', value=message.md_text)
    if get_data_from_key(f'{message.from_user.id}_is_repost'):
        await state.set_state(FSM.will_pin_message)
        await message.answer('Закрепляем сообщение при работе?', reply_markup=yes_no_keyboard)
    else:
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
    r = get_data_from_key(key=f"{message.chat.id}_buttons_names")
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
    if not re.match(r'^https?://', message.text):
        await message.answer('Отправь правильную ссылку в формате\n\nhttps://www.example.com')
        return
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
    if get_data_from_key(f'{message.chat.id}_is_repost'):
        await state.set_state(FSM.timer)
        await message.answer('Отправь время, через которое нужно перезакреплять сообщения( в минутах). \n\n'
                             'Можно написать целое число или через точку, например, 0.5')
    else:
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
    if get_data_from_key(f'{message.chat.id}_is_repost'):
        db.add_all_params(
            table_name=message.from_user.id,
            group_id=get_data_from_key(f'{message.from_user.id}_group_id'),
            lock=0,
            message_text='',
            message_photo_id='',
            buttons='',
            will_pin=get_data_from_key(f'{message.chat.id}_pin_message'),
            delete_previous_messages=get_data_from_key(f'{message.chat.id}_delete_old_message'),
            will_add_tags=0,
            amount_of_tags=0,
            tag_everyone=get_data_from_key(f'{message.chat.id}_all_or_online_tags'),
            currently_in_use=1,
            timer=get_data_from_key(f'{message.chat.id}_timer'),
            message=get_data_from_key(f'{message.chat.id}_message'))

        group_id = get_data_from_key(f'{message.from_user.id}_group_id')
        delete_cache(message)

        await message.answer('Сообщение добавлено в работу, для остановки нажмите /stop')
        asyncio.create_task(work_with_message(chat_id=group_id, table_name=message.from_user.id))
        return

    if get_data_from_key(f'{message.chat.id}_buttons_names') and get_data_from_key(f'{message.chat.id}_buttons_urls'):

        for name, url in zip(
                get_data_from_key(f'{message.chat.id}_buttons_names'),
                get_data_from_key(f'{message.chat.id}_buttons_urls')):
            buttons.append({'name': name, 'url': url})
    else:

        buttons = None

    db.add_all_params(
        table_name=message.from_user.id,
        group_id=get_data_from_key(f'{message.from_user.id}_group_id'),
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
        timer=get_data_from_key(f'{message.chat.id}_timer'),
        message=get_data_from_key(f'{message.chat.id}_message'))
    db.set_save(
        table_name=message.from_user.id, group_id=get_data_from_key(f'{message.from_user.id}_group_id')
    )
    group_id = get_data_from_key(f'{message.from_user.id}_group_id')
    delete_cache(message)

    await message.answer('Сообщение добавлено в работу, для остановки нажмите /stop')
    # asyncio.run(work_with_message(group_id=group_id, table_name=message.from_user.id))
    asyncio.create_task(work_with_message(chat_id=group_id, table_name=message.from_user.id))


@logger.catch
async def work_with_message(chat_id, table_name):
    group_id = await get_chat_id(chat_id)
    data = db.get_group_by_id(group_id=chat_id, table_name=table_name)

    tags_list = await get_members_ids(chat_id=group_id, is_online=(not bool(data["tag_everyone"])))
    if get_data_from_key(f'{table_name}_is_repost'):
        while True:
            data = db.get_group_by_id(group_id=chat_id, table_name=table_name)
            will_pin = bool(data["will_pin"])
            delete_previous_messages = bool(data["delete_previous_messages"])
            timer = float(data["timer"])
            message = data["message"]

            if not data["currently_in_use"]:
                break
            # if message.forward_from_chat.id is None:
            #     if message.forward
            # for i in message:
            #     print(f'{i}')
            # logger.info(f'{message=}')
            # logger.info(f'{group_id=}')
            # logger.info(f'{message.forward_from_chat.id=}')
            # logger.info(f'{message.forward_from_message_id=}')
            # time.sleep(20)
            try:
                result = await bot.forward_message(chat_id=int(group_id),
                                                   from_chat_id=int(message.forward_from_chat.id),
                                                   message_id=int(message.forward_from_message_id)
                                                   )
            except:
                await bot.send_message(chat_id=table_name,
                                       text='Бот не состоит в канале, либо, пост выложен не от имени канала'
                                       )
                break
            if will_pin:
                await bot.pin_chat_message(chat_id=group_id, message_id=result.message_id)

            await asyncio.sleep(timer * 60)

            if will_pin:
                await bot.unpin_chat_message(chat_id=group_id, message_id=result.message_id)

            if delete_previous_messages:
                await bot.delete_message(chat_id=group_id, message_id=result.message_id)
    else:

        while True:

            data = db.get_group_by_id(group_id=chat_id, table_name=table_name)
            buttons = data["buttons"]
            will_pin = bool(data["will_pin"])
            delete_previous_messages = bool(data["delete_previous_messages"])
            will_add_tags = bool(data["will_add_tags"])
            amount_of_tags = int(data["amount_of_tags"])
            tag_everyone = bool(data["tag_everyone"])
            timer = float(data["timer"])
            message = data["message"]

            if not data["currently_in_use"]:
                break

            # Кнопки
            if buttons == '' or buttons is None:
                keyboard = None
            else:
                builder = []
                for button in buttons:
                    builder.append([InlineKeyboardButton(text=button["name"], url=button['url'])])
                keyboard = InlineKeyboardMarkup(inline_keyboard=builder)

            # Теги
            if will_add_tags:
                # tags = await get_members_ids(chat_id=group_id, is_online=(not tag_everyone))
                await asyncio.sleep(1)
                if len(tags_list) <= amount_of_tags:
                    tags_list = await get_members_ids(chat_id=group_id, is_online=(not tag_everyone))
                if tags_list is None:
                    tags = ['test']
                for i in range(amount_of_tags - len(tags_list)):
                    tags_list.append('test')
                tags = random.sample(tags_list, amount_of_tags)
                for i in tags:
                    tags_list.remove(i)
                tags_string = '\n' + ''.join(
                    [f'[ ᅠ ](tg://user?id={tag})' for tag in tags])

            else:
                tags_string = ''

            logger.info(f'{tags_string=}')

            # Текст сообщения с тегами
            message_text = message.md_text + tags_string
            if message_text == '':
                message_text = None
            result = None
            if message.text is not None:
                result = await bot.send_message(chat_id=group_id,
                                                text=message_text,
                                                reply_markup=keyboard,
                                                parse_mode="MarkdownV2"
                                                )
            elif message.voice is not None:
                result = await bot.send_voice(chat_id=group_id,
                                              voice=message.voice.file_id,
                                              caption=message_text,
                                              reply_markup=keyboard,
                                              parse_mode="MarkdownV2"
                                              )
            elif message.photo is not None:
                result = await bot.send_photo(chat_id=group_id,
                                              photo=message.photo[0].file_id,
                                              caption=message_text,
                                              reply_markup=keyboard,
                                              parse_mode="MarkdownV2"
                                              )

            elif message.video_note is not None:
                result = await bot.send_video_note(chat_id=group_id,
                                                   video_note=message.video_note.file_id,
                                                   reply_markup=keyboard
                                                   )
            elif message.animation is not None:
                result = await bot.send_animation(chat_id=group_id,
                                                  animation=message.animation.file_id,
                                                  caption=message_text,
                                                  reply_markup=keyboard,
                                                  parse_mode="MarkdownV2"
                                                  )
            elif message.document is not None:
                result = await bot.send_document(chat_id=group_id,
                                                 document=message.document.file_id,
                                                 caption=message_text,
                                                 reply_markup=keyboard,
                                                 parse_mode="MarkdownV2"
                                                 )
            elif message.video is not None:
                result = await bot.send_video(chat_id=group_id,
                                              video=message.video.file_id,
                                              caption=message_text,
                                              reply_markup=keyboard,
                                              parse_mode="MarkdownV2"
                                              )
            elif message.poll is not None:

                result = await bot.send_poll(chat_id=group_id,
                                             question=message.poll.question,
                                             options=[i.text for i in message.poll.options],
                                             is_closed=message.poll.is_closed,
                                             is_anonymous=message.poll.is_anonymous,
                                             type=message.poll.type,
                                             allows_multiple_answers=message.poll.allows_multiple_answers,
                                             correct_option_id=message.poll.correct_option_id,
                                             explanation=message.poll.explanation,
                                             explanation_entities=message.poll.explanation_entities,
                                             open_period=message.poll.open_period,
                                             close_date=message.poll.close_date
                                             )

            if will_pin:
                await bot.pin_chat_message(chat_id=group_id, message_id=result.message_id)

            await asyncio.sleep(timer * 60)

            if will_pin:
                await bot.unpin_chat_message(chat_id=group_id, message_id=result.message_id)

            if delete_previous_messages:
                await bot.delete_message(chat_id=group_id, message_id=result.message_id)


@form_router.message(Command('stop'))
@logger.catch
async def stop(message: types.Message, state: FSMContext):
    if not is_admin(message):
        await message.answer('Вы не являетесь администратором')
        return
    delete_cache(message)
    builder = []
    for i in db.get_all_groups(table_name=message.from_user.id):
        builder.append([InlineKeyboardButton(text=i["group_name"], callback_data=i['group_id'])])
    kb = InlineKeyboardMarkup(inline_keyboard=builder)
    await message.answer('Выбери группу', reply_markup=kb)
    await state.set_state(FSM_STOP.get_group)


@form_router.callback_query(FSM_STOP.get_group)
@logger.catch
async def get_and_stop_group(c_query: types.CallbackQuery, state: FSMContext):
    data = db.get_group_by_id(group_id=c_query.data, table_name=c_query.from_user.id)
    db.stop_send_messages(table_name=c_query.from_user.id, group_id=data["group_id"])
    # db.leaved_a_group(group_id=data["group_id"], table_name=c_query.from_user.id)
    # db.joined_a_group(group_id=data["group_id"], group_name=data["group_name"], table_name=c_query.from_user.id)
    await state.clear()
    await bot.send_message(chat_id=c_query.from_user.id,
                           text='Работа с сообщением приостановлена')


@form_router.message()
@logger.catch
async def add_remove_group(message: types.Message):
    for i in message:
        print(i)
    if message.new_chat_members is not None:
        get_me_coro = await bot.get_me()
        bots_username = get_me_coro.username
        usernames = [i.username for i in message.new_chat_members]
        if bots_username in usernames:
            if message.chat.type == 'supergroup':
                db.joined_a_group(
                    group_id=message.chat.id,
                    group_name=f'@{message.chat.username}',
                    table_name=message.from_user.id
                )
            else:
                db.joined_a_group(
                    group_id=message.chat.id,
                    group_name=message.chat.title,
                    table_name=message.from_user.id
                )

    elif message.left_chat_member is not None:
        get_me_coro = await bot.get_me()
        bots_username = get_me_coro.username

        if bots_username == message.left_chat_member.username:
            db.leaved_a_group(group_id=message.chat.id, table_name=message.from_user.id)

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
