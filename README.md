# 🤖 Telegram Bot + Click To'lov Tizimi

E-commerce Telegram bot Click to'lov integratsiyasi bilan.

## ✨ Xususiyatlar

- 🛒 Mahsulot katalogi va kategoriyalar
- 🛍️ Savat tizimi
- 💳 Click to'lov integratsiyasi
- 📊 Order boshqaruvi
- 👥 Foydalanuvchi va admin paneli
- 📱 MongoDB database
- 🔔 Webhook to'lov bildirimlari

## 📋 Talablar

- Python 3.8+
- MongoDB
- Telegram Bot Token
- Click Merchant Account

## 🚀 Tezkor Boshlash

### 1. Repository'ni klonlash

```bash
git clone <repository-url>
cd "client 3"
```

### 2. Paketlarni o'rnatish

```bash
pip install -r requirements.txt
```

### 3. .env faylini sozlash

`bot/data/.env` faylini yarating:

```env
# Bot
BOT_TOKEN=your_bot_token
MONGO_URL=mongodb://localhost:27017

# Click Payment
CLICK_SERVICE_ID=your_service_id
CLICK_MERCHANT_ID=your_merchant_id
CLICK_MERCHANT_USER_ID=your_user_id
CLICK_SECRET_KEY=your_secret_key
CLICK_TEST_MODE=True
```

### 4. Webhook serverni ishga tushirish

Windows:
```bash
start_webhook.bat
```

Linux/Mac:
```bash
chmod +x start_webhook.sh
./start_webhook.sh
```

Yoki qo'lda:
```bash
python -m uvicorn webhook_server.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Botni ishga tushirish

```bash
cd bot
python main.py
```

## 📖 To'liq Qo'llanma

To'liq o'rnatish va sozlash qo'llanmasi uchun qarang: [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md)

## 🏗️ Arxitektura

```
┌─────────────────┐
│  Telegram Bot   │
│   (Aiogram)     │
│   MongoDB       │
└────────┬────────┘
         │
         │ HTTP
         │
┌────────▼────────┐
│ Webhook Server  │
│   (FastAPI)     │
│   SQLite        │
└────────┬────────┘
         │
         │ Webhook
         │
┌────────▼────────┐
│  Click Payment  │
│    Gateway      │
└─────────────────┘
```

## 📁 Struktura

```
client 3/
├── bot/                        # Telegram bot
│   ├── src/
│   │   ├── handlers/          # Handler'lar
│   │   ├── database/          # Database models
│   │   ├── utils/             # Yordamchi funksiyalar
│   │   └── config.py          # Sozlamalar
│   └── main.py                # Bot entry point
├── webhook_server/            # FastAPI webhook server
│   ├── main.py               # FastAPI app
│   ├── database.py           # SQLAlchemy models
│   └── handlers.py           # Webhook handlers
├── requirements.txt          # Python dependencies
├── start_webhook.bat         # Windows start script
├── start_webhook.sh          # Linux/Mac start script
├── WEBHOOK_SETUP.md         # Setup guide
└── README.md                # Bu fayl
```

## 🔧 Development

### Database'ni tozalash

```bash
# SQLite
rm payments.db

# MongoDB
mongo
> use dbname
> db.dropDatabase()
```

### Loglarni ko'rish

Webhook server:
```bash
# Terminal'da avtomatik ko'rsatiladi
📥 Received webhook: {...}
📤 Response: {...}
```

### Test to'lov

Click test kartasi:
- Karta: `8600 4954 0000 0094`
- Muddat: `03/99`
- SMS: `666666`

## 🐛 Troubleshooting

Tafsilotlar uchun: [WEBHOOK_SETUP.md#Muammolarni-Hal-Qilish](WEBHOOK_SETUP.md#🐛-muammolarni-hal-qilish)

## 📝 API Endpoints

### Webhook Server

- `GET /` - Server info
- `GET /health` - Health check
- `POST /payments/click/webhook` - Click webhook
- `GET /orders` - Barcha orderlar
- `GET /orders/{order_id}` - Bitta order
- `POST /api/create_order` - Order yaratish (bot uchun)

### Misol

```bash
# Health check
curl http://localhost:8000/health

# Orderlarni ko'rish
curl http://localhost:8000/orders

# Bitta orderni ko'rish
curl http://localhost:8000/orders/1
```

## 🔒 Xavfsizlik

- ⚠️ `.env` faylini GitHub'ga yuklang!
- ⚠️ Production'da `CLICK_TEST_MODE=False` qiling
- ⚠️ HTTPS ishlatiladi (ngrok yoki SSL sertifikat)
- ✅ Webhook'lar imzo bilan tekshiriladi

## 📞 Yordam

Savollar uchun:
1. [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md) ni o'qing
2. Loglarni tekshiring
3. GitHub Issues

## 📄 License

MIT License

## 🙏 Minnatdorchilik

- [Aiogram](https://github.com/aiogram/aiogram) - Telegram Bot Framework
- [FastAPI](https://github.com/tiangolo/fastapi) - Web Framework
- [PayTechUZ](https://github.com/PayTechUz/paytechuz) - Payment Integration

---

**Muvaffaqiyatli to'lovlar! 💰**
