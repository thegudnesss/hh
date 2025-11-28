from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from contextlib import suppress

from pymongo.errors import DuplicateKeyError

from typing import Callable, Dict, Any, Awaitable, Union

from datetime import datetime

from src.database.models.user import User


class UserMiddleware(BaseMiddleware):
    """
    Foydalanuvchini har bir so‘rovda avtomatik bazaga qo‘shuvchi yoki yangilovchi middleware.
    """

    def __init__(self, db):
        super().__init__()
        self.db = db  # <--- db ni saqlaymiz

    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:

        # Foydalanuvchini aniqlash
        user_id = event.from_user.id
        is_premium = bool(event.from_user.is_premium)

        # Foydalanuvchini bazadan topamiz
        
        status = await self.db.users.find_one(dict(_id=user_id))
        
            # Yangi foydalanuvchi yaratish
        user = User(
                id=user_id,
                phone_number=None,
                is_premium=is_premium,
                balance=0,
                referrer_id=None,
                referrals_count=0,
                order_count=0
            ) if not status else status if isinstance(status, User) else User(**status)
        with suppress(DuplicateKeyError):
            await self.db.users.insert_one(dict(_id=user_id))
            await self.db.users.update_one(dict(_id=user_id), dict(user.model_dump(by_alias=True)))
            # Mavjud foydalanuvchini yangilash

        # Handler uchun foydalanuvchini uzatamiz
        data["user"] = user

        # Keyingi handlerga o'tkazish
        return await handler(event, data)
