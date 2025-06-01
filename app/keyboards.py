from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def categories_keyboard(categories, prefix='category'):
    buttons = [
        [InlineKeyboardButton(text=cat['name'], callback_data=f"{prefix}_{cat['id']}")]
        for cat in categories
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def questions_keyboard(questions, prefix='question'):
    buttons = [
        [InlineKeyboardButton(text=q['question'], callback_data=f"{prefix}_{q['id']}")]
        for q in questions
    ]
    if prefix == 'question':
        buttons.append([InlineKeyboardButton(text="Нет нужного вопроса", callback_data="another_question")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

