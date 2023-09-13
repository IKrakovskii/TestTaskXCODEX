import sqlite3
import threading
from other import logger


class Database:
    @logger.catch
    def __init__(self):
        self.conn = sqlite3.connect('Database/DB.db')
        self.cur = self.conn.cursor()
        self.lock = threading.Lock()

        self.cur.execute('''
        CREATE TABLE IF NOT EXISTS groups(
        group_id INTEGER,
        currently_ in_use INTEGER,
        group_name TEXT,
        message_text TEXT,
        message_photo_id TEXT,
        buttons TEXT,
        will_pin INTEGER,
        delete_previous_messages INTEGER,
        will_add_tags INEGER,
        amount_of_tags INTEGER,
        tag_everyone INTEGER
        )
         ''')


db = Database()
