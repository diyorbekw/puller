import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN, logger
from app.handlers import start, withdraw, admin, ads, support

async def main():
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(start.router)
    dp.include_router(withdraw.router)
    dp.include_router(admin.router)
    dp.include_router(ads.router)
    dp.include_router(support.router)

    logger.info("🤖 Bot ishga tushdi...")
    print("🤖 Bot ishga tushdi...")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Botda xatolik: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())