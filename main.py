import os
import logging

import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, BotCommand



from app.handlers import router as handlers_router
from app.chat import router as chat_router
from app.database import create_db_pool
from loader import bot, storage

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    await create_db_pool()

    dp = Dispatcher(bot=bot,storage=storage)
    dp.include_router(handlers_router)
    dp.include_router(chat_router)

    commands = [
        BotCommand(command='start',description='Начать'),
        BotCommand(command='help',description='Помощь')
    ]
    await bot.set_my_commands(commands)
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')