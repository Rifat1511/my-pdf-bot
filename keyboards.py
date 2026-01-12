# keyboards.py
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Начать расчёт", callback_data="start_estimate")],
        [InlineKeyboardButton(text="ℹ️ О компании", callback_data="about")],
        [InlineKeyboardButton(text="🧾 Наши цены", callback_data="prices")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
    ])


def back_to_main():
    """Кнопка 'Назад в меню'"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def flat_types():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪄 Студия (25 м²)", callback_data="area_25")],
        [InlineKeyboardButton(text="🛋️ 1-комнатная (35 м²)", callback_data="area_35")],
        [InlineKeyboardButton(text="🛏️ 2-комнатная (45 м²)", callback_data="area_45")],
        [InlineKeyboardButton(text="👨‍👩‍👧‍👦 3-комнатная (60 м²)", callback_data="area_60")],
        [InlineKeyboardButton(text="🏠 Дом (80+ м²)", callback_data="area_80")],
        [InlineKeyboardButton(text="📏 Указать самому", callback_data="custom_area")]
    ])

def repair_types():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧩 Косметический", callback_data="repair_cosmetic")],
        [InlineKeyboardButton(text="🔧 Стандартный", callback_data="repair_standard")],
        [InlineKeyboardButton(text="⭐ Премиум", callback_data="repair_premium")],
        [InlineKeyboardButton(text="🎨 Дизайнерский", callback_data="repair_designer")]
    ])

def urgency_options():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Срочно (+50%)", callback_data="urgent")],
        [InlineKeyboardButton(text="🕓 Обычный срок", callback_data="normal")]
    ])

def result_actions():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать PDF", callback_data="pdf")],
        [InlineKeyboardButton(text="📤 Отправить менеджеру", callback_data="send")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def phone_keyboard():
    btn = KeyboardButton(text="📱 Отправить номер", request_contact=True)
    return ReplyKeyboardMarkup(keyboard=[[btn]], resize_keyboard=True, one_time_keyboard=True)