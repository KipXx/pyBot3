from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardButton, InlineKeyboardMarkup)

main_kb = [
    [KeyboardButton(text='Завтра'),
     KeyboardButton(text='Погода на 3 дня'),
     KeyboardButton(text='Каждый час'),
     KeyboardButton(text='Уфа')]
]

main = ReplyKeyboardMarkup(keyboard=main_kb,
                           resize_keyboard=True,
                           input_field_placeholder='Выберите пункт ниже')