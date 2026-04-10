import re
import aiohttp
import logging
from gigachat import GigaChat  # Библиотека от Сбера
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text, Location

# Импорты твоих модулей
import firebase_client as fc
from config import VK_TOKEN, OREL_LAT, OREL_LNG, GIGACHAT_CREDENTIALS

# --- НАСТРОЙКА ИИ (GIGACHAT) ---
# verify_ssl_certs=False помогает избежать проблем с сертификатами Минцифры на Windows
giga = GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False)

# Инициализация бота
bot = Bot(token=VK_TOKEN)
logging.basicConfig(level=logging.INFO)

# Словарь состояний пользователей
user_states = {}

# --- КЛАВИАТУРЫ ---


def get_main_keyboard():
    kb = Keyboard(one_time=False)
    kb.add(
        Text("👤 Профиль", payload={"cmd": "profile"}),
        color=KeyboardButtonColor.PRIMARY,
    )
    kb.add(
        Text("🤝 Попутчики", payload={"cmd": "buddy"}),
        color=KeyboardButtonColor.PRIMARY,
    )
    kb.row()
    kb.add(
        Text("📍 Ближайшие площадки", payload={"cmd": "near_spots"}),
        color=KeyboardButtonColor.SECONDARY,
    )
    kb.add(
        Text("🏆 Топ атлетов", payload={"cmd": "leaderboard"}),
        color=KeyboardButtonColor.SECONDARY,
    )
    kb.row()
    # Оставляем ИИ-Тренера и Погоду
    kb.add(
        Text("🤖 ИИ-Тренер", payload={"cmd": "ai_coach"}),
        color=KeyboardButtonColor.POSITIVE,
    )
    kb.add(
        Text("🌤 Погода", payload={"cmd": "weather"}),
        color=KeyboardButtonColor.SECONDARY,
    )
    # ЗДЕСЬ БЫЛА КНОПКА "ДОБАВИТЬ МЕСТО", МЫ ЕЁ УДАЛИЛИ
    return kb.get_json()


def get_ai_keyboard():
    kb = Keyboard(one_time=False)
    kb.add(
        Text("🔙 Закончить тренировку", payload={"cmd": "menu"}),
        color=KeyboardButtonColor.NEGATIVE,
    )
    return kb.get_json()


def get_back_keyboard():
    kb = Keyboard(inline=True)
    kb.add(
        Text("🔙 В меню", payload={"cmd": "menu"}), color=KeyboardButtonColor.NEGATIVE
    )
    return kb.get_json()


# --- ХЕНДЛЕРЫ: СТАРТ И РЕГИСТРАЦИЯ ---


@bot.on.message(text=["Начать", "Привет", "Меню", "🔙 В меню"])
@bot.on.message(payload={"cmd": "menu"})
async def cmd_start(message: Message):
    user_states.pop(message.from_id, None)
    user = fc.get_user_by_vk_id(message.from_id)

    if not user:
        kb = Keyboard(inline=True)
        kb.add(
            Text("✅ Зарегистрироваться", payload={"cmd": "register"}),
            color=KeyboardButtonColor.POSITIVE,
        )
        return await message.answer(
            "Привет! 👋 Похоже, ты еще не в системе «Плечом к Плечу». Зарегистрируемся?",
            keyboard=kb.get_json(),
        )

    await message.answer(
        f"С возвращением, {user.get('name')}! 💪 Чем сегодня займемся?",
        keyboard=get_main_keyboard(),
    )


@bot.on.message(payload={"cmd": "register"})
async def cmd_register_choice(message: Message):
    kb = Keyboard(inline=True)
    kb.add(
        Text("Да, есть", payload={"cmd": "link_acc"}), color=KeyboardButtonColor.PRIMARY
    )
    kb.add(
        Text("Нет, я новый", payload={"cmd": "new_acc"}),
        color=KeyboardButtonColor.SECONDARY,
    )
    await message.answer(
        "У тебя уже есть аккаунт в приложении?", keyboard=kb.get_json()
    )


# --- ИИ-ТРЕНЕР (GIGACHAT) ---


