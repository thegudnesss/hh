"""
Webhook handlers for Click payment system
"""

from sqlalchemy.orm import Session
from paytechuz.integrations.fastapi import ClickWebhookHandler
from motor.motor_asyncio import AsyncIOMotorClient

from .database import Order
import os
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv("bot/data/.env")

# MongoDB client
mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
mongo_db = mongo_client.dbname


class CustomClickWebhookHandler(ClickWebhookHandler):
    """
    Custom Click webhook handler
    To'lov muvaffaqiyatli yoki bekor qilingan holatlarni boshqaradi
    """

    def successfully_payment(self, params, transaction):
        """
        To'lov muvaffaqiyatli amalga oshirilganda chaqiriladi
        """
        # SQLite'dagi orderni yangilash
        order = self.db.query(Order).filter(Order.order_id == transaction.account_id).first()
        if order:
            order.status = "paid"
            order.payment_method = "click"
            self.db.commit()

            print(f"✅ Payment successful for Order #{order.order_id}")

            # MongoDB'dagi orderni ham yangilash (async)
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._update_mongo_order(order.order_id, order.user_id))
                loop.close()
            except Exception as e:
                print(f"⚠️ MongoDB update failed: {e}")

    def cancelled_payment(self, params, transaction):
        """
        To'lov bekor qilingan holatni boshqaradi
        """
        # SQLite'dagi orderni yangilash
        order = self.db.query(Order).filter(Order.order_id == transaction.account_id).first()
        if order:
            order.status = "cancelled"
            self.db.commit()

            print(f"❌ Payment cancelled for Order #{order.order_id}")

            # MongoDB'dagi orderni ham yangilash
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._update_mongo_order_cancelled(order.order_id))
                loop.close()
            except Exception as e:
                print(f"⚠️ MongoDB update failed: {e}")

    async def _update_mongo_order(self, order_id: int, user_id: int):
        """
        MongoDB'dagi orderni yangilash
        """
        # Order statusini yangilash
        await mongo_db.orders.update_one(
            {"order_id": order_id},
            {"$set": {"status": "paid", "payment_method": "click"}}
        )

        # Foydalanuvchi savatini tozalash va order_count'ni oshirish
        await mongo_db.users.update_one(
            {"id": user_id},
            {
                "$set": {"savat": []},
                "$inc": {"order_count": 1}
            }
        )

        print(f"✅ MongoDB updated for User #{user_id}")

    async def _update_mongo_order_cancelled(self, order_id: int):
        """
        MongoDB'dagi bekor qilingan orderni yangilash
        """
        await mongo_db.orders.update_one(
            {"order_id": order_id},
            {"$set": {"status": "cancelled"}}
        )

        print(f"❌ MongoDB order cancelled #{order_id}")
