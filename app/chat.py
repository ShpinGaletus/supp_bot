from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
ReplyKeyboardRemove)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from collections import deque
from .database import log_user_action, log_chat_message
import app.globals as g 

from loader import bot, storage

router = Router()

class SupportChat(StatesGroup):
    confirm_waiting = State()
    question_waiting = State()
    operator_accept_waiting = State()
    chatting = State()

waiting_questions = deque()

async def get_free_operator():
    for _ in range(len(g.operator_queue)):
        operator_id = g.operator_queue[0]
        operator_key = StorageKey(bot_id=bot.id, user_id=operator_id, chat_id=operator_id)
        state = await storage.get_state(operator_key)
        if state != SupportChat.chatting:
            g.operator_queue.rotate(-1)
            return operator_id
    return None


end_chat_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Завершить чат')]], resize_keyboard=True, one_time_keyboard=True)

@router.callback_query(F.data == 'another_question')
async def ask_user_confirm(callback: CallbackQuery, state: FSMContext):
    user_key = StorageKey(bot_id=bot.id, user_id=callback.from_user.id, chat_id=callback.from_user.id)
    current_state = await storage.get_state(user_key)
    if current_state == SupportChat.chatting:
        await callback.answer('Сначала завершите текущий чат с оператором!')
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Да', callback_data='start_chat_yes'),
            InlineKeyboardButton(text='Нет', callback_data='start_chat_no')
        ]
    ])
    await callback.message.answer('Хотите начать чат с оператором?', reply_markup=keyboard)
    await state.set_state(SupportChat.confirm_waiting)
    await callback.answer()

@router.callback_query(F.data == 'start_chat_yes', SupportChat.confirm_waiting)
async def ask_user_question(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)

    await log_user_action(callback.from_user.id, "chat_request")

    await callback.message.answer('Перед началом чата, пожалуйста, опишите свой вопрос.\n' \
    'Мы передадим его оператору')
    await state.set_state(SupportChat.question_waiting)
    await callback.answer()
    
@router.callback_query(F.data == 'start_chat_no', SupportChat.confirm_waiting)
async def cancel_chat(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer('Обращение к оператору отменено')
    await state.clear()
    await callback.answer()

async def send_question_to_operator(operator_id, user_id, user_name, question_text):
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Принять', callback_data=f'accept_chat_{user_id}')
    ]])

    await bot.send_message(
        operator_id,
          f'Новый вопрос от {user_name} (id {user_id}):\n\n{question_text}',
          reply_markup=keyboard
    )

@router.message(SupportChat.question_waiting)
async def handle_new_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.full_name or message.from_user.username or str(user_id)
    question_text = message.text

    await log_user_action(user_id, "ask_question", another_question=question_text)
    await state.update_data(user_id=user_id, question=question_text)

    operator_id = await get_free_operator()
    if operator_id is not None:
        await send_question_to_operator(operator_id, user_id, user_name, question_text)
        await state.set_state(SupportChat.operator_accept_waiting)
        await message.answer("Ваш вопрос отправлен оператору. Ожидайте")
    else:
        waiting_questions.append({
            'user_id': user_id,
            'user_name': user_name,
            'question': question_text,
        })
        await message.answer('Все операторы сейчас заняты.\nКак только появится свободный оператор, мы передадим ему ваш вопрос.')

async def process_waiting_questions():
    if not waiting_questions:
        return
    operator_id = await get_free_operator()
    if operator_id is None:
        return
    next_question = waiting_questions.popleft()
    user_id = next_question['user_id']
    user_name = next_question['user_name']
    question_text = next_question['question']

    user_state = FSMContext(
        storage=storage,
        key=StorageKey(bot_id=bot.id, user_id=user_id, chat_id=user_id)
    )

    await send_question_to_operator(operator_id, user_id, user_name, question_text)
    await user_state.set_state(SupportChat.operator_accept_waiting)
    await bot.send_message(user_id, 'Оператор освободился и получил ваш вопрос. Ожидайте')

