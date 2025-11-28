from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.utils.callbackdata import AdminMenuCallback, UserMenuCallback

from typing import Mapping, Any, List, Optional, Dict
def admin_builder(
    details: Optional[dict[str, str | dict[str, str | int]]] = None,
    row: int | list[int] | tuple[int, ...] = (1,)
):
    builder = InlineKeyboardBuilder()

    if details:
        for text, data in details.items():
            if isinstance(data, dict):
                builder.button(
                    text=text,
                    callback_data=AdminMenuCallback(**data).pack()
                )
            else:
                builder.button(
                    text=text,
                    callback_data=AdminMenuCallback(section=data).pack()
                )

    # agar row bitta son bo‘lsa => oddiy, agar list yoki tuple bo‘lsa => unpack qilamiz
    if isinstance(row, (list, tuple)):
        builder.adjust(*row)
    else:
        builder.adjust(row)

    return builder.as_markup()
def user_builder(
    details: Optional[dict[str, str | dict[str, str | int]]] = None,
    row: int | list[int] | tuple[int, ...] = (1,)
):
    builder = InlineKeyboardBuilder()

    if details:
        for text, data in details.items():
            if isinstance(data, dict):
                builder.button(
                    text=text,
                    callback_data=UserMenuCallback(**data).pack()
                )
            else:
                builder.button(
                    text=text,
                    callback_data=UserMenuCallback(section=data).pack()
                )

    # agar row bitta son bo‘lsa => oddiy, agar list yoki tuple bo‘lsa => unpack qilamiz
    if isinstance(row, (list, tuple)):
        builder.adjust(*row)
    else:
        builder.adjust(row)

    return builder.as_markup()
