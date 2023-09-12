import asyncio

from pyrogram import Client
from other import logger

api_id = 26106217
api_hash = "0de43b316dabff6f00d3e6466819dc23"
bot_token = "6654710163:AAFTGt7Xs_rBtfzd4kYGONRMhZBu1NJAQwM"

chat_id = -1001808942715


async def main():
    async with Client(name="my_bot", bot_token=bot_token, api_id=api_id, api_hash=api_hash) as app:
        chat_members = []
        await app.start()
        async for member in app.get_chat_members(chat_id):
            chat_members = chat_members + [member.user.id]
        await app.stop()
        logger.info(f'{chat_members=}')
        return chat_members


asyncio.run(main())
