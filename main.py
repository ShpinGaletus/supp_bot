import os
from dotenv import load_dotenv

import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, BotCommand
from aiogram.filters import Command

from app.handlers import router
from app.database import create_db_pool

load_dotenv()

TOKEN = os.getenv("API_TOKEN")

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    commands = [
        BotCommand(command='start',description='Начать'),
        BotCommand(command='help',description='Помощь')
    ]
    await bot.set_my_commands(commands)
    
    await create_db_pool()
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')