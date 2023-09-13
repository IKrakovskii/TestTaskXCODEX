import sqlite3
import threading
from other import logger


class Database:
    @logger.catch
    def __init__(self):
        self.conn = sqlite3.connect('Database/GROUPS.sqlite3')
        self.cur = self.conn.cursor()
        self.lock = threading.Lock()

        self.cur.execute('''
        CREATE TABLE IF NOT EXISTS groups(
        group_id TEXT,
        currently_in_use INTEGER,
        group_name TEXT,
        message_text TEXT,
        message_photo_id TEXT,
        buttons TEXT,
        will_pin INTEGER,
        delete_previous_messages INTEGER,
        will_add_tags INEGER,
        amount_of_tags INTEGER,
        tag_everyone INTEGER,
        lock INTEGER
        
        )
         ''')
        self.conn.commit()

    def joined_a_group(self, group_id, group_name):
        with self.lock:
            self.cur.execute('''
            INSERT INTO groups (
            group_id, group_name,lock, message_text, message_photo_id,
             buttons, will_pin, delete_previous_messages, will_add_tags,
              amount_of_tags, tag_everyone, currently_in_use
              )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', (group_id, group_name, 0, '', '', '', 0, 0, 0, 0, 0, 0))
            self.conn.commit()

    def leaved_a_group(self, group_id):
        with self.lock:
            self.cur.execute("""DELETE FROM groups WHERE group_id = ?""", (group_id,))

    def set_lock(self, group_id, lock):
        with self.lock:
            self.conn.execute("""UPDATE groups SET lock = ? WHERE group_id = ?""", (lock, group_id))
            self.conn.commit()

    def add_all_params(self, group_id, lock, message_text, message_photo_id,
                       buttons, will_pin, delete_previous_messages, will_add_tags,
                       amount_of_tags, tag_everyone, currently_in_use):
        with self.lock:
            self.cur.execute("""
                   UPDATE groups
                   SET 
                       lock = ?,
                       message_text = ?,
                       message_photo_id = ?,
                       buttons = ?,
                       will_pin = ?,
                       delete_previous_messages = ?,
                       will_add_tags = ?,
                       amount_of_tags = ?,
                       tag_everyone = ?,
                       currently_in_use = ?
                   WHERE group_id = ?
               """, (lock, message_text, message_photo_id, buttons, will_pin,
                     delete_previous_messages, will_add_tags, amount_of_tags, tag_everyone,
                     currently_in_use, group_id))


# INSERT INTO groups (group_id, group_name, lock)
db = Database()
db.joined_a_group(group_id=1234, group_name='Саня гей')
