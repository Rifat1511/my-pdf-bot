# bot.py
import asyncio
import logging
# === Подключение шрифта для кириллицы ===
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def load_fonts():
    font_file = "DejaVuSans.ttf"
    if os.path.exists(font_file):
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", font_file))
            print(f"✅ Шрифт загружен: {os.path.abspath(font_file)}")
        except Exception as e:
            print(f"❌ Ошибка загрузки шрифта: {e}")
    else:
        print(f"⚠️ Файл шрифта не найден: {os.path.abspath(font_file)}")
        print("💡 Выполни: curl -L -o DejaVuSans.ttf https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf")
# Проверка: доступен ли DejaVuSans?
from reportlab.pdfbase import pdfmetrics

def load_fonts():
    font_file = "DejaVuSans.ttf"
    if not os.path.exists(font_file):
        print("❌ Файл шрифта не найден")
        return False

    try:
        # Читаем заголовок файла, чтобы убедиться, что это TTF
        with open(font_file, "rb") as f:
            header = f.read(4)
            if header != b'\x00\x01\x00\x00':
                print(f"❌ Неверный формат .ttf: {header.hex()}")
                return False
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return False

    try:
        pdfmetrics.registerFont(TTFont("DejaVuSans", font_file))
        print("✅ Шрифт DejaVuSans зарегистрирован")
        return True
    except Exception as e:
        print(f"❌ Ошибка регистрации шрифта: {e}")
        return False

# Вызываем
load_fonts()
# Вызываем при старте
load_fonts()
from datetime import datetime
from io import BytesIO

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Модули
from config import BOT_TOKEN, MANAGER_CHAT_ID, COMPANY, PRICE_RATES
import keyboards
from messages import (
    WELCOME_MESSAGE, ABOUT_US, PRICES_INFO, CONTACTS,
    SELECT_FLAT_TYPE, ENTER_AREA, SELECT_REPAIR,
    SELECT_URGENCY, REQUEST_NAME, REQUEST_PHONE,
    REQUEST_COMMENT, SUCCESS_SENT
)

# === ГЕНЕРАТОР PDF БЕЗ QR-КОДА И ОШИБОК ===
def generate_beautiful_pdf(data: dict) -> BytesIO:
    buffer = BytesIO()
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.utils import simpleSplit
    except ImportError:
        raise Exception("reportlab не установлен")

    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50 * mm
    left = 30 * mm
    line_height = 18

    # --- Шрифт ---
    def draw_text(x, y, text, size=10, bold=False):
        font_name = "Helvetica"
        if bold:
            font_name += "-Bold"
        c.setFont(font_name, size)
        lines = simpleSplit(text, font_name, size, width - 2*left)
        for line in lines:
            c.drawString(x, y, line)
            y -= line_height
        return y

    # --- Заголовок ---
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0, 0.3, 0.6)
    c.drawString(left, y, "ПРОСТРОЙку и ремонт Оренбург")
    y -= 15
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    c.drawString(left, y, "Ремонт под ключ • Гарантия 3 года")
    y -= 20

    c.line(left, y, width - left, y)
    y -= 20

    # --- Данные ---
    flat_labels = {
        25: "Студия",
        35: "1-комнатная квартира",
        45: "2-комнатная квартира",
        60: "3-комнатная квартира",
        80: "Частный дом"
    }
    repair_names = {
        "cosmetic": "Косметический",
        "standard": "Стандартный",
        "premium": "Премиум",
        "designer": "Дизайнерский"
    }

    info_lines = [
        ("ID сметы", data["estimate_id"]),
        ("Тип жилья", flat_labels.get(data["area"], "Индивидуальный")),
        ("Площадь", f"{data['area']} м²"),
        ("Тип ремонта", repair_names[data["repair_type"]]),
        ("Срок выполнения", "Срочно (+50%)" if data["urgency"] == "urgent" else "Обычный срок"),
        ("Итого", f"{data['total_cost']:,} ₽"),
    ]

    for label, value in info_lines:
        y = draw_text(left, y, f"{label}:", size=11, bold=True)
        y = draw_text(left + 90*mm, y, value, size=11)
        y -= 5

    y -= 20

    # --- Подпись ---
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(left, y, "PDF сгенерирован автоматически")
    c.drawRightString(width - left, y, "prostroy-orenburg.ru")

    c.save()
    buffer.seek(0)
    return buffer
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class Form(StatesGroup):
    entering_area = State()
    entering_name = State()
    entering_phone = State()
    entering_comment = State()


