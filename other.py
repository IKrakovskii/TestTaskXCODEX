import dbm
import shelve
from loguru import logger


logger.add(
    'logs/logs.log',
    format='{time} {level} {message}',
    level='DEBUG'
)

shelf = shelve.open('Database/cache')
shelf_arr = shelve.open('Database/array')


def save_key_value(key, value):
    shelf[key] = value
    shelf.sync()


def get_data_from_key(key):
    try:
        return shelf[key]
    except:
        return False


def delete_by_key(key):
    shelf.pop(key)


'''
невидимые теги

await bot.send_photo(
        chat_id=message.chat.id,
        photo=message.photo[0].file_id,
        caption=f'{message.caption if message.text is None else message.text}'
                f'\n[ ᅠ ]({teg1})[ ᅠ ]({teg2})[ ᅠ ]({teg3})[ ᅠ ]({teg4})[ ᅠ ]({teg5})',
        parse_mode='Markdown'
    )

'''