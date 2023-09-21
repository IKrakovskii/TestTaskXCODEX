import ast
import json
import sqlite3
import threading
from aiogram import types

from other import logger


class Database:
    @logger.catch
    def __init__(self):
        self.conn = sqlite3.connect('Database/GROUPS.sqlite3')
        self.cur = self.conn.cursor()
        self.lock = threading.Lock()

    def create_admin_table(self, table_name):
        self.cur.execute(f'''
                CREATE TABLE IF NOT EXISTS table_{table_name}(
                group_id TEXT,
                currently_in_use INTEGER,
                group_name TEXT,
                message_text TEXT,
                message_photo_id TEXT,
                buttons TEXT,
                will_pin INTEGER,
                delete_previous_messages INTEGER,
                will_add_tags INTEGER,
                amount_of_tags INTEGER,
                tag_everyone INTEGER,
                lock INTEGER,
                timer REAL,
                message TEXT,
                save INTEGER

                )''')
        self.conn.commit()

    def joined_a_group(self, table_name, group_id, group_name):
        self.create_admin_table(table_name=table_name)
        with self.lock:
            self.cur.execute(f'''
            INSERT INTO table_{table_name} (
            group_id, group_name,lock, message_text, message_photo_id,
             buttons, will_pin, delete_previous_messages, will_add_tags,
              amount_of_tags, tag_everyone, currently_in_use, timer, message, save
              )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                             (group_id, group_name, 0, '', '', 'None', 0, 0, 0, 0, 0, 0, 0.0, b'', 0))
            self.conn.commit()

    def leaved_a_group(self, table_name, group_id):
        with self.lock:
            self.cur.execute(f"""DELETE FROM table_{table_name} WHERE group_id = ?""", (group_id,))
            self.conn.commit()

    def set_lock(self, table_name, group_id, lock):
        with self.lock:
            self.conn.execute(f"""UPDATE table_{table_name} SET lock = ? WHERE group_id = ?""",
                              (lock, group_id))
            self.conn.commit()

    def set_save(self, table_name, group_id):
        with self.lock:
            self.conn.execute(f"""UPDATE table_{table_name} SET save = ? WHERE group_id = ?""",
                              (1, group_id))
            self.conn.commit()

    def set_remove(self, table_name, group_id):
        with self.lock:
            self.conn.execute(f"""UPDATE table_{table_name} SET save = ? WHERE group_id = ?""",
                              (0, group_id))
            self.conn.commit()

    def stop_send_messages(self, table_name, group_id):
        with self.lock:
            self.conn.execute(f"""UPDATE table_{table_name} SET currently_in_use = ? WHERE group_id = ?""",
                              (0, group_id))
            self.conn.commit()

    def run_send_messages(self, table_name, group_id):
        with self.lock:
            self.conn.execute(f"""UPDATE table_{table_name} SET currently_in_use = ? WHERE group_id = ?""",
                              (1, group_id))
            self.conn.commit()

    def add_all_params(self, table_name, group_id: str, lock: int, message_text: str,
                       message_photo_id: str, buttons: str, will_pin: int,
                       delete_previous_messages: int, will_add_tags: int,
                       amount_of_tags: int, tag_everyone: int,
                       currently_in_use: int, timer: float, message):
        with self.lock:
            self.cur.execute(f"""
                   UPDATE table_{table_name}
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
                       message = ?,
                       timer = ?
                   WHERE group_id = ?
               """, (lock, message_text, message_photo_id, buttons, will_pin,
                     delete_previous_messages, will_add_tags, amount_of_tags, tag_everyone,
                     currently_in_use, message, timer, group_id))
            self.conn.commit()

    def get_all_groups(self, table_name):
        with self.lock:
            rows = self.conn.execute(f"SELECT * FROM table_{table_name}").fetchall()

        groups = []
        for row in rows:
            group = {
                "group_id": row[0],
                "currently_in_use": bool(row[1]),
                "group_name": row[2],
                "message_text": row[3],
                "message_photo_id": row[4],
                "buttons": eval(row[5]) if row[5] != '' else None,
                "will_pin": bool(row[6]),
                "delete_previous_messages": bool(row[7]),
                "will_add_tags": bool(row[8]),
                "amount_of_tags": row[9],
                "tag_everyone": bool(row[10]),
                "lock": bool(row[11]),
                "timer": max(0.5, float(row[12])),
                "message": types.Message.model_validate_json((eval(row[13]))) if row[13] != b'' else None
            }
            groups.append(group)

        return groups

    def get_group_by_id(self, table_name, group_id):
        with self.lock:
            row = self.conn.execute(
                f"SELECT * FROM table_{table_name} WHERE group_id = ?", (group_id,)
            ).fetchone()
            if row:
                group = {
                    "group_id": row[0],
                    "currently_in_use": bool(row[1]),
                    "group_name": row[2],
                    "message_text": row[3],
                    "message_photo_id": row[4],
                    "buttons": eval(row[5]) if row[5] != '' else None,
                    "will_pin": bool(row[6]),
                    "delete_previous_messages": bool(row[7]),
                    "will_add_tags": bool(row[8]),
                    "amount_of_tags": row[9],
                    "tag_everyone": bool(row[10]),
                    "lock": row[11],
                    "timer": max(0.5, float(row[12])),
                    "message": types.Message.model_validate_json((eval(row[13]))) if row[13] != b'' else None,
                    "save": bool(row[14])
                }
            else:
                group = None
        return group