# Хранилище
user_data = {}


def get_user(user_id: int):
    if user_id not in user_data:
        user_data[user_id] = {}
    return user_data[user_id]


# === Команды ===
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        WELCOME_MESSAGE,
        parse_mode="Markdown",
        reply_markup=keyboards.main_menu()
    )


# === Главное меню ===
@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    get_user(callback.from_user.id).clear()
    await callback.message.edit_text(
        WELCOME_MESSAGE,
        parse_mode="Markdown",
        reply_markup=keyboards.main_menu()
    )
    await callback.answer()


# === Информационные страницы ===
@dp.callback_query(F.data == "about")
async def about(callback: CallbackQuery):
    await callback.message.edit_text(
        ABOUT_US,
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=keyboards.back_to_main()
    )
    await callback.answer()


@dp.callback_query(F.data == "prices")
async def prices(callback: CallbackQuery):
    await callback.message.edit_text(
        PRICES_INFO,
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=keyboards.back_to_main()
    )
    await callback.answer()


@dp.callback_query(F.data == "contacts")
async def contacts(callback: CallbackQuery):
    await callback.message.edit_text(
        CONTACTS,
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=keyboards.back_to_main()
    )
    await callback.answer()


@dp.callback_query(F.data == "prices")
async def prices(callback: CallbackQuery):
    await callback.message.edit_text(PRICES_INFO, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data == "contacts")
async def contacts(callback: CallbackQuery):
    await callback.message.edit_text(CONTACTS, parse_mode="Markdown", disable_web_page_preview=True)
    await callback.answer()