@router.callback_query(F.data.startswith('accept_chat_'))
async def operator_accept_chat(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split('_')[-1])
    operator_id = callback.from_user.id

    user_key = StorageKey(bot_id=bot.id, user_id=user_id, chat_id=user_id)

    current_state = await storage.get_state(user_key)
    if current_state == SupportChat.chatting:
        await callback.answer('Вы уже приняли запрос данного пользователя.', show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return
    
    operator_key = StorageKey(bot_id=bot.id, user_id=operator_id, chat_id=operator_id)
    current_operator_state = await storage.get_state(operator_key)
    if current_operator_state == SupportChat.chatting:
        await callback.answer('Сначала завершите текущий чат.', show_alert=True)
        return
    
    chat_start_id = await log_user_action(user_id, "chat_start")

    await storage.update_data(user_key, {'operator_id': operator_id, 'chat_start_id': chat_start_id})
    await storage.set_state(user_key, SupportChat.chatting)
    

    await storage.update_data(operator_key, {'user_id': user_id, 'chat_start_id': chat_start_id})
    await storage.set_state(operator_key, SupportChat.chatting)

    await state.update_data(user_id=user_id)
    await state.set_state(SupportChat.chatting)

    await callback.message.edit_reply_markup(reply_markup=None)

    await bot.send_message(user_id, 'Оператор подключился к чату', reply_markup=end_chat_kb)
    await callback.message.answer('Вы начали чат с пользователем', reply_markup=end_chat_kb)
    await callback.answer()

@router.message(F.text == 'Завершить чат')
async def end_chat_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != SupportChat.chatting:
        await message.answer('Нет чата для завершения')
        return
    
    user_id = message.from_user.id
    user_key = StorageKey(bot_id=bot.id, user_id=user_id, chat_id=user_id )
    user_data = await storage.get_data(user_key)

    if user_id in g.OPERATORS:
        target_id = user_data.get('user_id')
        target_key = StorageKey(bot_id=bot.id, user_id=target_id, chat_id=target_id)
        target_state = FSMContext(storage=storage, key=target_key)
        await target_state.clear()
        await state.clear()
        await bot.send_message(target_id, 'Оператор завершил чат', reply_markup=ReplyKeyboardRemove())
        await message.answer('Вы завершили чат', reply_markup=ReplyKeyboardRemove())
    else:
        operator_id = user_data.get('operator_id')
        operator_key = StorageKey(bot_id=bot.id, user_id=operator_id, chat_id=operator_id)
        operator_state = FSMContext(storage=storage, key=operator_key)
        await operator_state.clear()
        await state.clear()

        await bot.send_message(operator_id, 'Пользователь завершил чат', reply_markup=ReplyKeyboardRemove())
        await message.answer('Вы завершили чат', reply_markup=ReplyKeyboardRemove())

    await process_waiting_questions()

@router.message(SupportChat.chatting)
async def chat_message(message: Message, state: FSMContext):
    if message.from_user.id in g.OPERATORS:
        if message.text.startswith('/'):
            return
        sender_type = 'operator'
        operator_id = message.from_user.id
        operator_key = StorageKey(bot_id=bot.id, user_id=operator_id, chat_id=operator_id)
        operator_data = await storage.get_data(operator_key)
        user_id = operator_data.get('user_id')
        chat_start_id = operator_data.get('chat_start_id')

        if not user_id:
            await message.answer('Произошел сбой. Пожалуйста, начните чат заново')
            await state.clear()
            return
        
        await bot.send_message(user_id, f'Оператор:\n{message.text}', reply_markup=end_chat_kb)

    else:
        sender_type = 'user'
        user_id = message.from_user.id
        user_key = StorageKey(bot_id=bot.id, user_id=user_id, chat_id=user_id)
        user_data = await storage.get_data(user_key)
        operator_id = user_data.get('operator_id')
        chat_start_id = user_data.get('chat_start_id')

        if not operator_id:
            await message.answer("Оператор пока не подключился к чату. Пожалуйста, подождите.")
            return
        await bot.send_message(operator_id, f'Пользователь:\n{message.text}', reply_markup=end_chat_kb)
    if chat_start_id:
        await log_chat_message(chat_start_id, sender_type, message.text, operator_id=operator_id)
