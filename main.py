import asyncio
from aiogram import Dispatcher

from app.handlers import router as handlers_router
from app.chat import router as chat_router
from app.admin_handlers import router as admin_router
from app.database import create_db_pool
from app.globals import load_roles
from app.commands import set_users_commands, set_admins_commands, set_operators_commands
from loader import bot, storage

async def main():
    await create_db_pool()
    await load_roles()

    dp = Dispatcher(bot=bot,storage=storage)
    dp.include_router(handlers_router)
    dp.include_router(admin_router)
    dp.include_router(chat_router)

    await set_users_commands(bot)
    await set_operators_commands(bot)
    await set_admins_commands(bot)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')