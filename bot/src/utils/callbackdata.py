from aiogram.filters.callback_data import CallbackData
from typing import Optional, Literal

class UserMenuCallback(CallbackData, prefix="menu"):
    # foydalanuvchi roli (user/admin/partner ...)

    # qaysi bo‘lim (home, category, product, cart ...)
    section: Optional[str] = None

    # harakat turi (view, open, next, prev, increase, decrease, add, remove, back ...)
    action: Optional[str] = None

    # qo‘shimcha ID maydonlar (product, category, order va hokazo)
    product_id: Optional[int] = None
    category_id: Optional[int] = None
    order_count: Optional[int] = None
    value:  Optional[str] = None

    # sahifalash uchun
    page: Optional[int] = 1


class AdminMenuCallback(CallbackData, prefix="adminmenu"):
    # foydalanuvchi roli (user/admin/partner ...)

    # qaysi bo‘lim (home, category, product, cart ...)
    section: Optional[str] = None
    
    action: Optional[str] = None
    product_id: Optional[int] = None
    category_id: Optional[int] = None
    value: Optional[str] = None
    id: Optional[int] = None
    # sahifalash uchun
    page: Optional[int] = 1
