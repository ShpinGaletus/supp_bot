from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def categories_keyboard(categories):
    buttons = [
        [InlineKeyboardButton(text=cat['name'], callback_data=f"category_{cat['id']}")]
        for cat in categories
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def questions_keyboard(questions):
    buttons = [
        [InlineKeyboardButton(text=q['question'], callback_data=f"question_{q['id']}")]
        for q in questions
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

