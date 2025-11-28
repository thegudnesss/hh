"""
FastAPI Webhook Server for Click Payment System

Bu server Click to'lov tizimidan webhook so'rovlarini qabul qiladi
va to'lov holatlarini boshqaradi.

Ishga tushirish:
    uvicorn webhook_server.main:app --host 0.0.0.0 --port 8000 --reload

Production:
    uvicorn webhook_server.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from .database import get_db, init_db, Order
from .handlers import CustomClickWebhookHandler

# .env faylini yuklash
load_dotenv("bot/data/.env")

# FastAPI app yaratish
app = FastAPI(
    title="Payment Webhook Server",
    description="Click to'lov tizimi uchun webhook server",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """
    Server ishga tushganda database'ni initialize qilish
    """
    print("🚀 Starting webhook server...")
    init_db()
    print("✅ Server ready!")


@app.get("/")
async def root():
    """
    Server health check
    """
    return {
        "status": "ok",
        "message": "Payment webhook server is running",
        "endpoints": {
            "click_webhook": "/payments/click/webhook",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}


@app.post("/payments/click/webhook")
async def click_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Click webhook endpoint

    Click to'lov tizimi bu endpoint'ga prepare va complete so'rovlarini yuboradi.

    Bu URL'ni Click merchant kabinetida webhook URL sifatida sozlash kerak:
    https://your-domain.com/payments/click/webhook
    """
    try:
        # Click'dan kelgan ma'lumotlarni olish
        # Click JSON yoki form-data yuborishi mumkin
        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            params = await request.json()
        else:
            # Form data
            form_data = await request.form()
            params = dict(form_data)

        print(f"📥 Received webhook: {params}")

        # Webhook handlerni yaratish
        handler = CustomClickWebhookHandler(
            db=db,
            service_id=os.getenv("CLICK_SERVICE_ID"),
            secret_key=os.getenv("CLICK_SECRET_KEY"),
            account_model=Order,
            account_field='order_id',
            amount_field='total_amount'
        )

        # Webhook'ni qayta ishlash
        response = await handler.handle_webhook(request)

        print(f"📤 Response: {response}")

        return response

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": -1,
                "error_note": f"Internal server error: {str(e)}"
            }
        )


@app.get("/orders/{order_id}")
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """
    Order statusini tekshirish (debug uchun)
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order.order_id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "status": order.status,
        "payment_method": order.payment_method,
        "created_at": order.created_at.isoformat()
    }


@app.get("/orders")
async def get_orders(
    skip: int = 0,
    limit: int = 10,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Barcha orderlarni ko'rish (debug uchun)
    """
    query = db.query(Order)

    if status:
        query = query.filter(Order.status == status)

    orders = query.offset(skip).limit(limit).all()

    return {
        "total": query.count(),
        "orders": [
            {
                "order_id": order.order_id,
                "user_id": order.user_id,
                "total_amount": order.total_amount,
                "status": order.status,
                "payment_method": order.payment_method,
                "created_at": order.created_at.isoformat()
            }
            for order in orders
        ]
    }


@app.post("/api/create_order")
async def create_order(
    order_data: dict,
    db: Session = Depends(get_db)
):
    """
    Telegram botdan order yaratish uchun API endpoint
    """
    try:
        # Order mavjudligini tekshirish
        existing_order = db.query(Order).filter(
            Order.order_id == order_data["order_id"]
        ).first()

        if existing_order:
            return {
                "status": "exists",
                "message": "Order already exists",
                "order_id": existing_order.order_id
            }

        # Yangi order yaratish
        new_order = Order(
            order_id=order_data["order_id"],
            user_id=order_data["user_id"],
            products=order_data["products"],
            total_amount=order_data["total_amount"],
            status=order_data["status"],
            payment_method=order_data.get("payment_method")
        )

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        return {
            "status": "success",
            "message": "Order created successfully",
            "order_id": new_order.order_id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create order: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting webhook server on http://0.0.0.0:8000")
    print("📝 Webhook URL: http://0.0.0.0:8000/payments/click/webhook")
    print("🔍 Health check: http://0.0.0.0:8000/health")

    uvicorn.run(
        "webhook_server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