@bot.on.message(payload={"cmd": "ai_coach"})
async def cmd_enter_ai_mode(message: Message):
    user_states[message.from_id] = "chatting_with_ai"
    await message.answer(
        "🤖 Привет! Я твой персональный ИИ-тренер GigaChat. 💪\n\n"
        "Спрашивай про упражнения, питание или проси составить программу. Я на связи!",
        keyboard=get_ai_keyboard(),
    )


@bot.on.message(func=lambda msg: user_states.get(msg.from_id) == "chatting_with_ai")
async def handle_ai_dialogue(message: Message):
    if message.text.lower() in ["🔙 закончить тренировку", "меню", "назад"]:
        user_states.pop(message.from_id, None)
        return await message.answer(
            "🫡 Тренировка окончена! Жду тебя снова.", keyboard=get_main_keyboard()
        )

    await message.answer("⏳ Тренер подбирает слова...")
    try:
        # Отправляем запрос в GigaChat
        # Мы используем метод .chat() — он самый простой
        response = giga.chat(
            f"Ты эксперт по воркауту и фитнесу. Отвечай кратко и мотивирующе. Вопрос: {message.text}"
        )

        answer = response.choices[0].message.content
        await message.answer(answer, keyboard=get_ai_keyboard())

    except Exception as e:
        print(f"ОШИБКА GIGACHAT: {e}")
        await message.answer("😢 Тренер временно недоступен. Попробуй через минуту!")


# --- ОСТАЛЬНЫЕ ХЕНДЛЕРЫ (Leaderboard, Profile, Weather) ---


@bot.on.message(payload={"cmd": "profile"})
async def cmd_profile(message: Message):
    user = fc.get_user_by_vk_id(message.from_id)
    if not user:
        return await message.answer("❌ Аккаунт не найден.")
    text = f"👤 Профиль: {user.get('name')}\n🆙 Уровень: {user.get('level', 1)}\n✨ Опыт: {user.get('xp', 0)} XP"
    await message.answer(text, keyboard=get_main_keyboard())


@bot.on.message(payload={"cmd": "leaderboard"})
async def cmd_leaderboard(message: Message):
    leaders = fc.get_leaderboard(limit=10)
    text = "🏆 ТОП-10 АТЛЕТОВ:\n" + "—" * 15 + "\n"
    for i, u in enumerate(leaders or []):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🔹"
        text += f"{medal} {u.get('name')} — {u.get('level', 1)} lvl\n"
    await message.answer(text)


@bot.on.message(payload={"cmd": "near_spots"})
async def ask_location(message: Message):
    kb = Keyboard(one_time=True)
    kb.add(Location())
    kb.row()
    kb.add(Text("🔙 В меню", payload={"cmd": "menu"}))
    await message.answer(
        "Отправь свою локацию, чтобы найти площадки рядом! 👇", keyboard=kb.get_json()
    )


@bot.on.message(payload={"cmd": "weather"})
async def cmd_weather(message: Message):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={OREL_LAT}&longitude={OREL_LNG}&current_weather=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            temp = round(data["current_weather"]["temperature"])
            await message.answer(
                f"🌤 В Орле сейчас {temp}°C. Отличное время для тренировки!"
            )


# --- УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК ---


@bot.on.message()
async def handle_all(message: Message):
    if message.geo:
        # Логика поиска площадок (уже была у нас)
        spots = fc.get_nearest_places(
            message.geo.coordinates.latitude, message.geo.coordinates.longitude
        )
        if not spots:
            return await message.answer("📍 Рядом ничего не найдено.")
        res = "📍 БЛИЖАЙШИЕ ПЛОЩАДКИ:\n\n"
        for s in spots:
            res += f"🔸 {s['name']} ({s['distance']} км)\n"
        return await message.answer(res, keyboard=get_main_keyboard())

    await message.answer(
        "❓ Я не понимаю. Используй меню 👇", keyboard=get_main_keyboard()
    )


if __name__ == "__main__":
    print("🚀 Бот запущен на GigaChat!")
    bot.run_forever()
