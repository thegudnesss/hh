from aiogram import Bot, Dispatcher 

from aiogram.enums import ParseMode

from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from motor.motor_asyncio import AsyncIOMotorClient

from src.config import config

session = AiohttpSession()

dp = Dispatcher()

bot = Bot(
    token=config.BOT_TOKEN.get_secret_value(),
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

client = AsyncIOMotorClient(config.MONGO_URL.get_secret_value())
dbname = client.dbname
