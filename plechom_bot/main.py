import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand  # Добавь этот импорт для кнопки Menu

from config import BOT_TOKEN
from handlers import start, gatherings, profile, buddy, weather
from scheduler import setup_scheduler


# Функция для настройки кнопки Menu (синяя кнопка слева от ввода)
async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="/start", description="🔄 Главное меню"),
        BotCommand(command="/help", description="❓ Помощь"),
    ]
    await bot.set_my_commands(main_menu_commands)


async def main():
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)

    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # 1. Подключение роутеров (все твои файлы из папки handlers)
    dp.include_router(start.router)
    dp.include_router(gatherings.router)
    dp.include_router(profile.router)
    dp.include_router(buddy.router)
    dp.include_router(weather.router)

    # 2. Установка кнопки Menu
    await set_main_menu(bot)

    # 3. Запуск планировщика (если он нужен для уведомлений)
    scheduler = setup_scheduler(bot)
    scheduler.start()

    print("Бот запущен и кнопка меню настроена...")

    # Запуск поллинга
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Бот остановлен!")
