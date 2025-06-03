from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import F, Router
from aiogram.types import Message,CallbackQuery,InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from .database import (get_categories, get_category_name_by_id, get_questions_by_category,\
    get_question_by_id, category_add, category_exists, category_remove, question_add, question_remove, question_exists)
from .keyboards import categories_keyboard, questions_keyboard 
import app.globals as g 

router = Router()

class AdminStates(StatesGroup):
    cat_name_waiting = State()
    question_add_text_waiting = State()
    question_add_answer_waiting = State() 
    question_remove_waiting = State()
  
@router.message(Command('list'))
async def list_categories(message:Message):
    user_id = message.from_user.id
    if user_id in g.ADMINS or user_id in g.OPERATORS:
        categories = await get_categories()
        if not categories:
            await message.answer('Категорий пока нет')
            return
        keyboard = categories_keyboard(categories, prefix='list_cat')
        await message.answer('Выберите категорию, если хотите посмотреть список вопросов', reply_markup=keyboard)
    else:
        return

@router.callback_query(F.data.startswith("list_cat_"))
async def list_questions(callback: CallbackQuery):
    cat_id = int(callback.data.split('_')[-1])
    cat_name = await get_category_name_by_id(cat_id)
    questions = await get_questions_by_category(cat_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад к категориям", callback_data="list_back")]
    ])

    if not questions:
        await callback.message.edit_text(f'В категории «{cat_name}» пока нет вопросов', reply_markup=keyboard)
        await callback.answer()
        return
    
    text = "Вопросы в категории:\n" + "\n".join(f"{q['id']}: {q['question']}" for q in questions)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == 'list_back')
async def back_to_cats(callback: CallbackQuery):
    categories = await get_categories()
    keyboard = categories_keyboard(categories, prefix='list_cat')
    await callback.message.edit_text('Выберите категорию', reply_markup=keyboard)
    await callback.answer()

@router.message(Command('cat_manage'))
async def manage_cat(message: Message):
    user_id = message.from_user.id
    if user_id in g.ADMINS:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Добавить категорию", callback_data="cat_add")],
            [InlineKeyboardButton(text="Удалить категорию", callback_data="cat_remove")]
        ])
        await message.answer('Выберите действие', reply_markup=keyboard)
    else:
        return

@router.callback_query(F.data =='cat_add')
async def admin_cat_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите название категории для добавления')
    await state.set_state(AdminStates.cat_name_waiting)
    await callback.answer()

@router.message(AdminStates.cat_name_waiting, ~F.text.startswith('/'))
async def process_cat_name(message: Message, state: FSMContext):
    cat_name = message.text.strip() if message.text else ""
    if not cat_name or cat_name.startswith('/'):
        await message.answer(f'Название категории не может начинаться со / или быть пустым')
        return
    if await category_exists(cat_name):
        await message.answer(f'Такая категория уже существует, введите другое название или /cancel для отмены')
        return
    cat_id = await category_add(cat_name)
    await message.answer(f'Категория «{cat_name}» успешно добавлена с id {cat_id}"')
    await state.clear()

@router.callback_query(F.data == "cat_remove")
async def cat_remove(callback: CallbackQuery):
    categories = await get_categories()
    keyboard = categories_keyboard(categories, prefix='remove_cat')
    await callback.message.answer('Выберите категорию для удаления', reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith('remove_cat_'))
async def cat_remove_confirm(callback: CallbackQuery):
    cat_id = int(callback.data.split('_')[-1])
    cat_name = await get_category_name_by_id(cat_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Да', callback_data=f'confirm_remove_cat_{cat_id}'),
            InlineKeyboardButton(text='Нет', callback_data='cancel_remove_cat')
        ]
    ])
    await callback.message.edit_text(f'Вы точно хотите удалить категорию «{cat_name}»?', reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith('confirm_remove_cat_'))
async def remove_cat(callback: CallbackQuery):
    cat_id = int(callback.data.split('_')[-1])
    cat_name = await get_category_name_by_id(cat_id)
    await category_remove(cat_id)
    await callback.message.edit_text(f'Категория «{cat_name}» успешно удалена', reply_markup=None)
    await callback.answer()

