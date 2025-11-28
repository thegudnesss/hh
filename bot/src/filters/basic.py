from aiogram.filters import Filter

from aiogram.types import Message, CallbackQuery
class IsAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        admin_ids = [2038175209, 5674598705] # Admin foydalanuvchi IDlarini shu yerga qo'shing
        return event.from_user.id in admin_ids

