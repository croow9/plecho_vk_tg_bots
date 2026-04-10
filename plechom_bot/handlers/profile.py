from aiogram import Router, types, F  # <--- ДОБАВЛЕН ИМПОРТ F
from aiogram.filters import Command
import firebase_client as fc
from keyboards.inline import get_back_keyboard  # Импортируем кнопку назад, если она там

router = Router()


@router.message(Command("profile"))
async def cmd_profile(message: types.Message, edit: bool = False):
    user = fc.get_user_by_chat_id(message.chat.id)
    if not user:
        if edit:
            return await message.edit_text("Привяжите аккаунт в /start")
        return await message.answer("Привяжите аккаунт в /start")

    # Безопасное получение очков эмпатии (на случай если в базе пусто)
    empathy = int(user.get("empathyScore", 0))
    stars = "★" * empathy + "☆" * (5 - empathy)

    badges_map = {
        "team_friend": "🤝 Друг команды",
        "first_step": "🌱 Первый шаг",
        "first_trainer": "🏅 Первый тренер",
        "steel_will": "🔥 Стальная воля",
    }
    badge_list = "\n".join([badges_map.get(b, b) for b in user.get("badges", [])])

    text = (
        f"👤 <b>{user.get('name', 'Пользователь')}</b>\n"
        f"📧 {user.get('email', '-')}\n\n"
        f"💛 Эмпатия: {stars}\n"
        f"📊 Надёжность: {user.get('reliabilityPct', 0)}%\n"
        f"🔥 Серия: {user.get('streakDays', 0)} дней\n\n"
        f"🏅 <b>Бейджи:</b>\n"
        f"{badge_list or 'Пока нет бейджей'}"
    )

    # Если мы пришли из нажатия кнопки — редактируем старое сообщение
    if edit:
        from handlers.start import (
            get_back_keyboard,
        )  # Берем клавиатуру с кнопкой "Назад"

        await message.edit_text(
            text, parse_mode="HTML", reply_markup=get_back_keyboard()
        )
    else:
        await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "btn_profile")
async def cb_profile(callback: types.CallbackQuery):
    # Вызываем cmd_profile и говорим, что нужно РЕДАКТИРОВАТЬ сообщение
    await cmd_profile(callback.message, edit=True)
    await callback.answer()


@router.message(Command("streak"))
async def cmd_streak(message: types.Message):
    user = fc.get_user_by_chat_id(message.chat.id)
    days = user["streakDays"]

    if days == 0:
        phrase = "Начни сегодня — запишись на сбор!"
    elif days <= 3:
        phrase = "Хорошее начало! Продолжай 💪"
    elif days <= 6:
        phrase = "Почти неделя! Ты на верном пути 🌟"
    else:
        phrase = "Невероятно! Ты — машина! 🔥🔥🔥"

    await message.answer(
        f"🔥 Твоя серия: <b>{days} дней</b> подряд!\n\n{phrase}", parse_mode="HTML"
    )


@router.message(Command("top"))
async def cmd_top(message: types.Message):
    users = fc.get_top_streak_users(5)
    text = "🏆 <b>Топ недели по серии:</b>\n\n"
    for i, u in enumerate(users, 1):
        text += f"{i}. {u['name']} — {u['streakDays']} дн. {'🔥' if i == 1 else ''}\n"
    await message.answer(text, parse_mode="HTML")
