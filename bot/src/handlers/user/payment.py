from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from motor.core import AgnosticDatabase as MDB
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest
import httpx
from datetime import datetime

from paytechuz.gateways.click import ClickGateway

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

    # SQLite (webhook server) ga ham orderni saqlash
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8000/api/create_order",
                json={
                    "order_id": order_id,
                    "user_id": user.id,
                    "products": user.savat,
                    "total_amount": float(total_amount),
                    "status": "pending",
                    "payment_method": "click"
                },
                timeout=5.0
            )
    except Exception as e:
        print(f"⚠️ SQLite order creation failed: {e}")

    # Click to'lov linkini yaratish
    try:
        click = ClickGateway(
            service_id=config.CLICK_SERVICE_ID,
            merchant_id=config.CLICK_MERCHANT_ID,
            merchant_user_id=config.CLICK_MERCHANT_USER_ID,
            secret_key=config.CLICK_SECRET_KEY.get_secret_value() if config.CLICK_SECRET_KEY else "",
            is_test_mode=config.CLICK_TEST_MODE
        )
        info = await bot.get_me()
        payment_link = click.create_payment(
            id=order_id,
            amount=total_amount,
            return_url=f"https://t.me/{info.username}  "  # O'z bot username'ingizni kiriting
        )

        # To'lov tugmalarini yaratish
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Click orqali to'lash", url=payment_link.get("payment_url"))],
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
