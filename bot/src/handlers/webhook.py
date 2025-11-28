"""
Click Webhook Handler

Bu fayl Click to'lov tizimidan kelgan webhook so'rovlarini qayta ishlash uchun mo'ljallangan.

MUHIM: Bu kodni ishlatish uchun quyidagi variantlardan birini tanlang:

1. FastAPI bilan (tavsiya etiladi):
   - Alohida FastAPI server yarating
   - Ushbu handlerni FastAPI endpoint sifatida ulang

2. Aiogram webhook bilan:
   - Aiogram'ning webhook funksiyasidan foydalaning
   - Custom path yaratib, ushbu handlerni ulang

Webhook URL: https://your-domain.com/payments/click/webhook
"""

from motor.core import AgnosticDatabase as MDB
from datetime import datetime


class ClickWebhookHandler:
    """
    Click webhook handlerni qayta ishlash uchun klass
    """

    def __init__(self, db: MDB, service_id: str, secret_key: str):
        self.db = db
        self.service_id = service_id
        self.secret_key = secret_key

    async def verify_signature(self, params: dict) -> bool:
        """
        Click'dan kelgan so'rovning imzosini tekshirish
        """
        import hashlib

        # Click imzo algoritmi
        sign_string = (
            f"{params.get('click_trans_id')}"
            f"{params.get('service_id')}"
            f"{self.secret_key}"
            f"{params.get('merchant_trans_id')}"
            f"{params.get('amount')}"
            f"{params.get('action')}"
            f"{params.get('sign_time')}"
        )

        generated_sign = hashlib.md5(sign_string.encode()).hexdigest()
        return generated_sign == params.get('sign_string')

    async def prepare(self, params: dict) -> dict:
        """
        Prepare - to'lovni tayyorlash (1-qadami)
        Click to'lov amalga oshirishdan oldin orderning mavjudligini tekshiradi
        """
        order_id = int(params.get('merchant_trans_id', 0))
        amount = float(params.get('amount', 0))

        # Orderni topish
        order = await self.db.orders.find_one({"order_id": order_id})

        if not order:
            return {
                "error": -5,
                "error_note": "Order not found"
            }

        if order.status == "paid":
            return {
                "error": -4,
                "error_note": "Already paid"
            }

        if order.total_amount != amount:
            return {
                "error": -2,
                "error_note": "Incorrect amount"
            }

        return {
            "error": 0,
            "error_note": "Success",
            "click_trans_id": params.get('click_trans_id'),
            "merchant_trans_id": order_id,
            "merchant_prepare_id": order_id
        }

    async def complete(self, params: dict) -> dict:
        """
        Complete - to'lovni yakunlash (2-qadami)
        To'lov muvaffaqiyatli amalga oshirilganda chaqiriladi
        """
        order_id = int(params.get('merchant_trans_id', 0))

        # Orderni topish
        order = await self.db.orders.find_one({"order_id": order_id})

        if not order:
            return {
                "error": -5,
                "error_note": "Order not found"
            }

        if order.status == "paid":
            return {
                "error": 0,
                "error_note": "Already paid",
                "click_trans_id": params.get('click_trans_id'),
                "merchant_trans_id": order_id,
                "merchant_confirm_id": order_id
            }

        # Orderni yangilash
        await self.db.orders.update_one(
            {"order_id": order_id},
            {
                "status": "paid",
                "payment_method": "click"
            }
        )

        # Foydalanuvchining order_count'ini oshirish
        await self.db.users.update_one(
            {"id": order.user_id},
            {"$inc": {"order_count": 1}}
        )

        return {
            "error": 0,
            "error_note": "Success",
            "click_trans_id": params.get('click_trans_id'),
            "merchant_trans_id": order_id,
            "merchant_confirm_id": order_id
        }

    async def handle_webhook(self, params: dict) -> dict:
        """
        Asosiy webhook handler
        Click'dan kelgan so'rovlarni qayta ishlaydi
        """
        # Imzoni tekshirish
        if not await self.verify_signature(params):
            return {
                "error": -1,
                "error_note": "Invalid signature"
            }

        action = params.get('action')

        if action == 0:  # Prepare
            return await self.prepare(params)
        elif action == 1:  # Complete
            return await self.complete(params)
        else:
            return {
                "error": -3,
                "error_note": "Action not found"
            }


# FastAPI bilan ishlatish uchun namuna
"""
from fastapi import FastAPI, Request, Depends
from sqlalchemy.orm import Session

app = FastAPI()

async def get_db():
    # MongoDB connection
    from src.loader import dbname
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient()
    db = client.dbname
    yield db

@app.post("/payments/click/webhook")
async def click_webhook(request: Request, db = Depends(get_db)):
    from src.config import config

    params = await request.json()

    handler = ClickWebhookHandler(
        db=db,
        service_id=config.CLICK_SERVICE_ID,
        secret_key=config.CLICK_SECRET_KEY.get_secret_value()
    )

    result = await handler.handle_webhook(params)
    return result
"""
