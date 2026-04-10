from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def gatherings_keyboard(gatherings: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for g in gatherings:
        builder.button(text=f"Записаться ✋", callback_data=f"join:{g['id']}")
    builder.adjust(1)
    return builder.as_markup()


def my_gatherings_keyboard(gatherings: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for g in gatherings:
        builder.button(
            text=f"❌ Отменить {g['spotName']}", callback_data=f"cancel:{g['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()


def buddy_offer_keyboard(other_uid, gathering_id) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Да, предложить 👋", callback_data=f"buddy_yes:{other_uid}:{gathering_id}"
    )
    builder.button(text="Нет, спасибо", callback_data="cancel_action")
    builder.adjust(2)
    return builder.as_markup()


def buddy_accept_keyboard(requester_uid, gathering_id) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Принять ✅", callback_data=f"buddy_accept:{requester_uid}")
    builder.button(text="Отказать", callback_data="cancel_action")
    builder.adjust(2)
    return builder.as_markup()


def support_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Ещё фразу 🔄", callback_data="support_more")
    return builder.as_markup()


def weather_spots_keyboard(spots: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in spots[:3]:
        builder.button(text=f"📍 {s['name']}", callback_data=f"spot:{s['id']}")
    builder.adjust(1)
    return builder.as_markup()


def spot_detail_keyboard(spot_id) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Ссылка на deep link в приложение (условно)
    builder.button(
        text="Создать сбор здесь", url=f"https://t.me/app_link?start=create_{spot_id}"
    )
    return builder.as_markup()


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard():
    """Главное меню"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Сборы", callback_data="btn_gatherings"),
                InlineKeyboardButton(text="👤 Профиль", callback_data="btn_profile"),
            ],
            [
                InlineKeyboardButton(text="🤝 Попутчик", callback_data="btn_buddy"),
                InlineKeyboardButton(text="🌤 Погода", callback_data="btn_weather"),
            ],
            [InlineKeyboardButton(text="ℹ️ О приложении", callback_data="btn_about")],
        ]
    )


def get_back_keyboard():
    """Универсальная кнопка назад"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="btn_back_main")]
        ]
    )