@router.callback_query(F.data == 'cancel_remove_cat')
async def cancel_remove_cat(callback: CallbackQuery):
    await callback.message.edit_text('Удаление категории отменено', reply_markup=None)
    await callback.answer()

@router.message(Command('question_manage'))
async def question_manage(message: Message):
    user_id = message.from_user.id
    if user_id not in g.ADMINS:
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить вопрос", callback_data="quest_add")],
    [InlineKeyboardButton(text="Удалить вопрос", callback_data="quest_remove")]])
    await message.answer('Выберите действие', reply_markup=keyboard)

@router.callback_query(F.data == 'quest_add')
async def question_add_start(callback: CallbackQuery, state: FSMContext):
    categories = await get_categories()
    keyboard = categories_keyboard(categories, prefix='quest_add_cat')
    await callback.message.answer('Выберите категорию для добавления вопроса:', reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith('quest_add_cat_'))
async def question_add_text(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split('_')[-1])
    await state.update_data(category_id=cat_id)
    await callback.message.edit_text('Введите текст вопроса', reply_markup=None)
    await state.set_state(AdminStates.question_add_text_waiting)
    await callback.answer()

@router.message(AdminStates.question_add_text_waiting, ~F.text.startswith('/'))
async def question_add_asnwer(message: Message, state: FSMContext):
    question_text = message.text.strip()
    if not question_text:
        await message.answer('Вопрос не может быть пустым')
        return
    if await question_exists(question_text):
        await message.answer('Такой вопрос уже существует')
        return
    await state.update_data(question_text=question_text)
    await message.answer('Введите ответ на вопрос')
    await state.set_state(AdminStates.question_add_answer_waiting)

@router.message(AdminStates.question_add_answer_waiting, ~F.text.startswith('/'))
async def question_add_end(message: Message, state: FSMContext):
    answer_text = message.text.strip()
    if not answer_text:
        await message.answer('Ответ не может быть пустым')
        return
    data = await state.get_data()
    cat_id = data.get('category_id')
    question_text = data.get('question_text')
    question_id = await question_add(cat_id, question_text, answer_text)
    await message.answer(f'Вопрос успешно добавлен с id {question_id}')
    await state.clear()

@router.callback_query(F.data == 'quest_remove')
async def question_remove_start(callback:CallbackQuery):
    categories = await get_categories()
    keyboard = categories_keyboard(categories, prefix='remove_question_cat')
    await callback.message.answer('Выберите категорию для удаления вопроса', reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith('remove_question_cat_'))
async def question_remove_questions_show(callback: CallbackQuery):
    cat_id = int(callback.data.split('_')[-1])
    questions = await get_questions_by_category(cat_id)
    if not questions:
        await callback.message.answer('В этой категории нет вопросов')
        await callback.answer()
        return
    keyboard = questions_keyboard(questions, prefix='remove_question')
    await callback.message.edit_text('Выберите вопрос для удаления', reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith('remove_question_'))
async def question_remove_confirm(callback: CallbackQuery):
    question_id = int(callback.data.split('_')[-1])
    question_text = await get_question_by_id(question_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Да', callback_data=f'confirm_question_remove_{question_id}'),
            InlineKeyboardButton(text='Нет', callback_data='cancel_question_remove')
        ]
    ])
    await callback.message.edit_text(f'Вы точно хотите удалить вопрос «{question_text}»?', reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith('confirm_question_remove_'))
async def remove_question(callback: CallbackQuery):
    question_id = int(callback.data.split('_')[-1])
    question_name = await get_question_by_id(question_id)
    await question_remove(question_id)
    await callback.message.edit_text(f'Вопрос «{question_name}» успешно удален', reply_markup=None)
    await callback.answer()

@router.callback_query(F.data == 'cancel_question_remove')
async def cancel_remove_question(callback: CallbackQuery):
    await callback.message.edit_text('Удаление вопроса отменено', reply_markup=None)
    await callback.answer()

@router.message(Command('cancel'))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer('Нет действий для отмены')
        return
    await state.clear()
    await message.answer('Действие отменено')
    