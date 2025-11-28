from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from motor.core import AgnosticDatabase as MDB
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest
import httpx
from datetime import datetime

from src.utils.callbackdata import UserMenuCallback
from src.utils.keyboards import user_builder
from src.utils.helper import build_cart_text
from src.config import config
from src.loader import bot

router = Router()

@router.callback_query(UserMenuCallback.filter(F.section == "payment"))
async def payment(call: CallbackQuery, callback_data: UserMenuCallback, db: MDB, user):
    """
    Foydalanuvchi savatidagi mahsulotlarni to'lash uchun Click to'lov tizimiga yo'naltirish
    """
    # Savatni tekshirish
    if not user.savat or len(user.savat) == 0:
        await call.answer("❌ Savatingiz bo'sh!", show_alert=True)
        return

    # Umumiy summani hisoblash
    total_amount = 0
    for item in user.savat:
        product = await db.products.find_one({"id": item["product_id"]})
        if product:
            total_amount += product.price * item["count"]

    if total_amount <= 0:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)
        return

    # Yangi order_id yaratish
    last_order = await db.orders.collection.find_one(
        {},
        sort=[("order_id", -1)]
    )
    order_id = (last_order["order_id"] + 1) if last_order else 1

    # MongoDB'ga orderni saqlash
    order_data = {
        "order_id": order_id,
        "user_id": user.id,
        "products": user.savat,
        "total_amount": float(total_amount),
        "status": "pending",
        "payment_method": "click"
    }
    await db.orders.insert_one(order_data)

    # To'lov havolasini olish uchun veb-ilovaga so'rov yuborish
    payment_link = None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://bulvar.site/api/v1/orders",  # Domen nomingiz
                json={
                    "product_name": f"Buyurtma #{order_id}",
                    "amount": float(total_amount),
                    "payment_method": "click",
                    "description": f"Foydalanuvchi {user.id} tomonidan yaratilgan buyurtma"
                },
                timeout=10.0
            )
            response.raise_for_status()  # Agar xatolik bo'lsa (4xx yoki 5xx)
            data = response.json()
            payment_link = data.get("payment_link")

    except httpx.RequestError as e:
        print(f"⚠️ Veb-ilovaga ulanishda xatolik: {e}")
        await call.answer("❌ To'lov xizmatiga ulanib bo'lmadi. Iltimos, keyinroq qayta urinib ko'ring.", show_alert=True)
        return
    except Exception as e:
        print(f"⚠️ To'lov havolasini olishda noma'lum xatolik: {e}")
        await call.answer("❌ Noma'lum xatolik yuz berdi.", show_alert=True)
        return

    if not payment_link:
        await call.answer("❌ To'lov havolasini yaratib bo'lmadi.", show_alert=True)
        return

    try:
        # To'lov tugmalarini yaratish
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Click orqali to'lash", url=payment_link)],
            [InlineKeyboardButton(
                text="🔙 Orqaga",
                callback_data=UserMenuCallback(section="cart").pack()
            )]
        ])

        text = (
            f"📦 <b>Buyurtma #{order_id}</b>\n\n"
            f"💰 Umumiy summa: {total_amount:,} so'm\n\n"
            f"💳 To'lov qilish uchun pastdagi tugmani bosing:"
        )

        with suppress(TelegramBadRequest):
            await call.message.delete()

        await call.message.answer(text, reply_markup=keyboard)

    except Exception as e:
        await call.message.answer(f"❌ Xatolik: {str(e)}")
        print(f"Payment error: {e}")


@router.callback_query(UserMenuCallback.filter(F.section == "check_payment"))
async def check_payment(call: CallbackQuery, callback_data: UserMenuCallback, db: MDB, user):
    """
    To'lovni tekshirish
    """
    order_id = callback_data.order_id

    # Orderni topish
    order = await db.orders.find_one({"order_id": order_id, "user_id": user.id})

    if not order:
        await call.answer("❌ Buyurtma topilmadi!", show_alert=True)
        return

    if order.status == "paid":
        # Savatni tozalash
        await db.users.update_one(
            {"id": user.id},
            {"savat": [], "$inc": {"order_count": 1}}
        )

        await call.message.edit_text(
            f"✅ <b>To'lov muvaffaqiyatli amalga oshirildi!</b>\n\n"
            f"📦 Buyurtma #{order_id}\n"
            f"💰 Summa: {order.total_amount:,} so'm\n\n"
            f"Tez orada sizga bog'lanamiz!",
            reply_markup=user_builder({
                "🏠 Bosh menyu": {"section": "main"}
            })
        )
    elif order.status == "cancelled":
        await call.message.edit_text(
            f"❌ <b>To'lov bekor qilindi</b>\n\n"
            f"📦 Buyurtma #{order_id}",
            reply_markup=user_builder({
                "🔄 Qayta urinish": {"section": "payment"},
                "🏠 Bosh menyu": {"section": "main"}
            })
        )
    else:
        await call.answer("⏳ To'lov hali amalga oshirilmagan", show_alert=True)
