import asyncio

from src.loader import dp, bot

from src.middlewares.middleware import UserMiddleware

from src.database.collections import db

from src.handlers import load_modules


async def main():
    load_modules(dp)

    dp.message.middleware(UserMiddleware(db))
    dp.callback_query.middleware(UserMiddleware(db))

    try:
        print("Bot is starting...")
        await dp.start_polling(bot, db=db)
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
    finally:
        print("Closing bot session...")
        await bot.session.close()
    
if __name__ == "__main__":
    asyncio.run(main())
