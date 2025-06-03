import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties  # ✅ Добавлено

from config import TELEGRAM_BOT_TOKEN
from bot.handlers import router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

# Функция для запуска бота
async def main():
    # Проверка наличия токена
    if not TELEGRAM_BOT_TOKEN:
        logging.error(
            "Не указан токен Telegram бота! Пожалуйста, укажите TELEGRAM_BOT_TOKEN в файле .env или config.py")
        return

    # ✅ Инициализация бота с использованием DefaultBotProperties
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутера
    dp.include_router(router)

    # Запуск поллинга
    logging.info("Запуск бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# ✅ Исправлено: __name__ вместо name
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")