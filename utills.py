import shelve
import sqlite3
import threading
from typing import Any

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from loguru import logger

logger.add(
    'logs/logs.log',
    format='{time} {level} {message}',
    level='DEBUG'
)

shelf = shelve.open('Database/cache')


@logger.catch
def save_key_value(key: str, value: Any):
    shelf[key] = value
    shelf.sync()


@logger.catch
def get_data_from_key(key: str) -> Any | bool:
    try:
        return shelf[key]
    except KeyError:
        return False


@logger.catch
def delete_by_key(key: str):
    try:
        shelf.pop(key)
    except KeyError:
        return False


yes_no_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='✅Да'), KeyboardButton(text='❌нет')]],
    resize_keyboard=True,
    one_time_keyboard=True
)
continue_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='✅Продолжить')]],
    resize_keyboard=True,
    one_time_keyboard=True
)


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('Database/admins.sqlite3')
        self.cur = self.conn.cursor()
        self.lock = threading.Lock()
        self.cur.execute("CREATE TABLE IF NOT EXISTS admins(admin_tg_user_id TEXT)")

    def add_admin(self, admin_tg_user_id: str):
        with self.lock:
            self.cur.execute(f"INSERT INTO admins VALUES('{admin_tg_user_id}')")
            self.conn.commit()

    def delete_admin(self, admin_tg_user_id: str):
        with self.lock:
            self.cur.execute(f"DELETE FROM admins WHERE admin_tg_user_id = '{admin_tg_user_id}'")
            self.conn.commit()

    def get_admins(self):
        with self.lock:
            self.cur.execute("SELECT * FROM admins")
            res = self.cur.fetchall()
            admins = []
            for admin in res:
                admins.append(admin[0])
            if admins == []:
                return None
            return admins