# === Начать расчёт ===
@dp.callback_query(F.data == "start_estimate")
async def start_estimate(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    user.clear()
    user["region"] = "Оренбург"
    await callback.message.edit_text(SELECT_FLAT_TYPE, reply_markup=keyboards.flat_types())
    await callback.answer()


# === Выбор площади ===
@dp.callback_query(F.data.startswith("area_"))
async def select_area(callback: CallbackQuery, state: FSMContext):
    area = int(callback.data.replace("area_", ""))
    get_user(callback.from_user.id)["area"] = area
    await callback.message.edit_text(SELECT_REPAIR, reply_markup=keyboards.repair_types())
    await callback.answer()


@dp.callback_query(F.data == "custom_area")
async def custom_area(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.entering_area)
    await callback.message.edit_text(ENTER_AREA)
    await callback.answer()


@dp.message(Form.entering_area)
async def got_area(message: Message, state: FSMContext):
    try:
        area = float(message.text.replace(",", "."))
        if not (10 <= area <= 300):
            await message.answer("Введите число от 10 до 300.")
            return
        get_user(message.from_user.id)["area"] = area
        await message.answer(SELECT_REPAIR, reply_markup=keyboards.repair_types())
        await state.clear()
    except ValueError:
        await message.answer("Введите корректное число.")


# === Выбор типа ремонта ===
@dp.callback_query(F.data.startswith("repair_"))
async def select_repair(callback: CallbackQuery):
    repair_type = callback.data.replace("repair_", "")
    get_user(callback.from_user.id)["repair_type"] = repair_type
    await callback.message.edit_text(SELECT_URGENCY, reply_markup=keyboards.urgency_options())
    await callback.answer()


# === Выбор срока → результат (исправлено!) ===
@dp.callback_query(F.data.in_(["urgent", "normal"]))
async def calculate_result(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = get_user(user_id)

    # ✅ Вот где была ошибка: переменная repair_key не определена
    repair_type = data["repair_type"]
    area = data["area"]

    rate = PRICE_RATES.get(repair_type, 4500)
    total = rate * area
    if callback.data == "urgent":
        total *= 1.5
    total = int(total)

    # Сохраняем
    data["urgency"] = callback.data
    data["total_cost"] = total
    data["estimate_id"] = f"EST{datetime.now().strftime('%Y%m%d%H%M')}"
    data["created_at"] = datetime.now()

    # Формируем текст
    repair_names = {
        "cosmetic": "Косметический",
        "standard": "Стандартный",
        "premium": "Премиум",
        "designer": "Дизайнерский"
    }
    flat_labels = {
        25: "Студия",
        35: "1-комнатная",
        45: "2-комнатная",
        60: "3-комнатная",
        80: "Дом"
    }
    flat_label = flat_labels.get(area, "Индивидуальная")

    urgency_text = "Срочно (+50%)" if callback.data == "urgent" else "Обычный срок"

    text = (
        f"*📋 Ваша смета*\n\n"
        f"*ID:* `{data['estimate_id']}`\n"
        f"*Тип жилья:* {flat_label}\n"
        f"*Площадь:* {area} м²\n"
        f"*Ремонт:* {repair_names[repair_type]}\n"
        f"*Срок:* {urgency_text}\n\n"
        f"*Итого:* `{total:,}` ₽\n\n"
        f"📞 Менеджер свяжется с вами для уточнения деталей."
    )

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboards.result_actions())
    await callback.answer()


# === Скачать PDF (прос
@dp.callback_query(F.data == "pdf")
async def send_pdf(callback: CallbackQuery):
    data = get_user(callback.from_user.id)
    if not data.get("total_cost"):
        await callback.answer("Сначала сделайте расчёт.", show_alert=True)
        return

    try:
        buf = generate_beautiful_pdf(data)
        filename = f"Смета_{data['estimate_id']}.pdf"
        doc = BufferedInputFile(file=buf.read(), filename=filename)
        await callback.message.answer_document(document=doc, caption="📄 Профессиональная смета от ПРОСТРОЙку и ремонт Оренбург")
        buf.close()
    except Exception as e:
        logger.error(f"Ошибка генерации PDF: {e}")
        await callback.message.answer("❌ Не удалось создать PDF.")

    await callback.answer()
 

# === Отправить менеджеру ===
@dp.callback_query(F.data == "send")
async def send_to_manager(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.entering_name)
    await callback.message.edit_text(REQUEST_NAME)
    await callback.answer()


@dp.message(Form.entering_name)
async def got_name(message: Message, state: FSMContext):
    get_user(message.from_user.id)["client_name"] = message.text.strip()
    await state.set_state(Form.entering_phone)
    await message.answer(REQUEST_PHONE, reply_markup=keyboards.phone_keyboard())


@dp.message(Form.entering_phone, F.contact)
async def got_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    get_user(message.from_user.id)["client_phone"] = phone
    await state.set_state(Form.entering_comment)
    await message.answer(REQUEST_COMMENT, reply_markup=ReplyKeyboardRemove())


@dp.message(Form.entering_phone)
async def got_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    get_user(message.from_user.id)["client_phone"] = phone
    await state.set_state(Form.entering_comment)
    await message.answer(REQUEST_COMMENT, reply_markup=ReplyKeyboardRemove())


@dp.message(Form.entering_comment)
async def finalize(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = get_user(user_id)

    data["comment"] = message.text.strip() if message.text else ""

    # Отправляем менеджеру
    if MANAGER_CHAT_ID:
        text = (
            f"*📩 Новая заявка #{data['estimate_id']}*\n"
            f"*Имя:* {data.get('client_name', '—')}\n"
            f"*Телефон:* {data['client_phone']}\n"
            f"*Площадь:* {data['area']} м²\n"
            f"*Ремонт:* {data['repair_type']}\n"
            f"*Срочность:* {'Срочно' if data['urgency'] == 'urgent' else 'Обычно'}\n"
            f"*Итого:* {data['total_cost']:,} ₽\n"
            f"*Коммент:* {data['comment'] or '—'}"
        )
        try:
            await bot.send_message(MANAGER_CHAT_ID, text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Send failed: {e}")

    # Подтверждение клиенту
    success = SUCCESS_SENT.format(estimate_id=data['estimate_id'])
    await state.clear()
    await message.answer(success, parse_mode="Markdown", reply_markup=keyboards.result_actions())


# === Запуск ===
async def main():
    logger.info("🚀 Бот запущен: красивый, информативный, без ошибок")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())