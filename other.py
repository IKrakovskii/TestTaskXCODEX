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


# def get_group_array():
#     if shelf_arr.get('groups_array') is None:
#         shelf_arr['groups_array'] = []
#     return shelf_arr.get('groups_array')
#
#
# def update_group_array(new_value):
#     shelf_arr['groups_array'] = new_value
