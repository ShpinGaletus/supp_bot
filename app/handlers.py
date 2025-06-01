from aiogram import F, Router
from aiogram.types import Message,CallbackQuery
from aiogram.filters import Command

from .database import (get_categories, get_category_name_by_id, get_questions_by_category,\
    get_answer, get_question_by_id, log_user_action)
from .keyboards import categories_keyboard, questions_keyboard
import app.globals as g 

router = Router()

@router.message(Command('start'))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id in g.OPERATORS:
        await message.answer('Здравствуйте, оператор!')
    elif user_id in g.ADMINS:
        await message.answer('Здравствуйте, администратор!')
    else:
        await message.answer('Вас приветствует КиберБот КиберПоддержки!\n' \
        'Ниже представлен список популярных категорий вопросов. Просто нажмите нужную вам!')
        await log_user_action(user_id, "start")
        categories = await get_categories()
        keyboard = categories_keyboard(categories)
        await message.answer("Популярные категории:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("category_"))
async def process_category(callback: CallbackQuery):
    user_id = callback.from_user.id
    category_id = int(callback.data.split("_")[-1])

    await log_user_action(user_id, "choose_category", category_id=category_id)

    category_name = await get_category_name_by_id(category_id)
    questions = await get_questions_by_category(category_id)
    if not questions:
        await callback.message.answer(f"В категории «{category_name}» пока нет вопросов.")
    else:
        keyboard = questions_keyboard(questions)
        await callback.message.answer(
            f"Вы выбрали категорию «{category_name}».\nВыберите вопрос:", 
            reply_markup=keyboard
        )
    await callback.answer()

@router.callback_query(F.data.startswith("question_"))
async def process_question(callback: CallbackQuery):
    user_id = callback.from_user.id
    faq_id = int(callback.data.split("_")[-1])

    await log_user_action(user_id, "choose_question", faq_id=faq_id)

    question = await get_question_by_id(faq_id)
    answer = await get_answer(faq_id)
    sent_mesage = await callback.message.answer(f'Выбран вопрос:\n{question}')

    await callback.message.answer(answer,reply_to_message_id=sent_mesage.message_id)
    await callback.answer()


@router.message(Command('help'))
async def cmd_help(message: Message):
    user_id = message.from_user.id

    await log_user_action(user_id, "help")
    await message.answer('Вы нажмали на help')

