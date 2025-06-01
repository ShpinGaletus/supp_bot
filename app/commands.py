from aiogram.types import BotCommand,  BotCommandScopeDefault, BotCommandScopeChat
import app.globals as g

BASE_COMMANDS = [
    BotCommand(command='start', description='Начать'),
    BotCommand(command='help', description='Помощь')
]

OPERATOR_COMMANDS = BASE_COMMANDS + [
    BotCommand(command='list', description='Просмотр категорий и вопросов'),
]

ADMIN_COMMANDS = [
    BotCommand(command='list', description='Просмотр категорий и вопросов'),
    BotCommand(command='cat_manage', description='Добавление/Удаление категории'),
    BotCommand(command='question_manage', description='Добавление/Удаление вопроса'),    
    BotCommand(command='question_add', description='Добавить вопрос'),
    BotCommand(command='question_remove', description='Удалить вопрос'),
    BotCommand(command='cancel', description='Отмена действия')

]
async def set_users_commands(bot):
    await bot.set_my_commands(BASE_COMMANDS, scope=BotCommandScopeDefault())

async def set_operators_commands(bot):
    print(f'Loaded operators: {g.OPERATORS}')
    for operator_id in g.OPERATORS:
        scope = BotCommandScopeChat(chat_id=operator_id)
        await bot.set_my_commands(OPERATOR_COMMANDS, scope=scope)

async def set_admins_commands(bot):
    commands = BASE_COMMANDS + ADMIN_COMMANDS
    print(f'Loaded admins: {g.ADMINS}')
    for admin_id in g.ADMINS:
        scope = BotCommandScopeChat(chat_id=admin_id)
        await bot.set_my_commands(commands, scope=scope)