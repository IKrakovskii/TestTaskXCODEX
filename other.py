import asyncio
import dbm
import shelve
import sqlite3
import threading
import time
from typing import List

from aiogram import Bot
from loguru import logger
from CONFIG import TOKEN

bot = Bot(token=TOKEN)
# region конфиг для логирования
logger.add(
    'logs/logs.log',
    format='{time} {level} {message}',
    level='DEBUG'
)

# endregion

# region БД ключ-значение
db = dbm.open('Database/cache.db', 'c')
shelf = shelve.Shelf(db)


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


# endregion


# region БД для хранения ссылок
class Database:
    @logger.catch
    def __init__(self):
        self.conn = sqlite3.connect('Database/urls.sqlite3')
        self.cur = self.conn.cursor()
        self.lock = threading.Lock()
        # Создание таблицы
        self.cur.execute('''CREATE TABLE IF NOT EXISTS urls
                          (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          url TEXT NOT NULL,
                          timer INTEGER NOT NULL,
                          time INTEGER NOT NULL 
                          )''')
        self.conn.commit()

    @logger.catch
    def url_exists(self, url):
        self.cur.execute("SELECT * FROM urls WHERE url=?", (url,))
        return self.cur.fetchone() is not None

    @logger.catch
    def insert_data(self, url, timer):
        if not self.url_exists(url):
            self.cur.execute('''
            INSERT INTO urls (url, timer, time) VALUES (?, ?, ?)''', (
                url, timer, int(time.time())
            )
                             )
            self.conn.commit()

    @logger.catch
    def update_time_by_url(self, url: str):
        self.cur.execute("SELECT id, timer FROM urls WHERE url=?", (url,))
        row = self.cur.fetchone()
        url_id, timer = row
        new_time = int(time.time() + timer * 60 + 5)
        self.cur.execute("UPDATE urls SET time=? WHERE id=?",
                         (new_time, url_id))
        self.conn.commit()

    @logger.catch
    def get_all_urls(self) -> List[dict]:
        """
        :return: [{'url': str, 'timer': int}]
        """
        self.cur.execute('''SELECT * FROM urls''')
        rows = self.cur.fetchall()
        out_lst = []
        for row in rows:
            out_lst.append({'url': row[1], 'timer': row[2], 'time': row[3]})
        return out_lst


# endregion

# region добавление ссылки в очередь
class Queue(Database):
    @staticmethod
    @logger.catch
    async def pin_message(bot, message_id, chat_id, timer):
        try:
            r = await bot.pin_chat_message(
                message_id=message_id,
                chat_id=chat_id,
                disable_notification=True
            )
            logger.info(f'результат закрепления сообщения: {message_id} {r}')
            await asyncio.sleep(timer * 60 + 1)
            r = await bot.unpin_chat_message(
                message_id=message_id,
                chat_id=chat_id
            )
            logger.info(f'результат открепления сообщения: {message_id} {r}')
            return False
        except Exception as e:
            logger.error(e)
            return True

    @logger.catch
    async def cyclic_consolidation(self, bot):
        while True:
            for i in self.get_all_urls():
                url, timer, time_to_send = i['url'], i['timer'], i['time']
                # print(url)
                # print(time_to_send)
                # print(int(time.time()))
                if int(time_to_send) + 1 >= int(time.time()):
                    continue
                logger.debug(f'пошло закрепляться сообщение{url}')
                data = url.split('/')
                chat_id, message_id = f'-100{data[-2]}', data[-1]
                try:
                    chat_id = int(chat_id)
                except ValueError:
                    chat_id = f"@{chat_id.replace('-100', '')}"
                except Exception as e:
                    logger.error(e)
                # asyncio.create_task(self.pin_message(bot, message_id=message_id, chat_id=chat_id, timer=timer))
                logger.debug('Закрепляю сообщение')
                logger.debug(f'{time_to_send=}')
                logger.debug(f'{time.time()=}')
                await self.pin_message(bot, message_id, chat_id, timer)
                self.update_time_by_url(url=url)
                logger.debug(f'Сообщение {url} закреплено\n')


# end region

if __name__ == '__main__':
    logger.info('Функция по закрепу сообщений, начала работу')
    Q = Queue()
    asyncio.run(Q.cyclic_consolidation(bot))
