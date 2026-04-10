from aiogram import Router, types, F
from keyboards.inline import get_main_keyboard, get_back_keyboard
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import firebase_client as fc

router = Router()


# Состояния для регистрации
class Registration(StatesGroup):
    waiting_email = State()


# === КЛАВИАТУРЫ ===


# def get_main_keyboard():
#     """Главное меню"""
#     return InlineKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 InlineKeyboardButton(text="📅 Сборы", callback_data="btn_gatherings"),
#                 InlineKeyboardButton(text="👤 Профиль", callback_data="btn_profile"),
#             ],
#             [
#                 InlineKeyboardButton(text="🤝 Попутчик", callback_data="btn_buddy"),
#                 InlineKeyboardButton(text="🌤 Погода", callback_data="btn_weather"),
#             ],
#             [InlineKeyboardButton(text="ℹ️ О приложении", callback_data="btn_about")],
#         ]
#     )


# def get_back_keyboard():
#     """Кнопка назад"""
#     return InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="btn_back_main")]
#         ]
#     )


# === ЛОГИКА СТАРТА И РЕГИСТРАЦИИ ===


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    try:
        await message.delete()
    except:
        pass

    # Проверка: если пользователь уже есть в базе, сразу даем меню
    user = fc.get_user_by_chat_id(message.chat.id)
    if user:
        await message.answer(
            f"👋 С возвращением, <b>{user['name']}</b>!",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML",
        )
        return

    text = (
        "<b>🐸 Привет! Я бот «Плечом к плечу».</b>\n\n"
        "Для начала привяжи аккаунт — отправь email из приложения."
    )
    sent_msg = await message.answer(text, parse_mode="HTML")
    await state.update_data(last_msg_id=sent_msg.message_id)
    await state.set_state(Registration.waiting_email)


@router.message(Registration.waiting_email)
async def process_email(message: Message, state: FSMContext):
    email = message.text.strip().lower()
    user = fc.get_user_by_email(email)
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")

    try:
        await message.delete()
    except:
        pass

    if user:
        fc.update_user(user["uid"], {"telegramChatId": str(message.chat.id)})
        await state.clear()
        welcome_text = (
            f"✅ Аккаунт привязан! Привет, <b>{user['name']}</b>!\n\n"
            f"Используй кнопки ниже для управления."
        )
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=last_msg_id,
            text=welcome_text,
            reply_markup=get_main_keyboard(),
            parse_mode="HTML",
        )
    else:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=last_msg_id,
            text="❌ Email не найден. Попробуй еще раз:",
        )


# === ОБРАБОТКА КНОПОК МЕНЮ ===


@router.callback_query(F.data == "btn_profile")
async def show_profile(callback: CallbackQuery):
    # Импортируем функцию прямо здесь, чтобы избежать циклической ошибки
    from handlers.profile import cmd_profile

    await cmd_profile(callback.message, edit=True)
    await callback.answer()


@router.callback_query(F.data == "btn_gatherings")
async def process_gatherings_btn(callback: CallbackQuery):
    from handlers.gatherings import cmd_gatherings

    # Важно: вызываем функцию, которая выводит сборы
    await cmd_gatherings(callback.message)
    await callback.answer()


@router.callback_query(F.data == "btn_weather")
async def process_weather_btn(callback: CallbackQuery):
    from handlers.weather import cmd_weather

    await cmd_weather(callback.message)
    await callback.answer()


@router.callback_query(F.data == "btn_buddy")
async def process_buddy_btn(callback: CallbackQuery):
    from handlers.buddy import cmd_buddy

    await cmd_buddy(callback.message)
    await callback.answer()


@router.callback_query(F.data == "btn_about")
async def show_about(callback: CallbackQuery):
    await callback.message.edit_text(
        text="🍀 <b>Плечом к плечу</b> — это сообщество для совместных тренировок.\n\n"
        "Бот помогает находить сборы и единомышленников.",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "btn_back_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        text="👋 Добро пожаловать! Выберите нужный раздел:",
        reply_markup=get_main_keyboard(),
    )
    await callback.answer()
