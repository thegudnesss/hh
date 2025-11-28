from aiogram import Router, F

from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from motor.core import AgnosticDatabase as MDB

from contextlib import suppress

from aiogram.filters import CommandStart

from aiogram.exceptions import TelegramBadRequest

from src.filters.chattype import ChatTypeFilter

from src.utils.keyboards import user_builder

from src.utils.pagination import Pagination

from src.utils.callbackdata import UserMenuCallback

router = Router()
router.message.filter(ChatTypeFilter(private=True))
router.callback_query.filter(ChatTypeFilter(private=True))


@router.message(CommandStart())
@router.callback_query(UserMenuCallback.filter(F.section == "main"))
async def cmd_start(union: Message | CallbackQuery, user):
    message = union if isinstance(union, Message) else union.message
    user_mention = message.from_user.mention_html()
    text_phone = """
‼️Quyidagi tugma orqali telefon raqamingizni qoldiring va botdan to'liq foydalaning!👇
""" 
    
    markup_phone =ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📞Telefon raqamni yuborish!", request_contact=True)]],
    resize_keyboard=True
)
    text = """
🌿 <b>Bulvar</b>ga Xush kelibsiz <b>{user}</b>  — ta’m, qulaylik va ishonch uyg‘unligi!

Bu yerda siz uchun:
🍽️ <b>Eng mazali taomlar</b>,
🚴‍♂️ <b>Tez va ishonchli yetkazib berish</b>,
💳 <b>Qulay to‘lov usullari</b>,
📍 <b>Hamda sizga eng yaqin filial</b> — barchasi bir joyda!

<b>Siz faqat buyurtma bering</b>‼️
<b>Biz uchun har bir buyurtma — bu e’tibor, sifat va g‘amxo‘rlik ifodasi</b>.

👇 Quyidagi tugmalardan birini tanlang va mazali sayohatni boshlang!
"""
    
    if not user.phone_number:
        await message.answer(text=text_phone.format(user=user_mention), reply_markup=markup_phone)
    else:
        with suppress(TelegramBadRequest):
            await message.delete()
        await message.answer_photo(photo="https://t.me/AniPro_Uzb/387", caption=text.format(user=user_mention), reply_markup=user_builder(
            details={
                "🛍Buyurtma berish": {"section": "category"},
                "🖇Biz haqimizda": {"section": "aboutus"},
                "🛒Savatim": {"section": "cart"}
            },
            row=(1,2)
        ))
        



@router.message(F.contact)
async def contact(message: Message, db: MDB, user):
    await message.delete()
    print(user.phone_number)
    if not user.phone_number:
        user.phone_number = message.contact.phone_number
        await db.users.update_one(dict(id=user.id), user.model_dump())
        await message.answer("✅ | Raqamingiz saqlandi!", reply_markup=ReplyKeyboardRemove())
        await cmd_start(message, user)
    print(user.phone_number)
