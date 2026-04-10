from aiogram import Router, types, F
from aiogram.filters import Command
import firebase_client as fc
from keyboards.inline import gatherings_keyboard, my_gatherings_keyboard
from config import RU_MONTHS

router = Router()


def format_date(dt):
    return f"{dt.day} {RU_MONTHS[dt.month]}, {dt.strftime('%H:%M')}"


@router.message(Command("gatherings"))
async def cmd_gatherings(message: types.Message):
    gatherings = fc.get_upcoming_gatherings()
    if not gatherings:
        return await message.answer("Пока нет предстоящих сборов 😔")

    for g in gatherings:
        level_map = {
            "beginner": ("🌱", "Новичок"),
            "intermediate": ("💪", "Средний"),
            "advanced": ("🔥", "Профи"),
        }
        type_map = {
            "normal": ("👥", "Обычный"),
            "silent": ("🤫", "Тихий"),
            "closed": ("🔒", "Закрытый"),
        }

        l_e, l_t = level_map.get(g["level"], ("🔘", g["level"]))
        t_e, t_t = type_map.get(g["type"], ("🔘", g["type"]))

        text = (
            f"📍 <b>{g['spotName']}</b>\n"
            f"🕐 {format_date(g['scheduledAt'])}\n"
            f"👥 {g['currentCount']}/{g['maxParticipants']}\n"
            f"📊 {l_e} {l_t} • {t_e} {t_t}"
        )
        await message.answer(
            text, reply_markup=gatherings_keyboard([g]), parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("join:"))
async def callback_join(callback: types.CallbackQuery):
    user = fc.get_user_by_chat_id(callback.from_user.id)
    if not user:
        return await callback.answer(
            "Сначала привяжите аккаунт в /start", show_alert=True
        )

    g_id = callback.data.split(":")[1]
    g = fc.get_gathering(g_id)

    if g["currentCount"] >= g["maxParticipants"]:
        return await callback.answer("Мест больше нет 😔", show_alert=True)

    if g["type"] == "closed" and user["reliabilityPct"] < g["minReliability"]:
        return await callback.answer(
            f"Недостаточно надёжности (нужно {g['minReliability']}%)", show_alert=True
        )

    fc.join_gathering(g_id, user["uid"], user["name"])
    await callback.message.edit_text(
        f"✅ Ты записан на сбор в <b>{g['spotName']}</b>!", parse_mode="HTML"
    )

    # Уведомление создателю
    creator = fc.db.collection("users").document(g["creatorId"]).get().to_dict()
    if creator.get("telegramChatId"):
        from main import bot

        await bot.send_message(
            creator["telegramChatId"], f"👤 {user['name']} записался на ваш сбор!"
        )


@router.message(Command("my"))
async def cmd_my(message: types.Message):
    user = fc.get_user_by_chat_id(message.chat.id)
    if not user:
        return await message.answer("Привяжите аккаунт в /start")

    gatherings = fc.get_user_gatherings(user["uid"])
    if not gatherings:
        return await message.answer("У тебя нет предстоящих записей.")

    await message.answer("Твои сборы:", reply_markup=my_gatherings_keyboard(gatherings))


@router.callback_query(F.data.startswith("cancel:"))
async def callback_cancel(callback: types.CallbackQuery):
    user = fc.get_user_by_chat_id(callback.from_user.id)
    g_id = callback.data.split(":")[1]
    fc.cancel_participation(g_id, user["uid"])
    await callback.message.edit_text("Запись отменена.")
