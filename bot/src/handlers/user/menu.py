from aiogram import Router, F, Bot

from aiogram.types import CallbackQuery, LabeledPrice, PreCheckoutQuery

from aiogram.exceptions import TelegramBadRequest

from motor.core import AgnosticDatabase as MDB

from contextlib import suppress

from typing import Dict, List

from src.utils.callbackdata import UserMenuCallback

from src.utils.pagination import Pagination

from src.utils.keyboards import user_builder

from src.utils.helper import build_cart_text

from src.database.models.user import Categories, User

from src.filters.chattype import ChatTypeFilter

router = Router()
router.message.filter(ChatTypeFilter(private=True))
router.callback_query.filter(ChatTypeFilter(private=True))

# @router.callback_query(UserMenuCallback.filter())
# async def _(call: CallbackQuery, callback_data: UserMenuCallback):
#     print(callback_data)


@router.callback_query(UserMenuCallback.filter(F.section == "category"))
async def show_menu(call: CallbackQuery, callback_data: UserMenuCallback, db: MDB):
    
    categories = await db.categories.find({})
    print(categories)
    if not categories:
        with suppress(TelegramBadRequest):
            await call.message.delete()
        await call.message.answer("Hozircha kategoriya mavjud emas 😔", reply_markup=user_builder({"🔙ortga": {"section": "main"}}))
        return
    
    details = {}
    for cat in categories:
        details[cat.name] = {
            "category_id": cat.category_id,
            "action":"show"
        }

    # Keyboard yaratish (har qatorda 2 ta tugma)
    kb = user_builder(details=details, row=2)
    footer = user_builder({
        "🏠 Bosh menyu": {"section": "main"}
    },row=2)
    kb.inline_keyboard += footer.inline_keyboard
    # Foydalanuvchiga jo'natish
    with suppress(TelegramBadRequest):
        await call.message.delete()
    await call.message.answer(
        "🛒 Kategoriyalarni tanlang:",
        reply_markup=kb
    )

@router.callback_query(UserMenuCallback.filter(F.category_id & F.action=="show"))
@router.callback_query(UserMenuCallback.filter(F.action == "pagination"))
@router.callback_query(UserMenuCallback.filter(F.category_id & F.action=="add"))
async def category(call: CallbackQuery, callback_data: UserMenuCallback, db: MDB, user):
    category_id = callback_data.category_id
    page = callback_data.page or 1  # default 1

    savat_text = None
    if callback_data.action == "add":
        await add_to_cart(call, callback_data, db, user)


    # Kategoriya ma'lumotini olish
    info = await db.categories.find_one({"category_id": category_id})
    if not info or not info.products:
        await call.message.edit_text(
            f"{info.name if info else 'Bu'} categoriysida mahsulotlar mavjud emas",
            reply_markup=user_builder({"🔙ortga": "category"})
        )
        return

    # Mahsulotlarni olish
    products = await db.products.find({"id": {"$in": info.products}})
    if not products:
        await call.message.edit_text(
            "Mahsulotlar mavjud emas",
            reply_markup=user_builder({"🔙ortga": "category"})
        )
        return

    # Pagination obyektini yaratish
    pagination = Pagination(
        objects=products,
        page_data=lambda p: UserMenuCallback(
            category_id=category_id,
            action="pagination",
            page=p
        ).pack(),
        item_data=lambda item, _: UserMenuCallback(
            section="product",
            action="view",
            product_id=item.id,  # Pydantic model maydonidan foydalanish
            category_id=category_id,
            page=_
        ).pack(),
        item_title=lambda item, _: item.title  # Pydantic model maydonidan foydalanish
    )

    # InlineKeyboard yaratish
    keyboard = pagination.create(page=page, lines=10, columns=2)

    # Footer tugmalar (orqaga / bosh menyu)
    savat_text = await build_cart_text(user, db)
    text = (
    f"✅ | birini tanlang!\n\n{info.name}"
    if not savat_text
    else f"{savat_text}\n\n✅ | Kategoriyalardan birini tanlang!\n\n{info.name}")

    if savat_text:
        footer = user_builder({
        "🛒Savatim": {"section": "cart"},
        "🔙 Orqaga": {"section": "category"},
        "🏠 Bosh menyu": {"section": "main"}
    },row=(1,2))
        
    else:
        footer = user_builder({
        "🔙 Orqaga": {"section": "category"},
        "🏠 Bosh menyu": {"section": "main"}
    },row=(2))
    keyboard.inline_keyboard += footer.inline_keyboard


    if callback_data.action == "pagination":
        with suppress(TelegramBadRequest):
            await call.message.edit_reply_markup(reply_markup=keyboard)
            return
    with suppress(TelegramBadRequest):
        await call.message.delete()
    if not info.photo:
        await call.message.answer(text=text, reply_markup=keyboard)
        return
    await call.message.answer_photo(
        photo=info.photo,
        caption=text,
        reply_markup=keyboard
    )

