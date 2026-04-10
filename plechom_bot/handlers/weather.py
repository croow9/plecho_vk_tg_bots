import logging
import aiohttp
from aiogram import Router, types, F
from config import OREL_LAT, OREL_LNG
import firebase_client as fc
from keyboards.inline import get_back_keyboard

router = Router()

# Словарь расшифровки кодов погоды WMO
WMO_CODES = {
    0: "Ясно ☀️",
    1: "Преимущественно ясно 🌤",
    2: "Переменная облачность ⛅",
    3: "Пасмурно ☁️",
    45: "Туман 🌫",
    48: "Иней 🌫",
    51: "Легкая морось 🌧",
    53: "Умеренная морось 🌧",
    55: "Плотная морось 🌧",
    61: "Небольшой дождь 🌦",
    63: "Умеренный дождь 🌧",
    65: "Сильный дождь 🌧",
    71: "Небольшой снег ❄️",
    73: "Снегопад ❄️",
    75: "Сильный снегопад ❄️",
    77: "Снежные зерна 🌨",
    80: "Слабый ливень 🌧",
    81: "Умеренный ливень 🌧",
    82: "Сильный ливень ⛈",
    85: "Слабый снежный ливень 🌨",
    86: "Сильный снежный ливень 🌨",
    95: "Гроза ⛈",
    96: "Гроза со слабым градом ⛈",
    99: "Гроза с сильным градом ⛈",
}


@router.callback_query(F.data == "btn_weather")
async def cb_weather(callback: types.CallbackQuery):
    """Обработка нажатия на кнопку 'Погода' из главного меню"""
    await cmd_weather(callback.message, edit=True)
    await callback.answer()


async def cmd_weather(message: types.Message, edit: bool = False):
    try:
        # 1. Запрос к Open-Meteo (ключ не нужен!)
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={OREL_LAT}&longitude={OREL_LNG}&current_weather=true"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    text = "⚠️ Метеослужба временно недоступна. Попробуйте позже."
                    return await (
                        message.edit_text(text, reply_markup=get_back_keyboard())
                        if edit
                        else message.answer(text)
                    )

                weather_data = await resp.json()

        # Извлекаем данные
        current = weather_data["current_weather"]
        temp = round(current["temperature"])
        code = current["weathercode"]
        desc = WMO_CODES.get(code, "Неизвестные условия")

        # 2. Получаем площадки из Firebase
        try:
            spots = fc.get_approved_spots()
        except Exception as e:
            logging.error(f"Firebase error in weather: {e}")
            spots = []

        # 3. Формируем ответ
        text = (
            f"🌤 <b>Погода в Орле сейчас:</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"🌡 Температура: <b>{temp}°C</b>\n"
            f"📝 Состояние: <b>{desc}</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
        )

        if spots:
            text += "📍 <b>Рекомендуемые площадки:</b>\n"
            for s in spots[:3]:  # Показываем топ-3 площадки
                text += f"• {s['name']} (⭐ {s.get('rating', '5.0')})\n"
        else:
            text += "🛝 Список площадок временно недоступен."

        kb = get_back_keyboard()

        if edit:
            await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=kb, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Weather error: {e}")
        error_text = "😢 Ошибка при получении данных о погоде."
        if edit:
            await message.edit_text(error_text, reply_markup=get_back_keyboard())
        else:
            await message.answer(error_text, reply_markup=get_back_keyboard())
