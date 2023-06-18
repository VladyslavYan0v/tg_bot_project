from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

kbd_menu = ReplyKeyboardMarkup(row_width=2 ,keyboard=[
    [KeyboardButton(text="Пошук інформації"), KeyboardButton(text="Кінотеатри")]

], resize_keyboard=True)

kbd_inf = ReplyKeyboardMarkup(row_width=3, keyboard=[
    [KeyboardButton(text="/rate"), KeyboardButton(text="/topbest"), KeyboardButton(text="/calendar")],
    [KeyboardButton(text="Назад")]
], resize_keyboard=True)

kbd_cinema = ReplyKeyboardMarkup(row_width=3, keyboard=[
    [KeyboardButton(text="/cinemashort"), KeyboardButton(text="/cinemanow"), KeyboardButton(text="/cinemasoon")],
    [KeyboardButton(text="Назад")]
], resize_keyboard=True)

kbd_stop = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="/stop")]
], resize_keyboard=True, one_time_keyboard=True)