@router.callback_query(UserMenuCallback.filter((F.section=="product") & (F.product_id) & ((F.action=="view") | ((F.action=="increase") | (F.action=="decrease"))) ))
async def info_product(call: CallbackQuery, callback_data: UserMenuCallback, db: MDB):
    product_id = callback_data.product_id
    info = await db.products.find_one(dict(id=product_id))
    order_count = callback_data.order_count or 1
    count = order_count if order_count>=1 else 1

    
    markup = user_builder(
        {
            "➖🔟": {"section":"product", "action": "decrease", "product_id": product_id, "order_count": count-10, "category_id": callback_data.category_id, "page": callback_data.page},
            "➖": {"section":"product", "action": "decrease", "product_id": product_id, "order_count": count-1, "category_id": callback_data.category_id, "page": callback_data.page},
            str(count) : {"section":"product", "action": "ignore"},
            "➕": {"section":"product", "action": "increase", "product_id": product_id, "order_count": count+1, "category_id": callback_data.category_id, "page": callback_data.page},
            "➕🔟": {"section":"product", "action": "increase", "product_id": product_id, "order_count": count+10, "category_id": callback_data.category_id, "page": callback_data.page},
            "🛒 Savatga qo'shish": {"section": "product", "action": "add", "product_id": product_id, "order_count": count, "category_id": callback_data.category_id},
            "🔙 Orqaga": {"category_id": callback_data.category_id, "action": "show", "page": callback_data.page },
            "🏠 Bosh menyu": {"section": "main"}
        },
        row=(5,1,2)
    )
    text = f"<b>{info.title}</b>\n\nTavsif: {info.description}\n\n Mahsulot narxi:\n{info.price:,}✖️{count}={eval(f"{info.price}*{count}"):,} So'm"
    print(callback_data.category_id)
    print(callback_data.page)
    if not callback_data.action == "view":
        with suppress(TelegramBadRequest):
            await call.message.edit_caption(caption=text, reply_markup=markup)
            return
    if callback_data.action == "view":
        with suppress(TelegramBadRequest):
            await call.message.delete()
        await call.message.answer_photo(photo=info.photo, caption=text, reply_markup=markup)
    await call.answer("Minimum 1")
    return


async def add_to_cart(call: CallbackQuery, callback_data: UserMenuCallback, db: MDB, user):
    """
    Foydalanuvchining savatiga mahsulot qo‘shish yoki miqdorini oshirish.
    Middleware orqali kelgan `user` bazadagi ma'lumotlarni ifodalaydi.
    """
    product_id = callback_data.product_id
    count = callback_data.order_count
    category_id = callback_data.category_id

    # Foydalanuvchining hozirgi savati (agar mavjud bo‘lmasa, bo‘sh list bilan boshlaymiz)
    savat = list(user.savat or [])
    updated = False

    for item in savat:
        if item["product_id"] == product_id:
            item["count"] += count
            updated = True
            break

    if not updated:
        savat.append({"product_id": product_id, "count": count})

    # DRY prinsipida faqat o‘zgargan maydonni yangilaymiz
    await db.users.update_one(
        {"id": user.id},
        {"savat": savat}
    )

    await call.answer("🛒 Mahsulot savatga qo‘shildi!", show_alert=False)


@router.callback_query(UserMenuCallback.filter(F.section=="cart"))
async def cart(call: CallbackQuery, callback_data: UserMenuCallback, db: MDB, user):
    text = await build_cart_text(user, db)
    if not text:
        await call.message.answer("‼️ | Hozircha savatingiz bo'sh!\n\n✅ | Pastdagi tugma orqali categoriyaga o'tib mahsulotni va miqdorini kiriting!", reply_markup=user_builder(
            {"🛒 Savatni to'ldirish" : {"section": "category"}}
        ))
    with suppress(TelegramBadRequest):
        await call.message.delete()
    

    await call.message.answer(text, reply_markup=user_builder(
        {
            "💳 To'lash": {"section": "payment"},
            "🏠 Bosh menyu": {"section": "main"}
        },
        row=(1, 1)
    ))