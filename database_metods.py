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
        lock INTEGER,
        timer REAL
        
        )
         ''')
        self.conn.commit()

    def joined_a_group(self, group_id, group_name):
        with self.lock:
            self.cur.execute('''
            INSERT INTO groups (
            group_id, group_name,lock, message_text, message_photo_id,
             buttons, will_pin, delete_previous_messages, will_add_tags,
              amount_of_tags, tag_everyone, currently_in_use, timer
              )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                             (group_id, group_name, 0, '', '', '', 0, 0, 0, 0, 0, 0, 0.0))
            self.conn.commit()

    def leaved_a_group(self, group_id):
        with self.lock:
            self.cur.execute("""DELETE FROM groups WHERE group_id = ?""", (group_id,))
            self.conn.commit()

    def set_lock(self, group_id, lock):
        with self.lock:
            self.conn.execute("""UPDATE groups SET lock = ? WHERE group_id = ?""", (lock, group_id))
            self.conn.commit()

    def add_all_params(self, group_id: str, lock: int, message_text: str,
                       message_photo_id: str, buttons: str, will_pin: int,
                       delete_previous_messages: int, will_add_tags: int,
                       amount_of_tags: int, tag_everyone: int,
                       currently_in_use: int, timer: float):
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
                       currently_in_use = ?,
                       timer = ?
                   WHERE group_id = ?
               """, (lock, message_text, message_photo_id, buttons, will_pin,
                     delete_previous_messages, will_add_tags, amount_of_tags, tag_everyone,
                     currently_in_use, timer, group_id))
            self.conn.commit()

    def get_all_groups(self):
        with self.lock:
            rows = self.conn.execute("SELECT * FROM groups").fetchall()

        groups = []
        for row in rows:
            group = {
                "group_id": row[0],
                "currently_in_use": row[1],
                "group_name": row[2],
                "message_text": row[3],
                "message_photo_id": row[4],
                "buttons": eval(row[5]),
                "will_pin": bool(row[6]),
                "delete_previous_messages": bool(row[7]),
                "will_add_tags": bool(row[8]),
                "amount_of_tags": row[9],
                "tag_everyone": bool(row[10]),
                "lock": row[11],
                "timer": float(row[12])
            }
            groups.append(group)

        return groups

    def get_group_by_id(self, group_id):
        with self.lock:
            row = self.conn.execute(
                "SELECT * FROM groups WHERE group_id = ?", (group_id,)
            ).fetchone()
            if row:
                group = {
                    "group_id": row[0],
                    "currently_in_use": row[1],
                    "group_name": row[2],
                    "message_text": row[3],
                    "message_photo_id": row[4],
                    "buttons": eval(row[5]),
                    "will_pin": bool(row[6]),
                    "delete_previous_messages": bool(row[7]),
                    "will_add_tags": bool(row[8]),
                    "amount_of_tags": row[9],
                    "tag_everyone": bool(row[10]),
                    "lock": row[11],
                    "timer": float(row[12])
                }
            else:
                group = None
        return group


if __name__ == '__main__':
    db = Database()
    for i in db.get_all_groups():
        print(i)
