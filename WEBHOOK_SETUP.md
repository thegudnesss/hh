# Click To'lov Tizimi - O'rnatish Qo'llanmasi

## 📋 Tizim Arxitekturasi

Bu tizim ikki qismdan iborat:

1. **Telegram Bot (Aiogram)** - MongoDB bilan ishlaydi
2. **Webhook Server (FastAPI)** - SQLite bilan ishlaydi, PayTechUZ integratsiyasi

### Nega ikkita database?

- **MongoDB**: Asosiy bot ma'lumotlari (foydalanuvchilar, mahsulotlar, kategoriyalar)
- **SQLite**: Faqat to'lov transaksiyalari (PayTechUZ bilan integratsiya uchun kerak)

To'lov muvaffaqiyatli bo'lganda, webhook server MongoDB'ni ham yangilaydi.

---

## 🚀 O'rnatish

### 1. Paketlarni o'rnatish

```bash
pip install -r requirements.txt
```

### 2. .env faylini sozlash

`bot/data/.env` faylini yarating va quyidagi ma'lumotlarni kiriting:

```env
# Bot sozlamalari
BOT_TOKEN=your_bot_token_here
MONGO_URL=mongodb://localhost:27017
DB_CHANNEL=your_channel_id

# Click to'lov tizimi sozlamalari
CLICK_SERVICE_ID=your_service_id
CLICK_MERCHANT_ID=your_merchant_id
CLICK_MERCHANT_USER_ID=your_merchant_user_id
CLICK_SECRET_KEY=your_secret_key
CLICK_TEST_MODE=True
```

### 3. Click sozlamalarini olish

1. https://my.click.uz/ ga kiring
2. Merchant kabinetiga o'ting
3. API sozlamalaridan quyidagi ma'lumotlarni oling:
   - Service ID
   - Merchant ID
   - Merchant User ID
   - Secret Key

---

## 🔧 Ishga Tushirish

### 1. Webhook Serverni ishga tushirish

```bash
# Terminal 1
python -m uvicorn webhook_server.main:app --host 0.0.0.0 --port 8000 --reload
```

Server ishga tushganda database avtomatik yaratiladi: `payments.db`

### 2. Botni ishga tushirish

```bash
# Terminal 2
cd bot
python main.py
```

---

## 🌐 Webhook URL'ni sozlash

### Development (Mahalliy test uchun)

1. **ngrok** o'rnating:
```bash
ngrok http 8000
```

2. ngrok sizga public URL beradi:
```
https://abc123.ngrok.io
```

3. Bu URL'ni Click kabinetida webhook URL sifatida sozlang:
```
https://abc123.ngrok.io/payments/click/webhook
```

### Production

1. Serveringizni domain bilan sozlang (masalan: `https://yourdomain.com`)
2. SSL sertifikat o'rnating (Let's Encrypt)
3. Webhook URL'ni Click kabinetida sozlang:
```
https://yourdomain.com/payments/click/webhook
```

4. Serverni production rejimda ishga tushiring:
```bash
uvicorn webhook_server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📁 Fayl Strukturasi

```
client 3/
├── bot/
│   ├── src/
│   │   ├── handlers/
│   │   │   ├── user/
│   │   │   │   ├── payment.py      # To'lov handlerlari
│   │   │   │   └── menu.py
│   │   │   └── webhook.py          # (eski, ishlatilmaydi)
│   │   ├── database/
│   │   │   ├── models/
│   │   │   │   └── user.py         # Order modeli
│   │   │   └── collections.py
│   │   └── config.py               # Click sozlamalari
│   ├── data/
│   │   ├── .env                    # Sozlamalar
│   │   └── .env.example
│   └── main.py
├── webhook_server/                  # FastAPI webhook server
│   ├── __init__.py
│   ├── main.py                      # FastAPI app
│   ├── database.py                  # SQLAlchemy database
│   ├── handlers.py                  # Click webhook handlerlari
│   └── setup_db.py
├── requirements.txt
├── payments.db                      # SQLite database (avtomatik yaratiladi)
└── WEBHOOK_SETUP.md                # Bu fayl
```

---

## 🔄 Qanday Ishlaydi?

### 1. Order yaratish

```
Foydalanuvchi → Savatga qo'shish → "💳 To'lash" tugmasi
                ↓
    MongoDB: Order yaratiladi
                ↓
    SQLite: Order yaratiladi (API orqali)
                ↓
    Click: To'lov linki yaratiladi
                ↓
    Foydalanuvchi: To'lov sahifasiga yo'naltiriladi
```

### 2. To'lov jarayoni

```
Foydalanuvchi → Click sahifasida to'lov qiladi
                ↓
Click → Webhook: /payments/click/webhook
                ↓
    1. Prepare (tekshirish)
    2. Complete (to'lovni tasdiqlash)
                ↓
Webhook Server → MongoDB'ni yangilaydi
                ↓
    - Order status: "paid"
    - Savat tozalanadi
    - order_count oshiriladi
```

---

## 🧪 Test Qilish

### 1. Webhook serverni tekshirish

```bash
# Health check
curl http://localhost:8000/health

# Barcha orderlar
curl http://localhost:8000/orders

# Bitta order
curl http://localhost:8000/orders/1
```

### 2. Test to'lov

1. Botda mahsulot tanlang
2. Savatga qo'shing
3. "💳 To'lash" tugmasini bosing
4. Click test kartasidan foydalaning:
   - Karta: `8600 4954 0000 0094`
   - Amal qilish muddati: `03/99`
   - SMS kod: `666666`

---

## 🐛 Muammolarni Hal Qilish

### Problem: "Order not found"

**Sabab**: MongoDB'da order bor, lekin SQLite'da yo'q

**Hal qilish**:
```python
# payment.py da SQLite ga order yaratish qismi tekshiring
# http://localhost:8000/api/create_order endpoint ishlab turibmi?
```

### Problem: Webhook ishlamayapti

**Tekshirish**:
1. Webhook server ishlab turibmi? (`http://localhost:8000/health`)
2. ngrok ishlab turibmi? (`http://127.0.0.1:4040` - ngrok dashboard)
3. Click kabinetida webhook URL to'g'rimi?

**Loglarni tekshirish**:
```bash
# Webhook server terminali
# Har bir webhook so'rov logda ko'rinadi:
# 📥 Received webhook: {...}
# 📤 Response: {...}
```

### Problem: MongoDB yangilanmayapti

**Sabab**: `handlers.py` da MongoDB connection xato

**Tekshirish**:
```python
# .env faylidagi MONGO_URL to'g'rimi?
# MongoDB server ishlab turibmi?
```

---

## 🔒 Xavfsizlik

1. **Secret Key**: `.env` faylini hech qachon GitHub'ga yuklang!
2. **Webhook Verification**: Click'dan kelgan so'rovlar imzo bilan tekshiriladi
3. **HTTPS**: Production'da faqat HTTPS ishlatiladi

---

## 📞 Yordam

Agar muammo yuzaga kelsa:

1. Loglarni tekshiring (terminal output)
2. Database'ni tekshiring (`http://localhost:8000/orders`)
3. Click kabinetida test transaksiyalarni ko'ring

---

## 🎯 Keyingi Qadamlar

1. ✅ Paketlarni o'rnating
2. ✅ .env faylini sozlang
3. ✅ Webhook serverni ishga tushiring
4. ✅ Botni ishga tushiring
5. ⏳ ngrok bilan test qiling
6. ⏳ Production serverga deploy qiling
7. ⏳ Click kabinetida webhook URL'ni sozlang

**Omad! 🚀**
