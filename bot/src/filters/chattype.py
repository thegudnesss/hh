from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Optional, List


class ChatTypeFilter(Filter):
    def __init__(
        self,
        private: Optional[bool] = None,
        group: Optional[bool] = None,
        supergroup: Optional[bool] = None,
        channel: Optional[bool] = None
    ) -> None:
        # Yig‘amiz faqat True bo‘lganlarini
        self.chat_types: List[str] = [
            name
            for name, value in {
                "private": private,
                "group": group,
                "supergroup": supergroup,
                "channel": channel,
            }.items()
            if value
        ]

        # Agar hech biri berilmasa, barcha turlarga ruxsat
        if not self.chat_types:
            self.chat_types = ["private", "group", "supergroup", "channel"]

    async def __call__(self, union: Message | CallbackQuery) -> bool:
        if isinstance(union, CallbackQuery):
            chat_type = union.message.chat.type
        elif isinstance(union, Message):
            chat_type = union.chat.type
        else:
            return False
        return chat_type in self.chat_types
