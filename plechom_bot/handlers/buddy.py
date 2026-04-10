from aiogram import Router, types, F
import firebase_client as fc
from keyboards.inline import get_back_keyboard
from config import RU_MONTHS

router = Router()


@router.callback_query(F.data == "btn_buddy")
async def cb_buddy(callback: types.CallbackQuery):
    await cmd_buddy(callback.message, edit=True)
    await callback.answer()


async def cmd_buddy(message: types.Message, edit: bool = False):
    user = fc.get_user_by_chat_id(message.chat.id)
    if not user:
        text = "❌ Сначала привяжите аккаунт в /start"
        return await (message.edit_text(text) if edit else message.answer(text))

    # Получаем сборы, в которых участвует юзер
    user_gatherings = fc.get_user_gatherings(user["uid"])

    if not user_gatherings:
        text = (
            "🤝 <b>Попутчики</b>\n\n"
            "Вы еще не записаны ни на один сбор.\n"
            "Чтобы увидеть список попутчиков, запишитесь на тренировку в разделе «Сборы»."
        )
    else:
        text = "🤝 <b>Твои попутчики по сборам:</b>\n\n"

        for g in user_gatherings:
            # --- ЛОГИКА ОПРЕДЕЛЕНИЯ НАЗВАНИЯ ---
            # Пробуем достать название из разных полей (title, name или comment)
            g_name = g.get("title") or g.get("name") or g.get("comment")

            # Если названия в базе нет вообще, формируем его из даты
            if not g_name:
                dt = g.get("scheduledAt")  # Это объект datetime
                if dt:
                    g_name = f"Сбор {dt.day} {RU_MONTHS.get(dt.month)} в {dt.strftime('%H:%M')}"
                else:
                    g_name = "Тренировка"

            participants = fc.get_participants(g["id"])
            # Убираем самого себя из списка попутчиков
            others = [p for p in participants if p != user.get("name")]

            text += f"📍 <b>{g_name}</b>\n"
            if others:
                text += "👥 Идут с тобой: " + ", ".join(others) + "\n\n"
            else:
                text += "👤 Пока только ты. Зови друзей!\n\n"

        text += "<i>Связаться с ребятами можно в мобильном приложении.</i>"

    kb = get_back_keyboard()

    if edit:
        await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
