import random

from contextlib import suppress

from aiogram import Router, F

from aiogram.types import Message, CallbackQuery

from aiogram.filters import Command 

from aiogram.fsm.context import FSMContext

from aiogram.exceptions import TelegramBadRequest

from src.config import config

from src.filters.chattype import ChatTypeFilter
from src.filters.basic import IsAdmin

from motor.core import AgnosticDatabase as MDB

from src.utils.keyboards import admin_builder
from src.utils.callbackdata import AdminMenuCallback
from src.utils.states import AdminAddState, CategoryAddState, ProductAddState, CategoryEditState, ProductEditState, PushState
from src.utils.pagination import Pagination

from src.utils.helper import mass_broadcast, format_broadcast_report, create_progress_callback

from src.database.models.user import Admin, Categories, Products

from src.loader import bot


router = Router()
router.message.filter(ChatTypeFilter(private=True))
router.callback_query.filter(ChatTypeFilter(private=True))
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

@router.message(Command("admin"))
@router.callback_query(AdminMenuCallback.filter(F.section=="main"))
async def admin_menu(union: Message | CallbackQuery, state: FSMContext, user):
    await state.clear()
    message = union if isinstance(union, Message) else union.message
    text = "Admin menyusiga xush kelibsiz!"
    markup = admin_builder(
        {"Admin qo'shish ➕": {"section": "add_admin"}, "Admin o'chirish ➖":{"section": "del_admin"},
        "Category qo'shish ➕": {"section": "add_category"}, "Category o'chirish ➖" : {"section": "del_category"},
        "Category tahrirlash 🛠️": {"section": "edit_category"},
        "Mahsulot qo'shish 🍜": {"section": "add_product"},
        "Mahsulot o'chirish ➖": {"section": "del_product"},
        "Mahsulot tahrirlash 🛠️": {"section": "edit_product"},
        "Boshqaruv paneli 🔑" : {"section": "main", "page": 2}
        }
        , row=(2,2,2,2,1))
    
    
    if isinstance(union, CallbackQuery):
        data = union.data.split(":")
        print(data[7])
        if data[7]=="2":

            markup = admin_builder(
            {
                "Post yuborish 📬": {"section": "push_menu"},
                "Orqaga🔙": {"section": "main"}
            }
        )
        try:
            await message.edit_text(text, reply_markup=markup)
        except:
            await message.delete()
            await message.answer(text=text, reply_markup=markup)
    else:
        await message.delete()
        await message.answer(text, reply_markup=markup)

@router.callback_query(AdminMenuCallback.filter(F.section == "push_menu"))
async def push_menu(call: CallbackQuery, callback_data: AdminMenuCallback):
    markup = admin_builder({
        "Anonim Xabar 🔏": {"section": "push", "action": "anonim"},
        "Uzatilgan xabar(premium emoji)📨" : {"section": "push", "action": "forward"},
        "ortga🔙": {"section":"main", "page": "2"}, "Bosh menu🏡" : {"section":"main"}
    },row=2)
    await call.message.edit_text("📬 | Xabar yuborish usulini tanlang!", reply_markup=markup)

@router.callback_query(AdminMenuCallback.filter(F.section == "push"))
async def push_anonim(call: CallbackQuery, callback_data: CallbackQuery,state: FSMContext):
    text = "Yubormoqchi bo'lgan xabaringizni yuboring!\n\n‼️Eslatma: Xabar yuborilganda adminning ismi ko‘rinmaydi (Anonim yuborish)‼️"
    markup = admin_builder(details={"ortga🔙": {"section":"push_menu"}})
    
    await call.message.edit_text(
        text=text,
        reply_markup=markup
    )
    await state.update_data(action=callback_data.action)
    await state.set_state(PushState.INPUT)

# ↑ helper faylga siz bergan funksiyalarni joylashtirgansiz deb hisoblayman
@router.message(PushState.INPUT)
async def push_message(message: Message, state: FSMContext, db: MDB):

    data = await state.get_data()

    # Xabarni DB kanalga saqlaymiz
    saved = await message.copy_to(config.DB_CHANNEL)
    await message.delete() if data["action"]=="anonim" else None

    # Admin oynasiga preview

    # Barcha userlar
    users = await db.users.find({})
    user_ids = [u.id for u in users]

    # 1. Admin uchun boshlangich progress xabari
    progress_message = await message.answer(
        f"🚀 *Tarqatish boshlandi!*\n"
        f"👥 Foydalanuvchilar: `{len(user_ids)}`\n\n"
        f" Yuborilmoqda...",
        parse_mode="Markdown"
    )

    # 2. realtime progress callback
    progress_callback = await create_progress_callback(progress_message)

    # 3. broadcastni boshlaymiz

    result = await mass_broadcast(
        bot=bot,
        user_ids=user_ids,
        send_func=bot.copy_message if data["action"]=="anonim" else bot.forward_message,
        from_chat_id=config.DB_CHANNEL if data["action"]=="anonim" else message.chat.id,
        message_id=saved.message_id if data["action"]=="anonim" else message.message_id,
        progress_callback=progress_callback,
        chunk_size=50,
        delay=0.05
    )

    # 4. Final natija
    await progress_message.edit_text(
        format_broadcast_report(result),
        parse_mode="Markdown"
    )

    await state.clear()


@router.callback_query(AdminMenuCallback.filter(F.section == "add_admin"))
async def add_admin(message: CallbackQuery, state: FSMContext):
    text = "Yangi Adminning telegram ID'si yoki undan xabar forward qiling!"
    markup = admin_builder(details={"ortga🔙": "main"})
    try:
        await message.message.edit_text(
        text=text,
        reply_markup=markup
    )
    except:
        await message.message.delete()
        await message.message.answer(text=text, reply_markup=markup)

    await state.set_state(AdminAddState.INPUT)


@router.message(AdminAddState.INPUT)
async def admin_id(message: Message, state: FSMContext, db: MDB):
    await message.delete()

    # --- STEP 1: ID ni tekshirish
    if message.forward_date:
        if message.forward_from:
            user_id = message.forward_from.id 
            print(user_id)
        else:
            await message.answer("⚠️ Ushbu foydalanuvchining 'forward privacy' sozlamasi yoqilgan.\n"
                "Uning ID'sini avtomatik aniqlab bo‘lmadi.\n\n"
                "❗ Iltimos, foydalanuvchining <b>ID</b>* raqamini qo‘lda kiriting.**")
            print(1)
            return
    
    elif not message.text or not message.text.isdigit():
        print(2)
        await message.answer("❌ ID faqat sondan iborat bo'lishi kerak!\nIltimos, qayta kiriting.")
        return
    else: user_id = int(message.text)

    print(3)
    # --- STEP 2: Foydalanuvchini topish
    user = await db.users.find_one({"_id": user_id})
    print(4)
    if not user:
        print(5)
        await message.answer("⚠️ Bu ID bo‘yicha foydalanuvchi topilmadi!\nIltimos, boshqa ID kiriting.")
        return

    # --- STEP 3: Admin mavjudligini tekshirish
    existing_admin = await db.admins.find_one({"_id": user_id})
    print(6)
    if existing_admin:
        print(7)
        await message.answer("ℹ️ Ushbu foydalanuvchi allaqachon admin sifatida ro‘yxatdan o‘tgan.")
        return

    photos = await message.bot.get_user_profile_photos(user_id=user_id, limit=1)
    # --- STEP 4: Admin sifatida qo‘shish

    print(8)
    info = await bot.get_chat(user_id)
    admin = Admin(
        id=user_id
    )
    await db.admins.insert_one(dict(_id=user_id))
    await db.admins.update_one(dict(_id=user_id), dict(admin.model_dump()))
    print(9)
    try: 
        largest_photo = photos.photos[0][-1]
        file_id = largest_photo.file_id
        print(10)
    except:
        file_id = False
        print(11)

    text = f"<b>Status:</b> ✅Muvaffaqiyatli\n\n🪪 <b>Foydalanuvchi nomi:</b> {info.full_name}\n\n💈 <b>Username:</b> @{info.username}\n\n🆔 <b>ID:</b> <code>{info.id}</code>"
    markup = admin_builder({"ortga🔙": {"section":"main"}, "Admin qo'shish ➕": {"section": "add_admin"}})

    await message.answer_photo(photo=file_id, caption=text, reply_markup=markup) if file_id else await message.answer(text, reply_markup=markup)
    print(12)

    # --- STEP 5: State tozalash
    print(13)
    await state.clear()
    
@router.callback_query(AdminMenuCallback.filter(F.section == "del_admin"))
async def list_admins(callback: CallbackQuery, db: MDB):
    admins = await db.admins.find({})
    print(admins)
    
    if not admins:
        await callback.message.edit_text("✖️ Adminlar mavjud emas‼️", reply_markup=admin_builder({"ortga🔙": {"section":"main"}}))
        return
    
    text_lines = []
    details = {}

    for i, admin in enumerate(admins):
        try:
            chat = await bot.get_chat(admin.id)  # Admin haqida to‘liq info olish
            full_name = chat.full_name
        except Exception: 
            full_name = "❓ Noma’lum foydalanuvchi"

        text_lines.append(f"{i+1}. <b>{full_name}</b> — 🆔 <code>{admin.id}</code>")

        # Har bir admin uchun "❌ O‘chirish" tugmasi
        details[f"❌ {i + 1}"] = {
            "action": "delete",
            "id": admin.id
        }
    # 🔳 Inline buttonlar admin_builder() orqali
    details["ortga🔙"] = {"section": "main"}
    markup = admin_builder(details=details, row=3)
    
    text = "‼️O'chirmoqchi bo'lgan adminingizni tanlang‼️\n\n" + "\n".join(text_lines)
    
    await callback.message.edit_text(text=text, reply_markup=markup)

@router.callback_query(AdminMenuCallback.filter(F.action == "delete"))
async def del_admin(callback: CallbackQuery, callback_data: AdminMenuCallback, db: MDB):
    admin_id = callback_data.id
    await db.admins.delete_one({"_id": admin_id})
    await callback.answer(f"Admin {admin_id} o‘chirildi ✅")
    await list_admins(callback, db)

@router.callback_query(AdminMenuCallback.filter(F.section=="add_category"))
async def add_category(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await call.message.edit_text("✅ | Qo'shmoqchi bo'lgan yangi category nomini kiriting\n\n‼️ | Eslatma shunga o'xshash emjilardan foydalaning:\n\n🍔 🍕🍟 🍫🥐🍙🍧🌮🍥🍿🎂🍪🍹🌭🥨", reply_markup=admin_builder(
        {
            "ortga🔙" : {"section": "main"}
        }
    ))
    await state.set_state(CategoryAddState.NAME)

@router.message(CategoryAddState.NAME)
async def category_name(message: Message, db: MDB, state: FSMContext):
    with suppress(TelegramBadRequest):
        await message.delete()
    categories = await db.categories.find({})
    name = message.text
    for i in categories:
        print(i)
        if name == i.name:
            await message.answer(f"‼️ | {name} nomli catgory allaqachon mavjud\n\n✅ | Iltimos boshqa nom yozing!", reply_markup=admin_builder(
                {
                    "Bekor qilish❌": {"section": "main"}
                }
            ))
            return
            break

    rndm = random.randint(1,1000)
    category = Categories(
        name=name,
        category_id=rndm
    )
    await db.categories.insert_one(category.model_dump())
    await message.answer(f"✅ | Category muvaffaqiyatli qo'shildi: {name}", reply_markup=admin_builder(
        {
            "Rasm qo'shish 🖼️" : {"section": "category_picture", "category_id": rndm},
            "Mahsulot qo'shish 🍜" : {"section": "add_product_to_category", "category_id": rndm},
            "ortga🔙" : {"section": "main"},
            "Category qo'shish ➕": {"section": "add_category"},
        },
        row=2
    ))
    
@router.callback_query(AdminMenuCallback.filter(F.section =="category_picture"))
async def addpicture(call: CallbackQuery, callback_data: AdminMenuCallback, db: MDB, state: FSMContext ):
    print(callback_data.category_id)
    await call.message.edit_text("✅ | Category uchun rasm yuboring!", reply_markup=admin_builder(
        {
            "❌Bekor qilish": {"section": "main"}
        }
    ))
    await state.set_data(dict(category_id=callback_data.category_id))
    await state.set_state(CategoryAddState.PHOTO)

@router.message(CategoryAddState.PHOTO)
async def category_photo(message: Message, db: MDB, state: FSMContext):
    if not message.photo:
        await message.answer("❌ | Iltimos rasm yuboring!", reply_markup=admin_builder(
            {
                "❌Bekor qilish": {"section": "main"}
            }
            ))
        return
    data = await state.get_data()
    category = await db.categories.find_one({"category_id": data['category_id']})
    if config.DB_CHANNEL:
        photo = await message.copy_to(config.DB_CHANNEL)
        print(photo.message_id)
        channel = await bot.get_chat(config.DB_CHANNEL)
    category.photo = f"https://t.me/{channel.username}/{photo.message_id}"
        
    await db.categories.update_one({"category_id": category.category_id}, category.model_dump())
    with suppress(TelegramBadRequest):
        await message.delete()
    await message.answer(f"✅ | Category rasmi saqlandi!", reply_markup=admin_builder(
        {
            "ortga🔙" : {"section": "main"},
            "Category qo'shish ➕": {"section": "add_category"},
        },
        row=(1,2)
    ))
    await state.clear()

@router.callback_query(AdminMenuCallback.filter(F.section=="add_product_to_category"))
async def show_product_to_category(call: CallbackQuery, callback_data: AdminMenuCallback, db: MDB):
    category_id = callback_data.category_id
    product_id = callback_data.product_id
    page = callback_data.page or 1
    category = await db.categories.find_one({"category_id": category_id})

    products = await db.products.find({})
    if callback_data.action == "add":
        # Category ga tegishli bo'lmagan mahsulotlarni filtrlash
        category = await db.categories.update_one(
        {"category_id": category_id},
        {"$addToSet": {"products": product_id}})
        await call.message.answer("✅ | Mahsulot category ga qo'shildi!", reply_markup=admin_builder({
            "ortga 🔙": {"section": "main"}
        }))
        return

    if not products:
        await call.message.edit_text(
            "‼️ | Mahsulotlar mavjud emas\n\n✅ | Iltimos yangi mahsulot qo'shing!",
            reply_markup=admin_builder({
                "Mahsulot qo'shish 🍜" : {"section": "add_product", "action": "add"},
                "🔙ortga": {"section": "main"}
                }, row=2)
        )
        return

    # Pagination obyektini yaratish
    pagination = Pagination(
        objects=products,
        page_data=lambda p: AdminMenuCallback(
            category_id=category_id,
            action="add_category",
            page=p
        ).pack(),
        item_data=lambda item, _: AdminMenuCallback(
            section="add_product_to_category",
            action="add",
            product_id=item.id,  # Pydantic model maydonidan foydalanish
            category_id=category_id,
            page=_
        ).pack(),
        item_title=lambda item, _: item.title  # Pydantic model maydonidan foydalanish
    )

    # InlineKeyboard yaratish
    keyboard = pagination.create(page=page, lines=10, columns=2)
    kb = admin_builder(
        {
            "Mahsulot qo'shish 🍜" : {"section": "add_product", "action": "add"},
            "Bekor qilish❌": {"section": "main"}
        },
        row=2
    )
    keyboard.inline_keyboard += kb.inline_keyboard

    await call.message.edit_text(f"✅ | Category uchun mahsulot tanlang yoki yangi mahsulot qo'shing!", reply_markup=keyboard)
    
    
@router.callback_query(AdminMenuCallback.filter(F.section=="del_category"))
async def del_category(call: CallbackQuery, db: MDB):
    categories = await db.categories.find({})
    if not categories:
        await call.message.edit_text("❌ | Categorylar mavjud emas!\n\n✅ | Iltimos yangi category qo'shing!", reply_markup=admin_builder({"Category qo'shish ➕": {"section": "add_category"},"ortga🔙": {"section":"main"}}))
        return
    
    text_lines = []
    details = {}

    for i, category in enumerate(categories):
        text_lines.append(f"{i+1}. <b>{category.name}</b> — 🆔 <code>{category.category_id}</code>")

        # Har bir category uchun "❌ O‘chirish" tugmasi
        details[f"❌ {i + 1}"] = {
            "action": "delete_category",
            "id": category.category_id
        }
    # 🔳 Inline buttonlar admin_builder() orqali

    markup = admin_builder(details=details, row=3)
    kb = admin_builder(
        {
            "ortga🔙": {"section":"main"}
        }
    )
    markup.inline_keyboard += kb.inline_keyboard
    text = "‼️O'chirmoqchi bo'lgan categoryingizni tanlang‼️\n\n" + "\n".join(text_lines)
    
    await call.message.edit_text(text=text, reply_markup=markup)

@router.callback_query(AdminMenuCallback.filter(F.action == "delete_category"))
async def delete_category(callback: CallbackQuery, callback_data: AdminMenuCallback, db: MDB):

    category_id = callback_data.id
    await db.categories.delete_one({"category_id": category_id})
    await callback.answer(f"Category {category_id} o‘chirildi ✅")
    await del_category(callback, db)


@router.callback_query(AdminMenuCallback.filter(F.section=="edit_category"))
async def edit_category(call: CallbackQuery, db: MDB):
    categories = await db.categories.find({})
    if not categories:
        await call.message.edit_text("❌ | Categorylar mavjud emas!\n\n✅ | Iltimos yangi category qo'shing!", reply_markup=admin_builder({"Category qo'shish ➕": {"section": "add_category"},"ortga🔙": {"section":"main"}}))
        return
    
    text_lines = []
    details = {}

    for i, category in enumerate(categories):
        text_lines.append(f"{i+1}. <b>{category.name}</b> — 🆔 <code>{category.category_id}</code>")

        # Har bir category uchun "🛠 Tahrirlash" tugmasi
        details[f"🛠 {i + 1}"] = {
            "category_id": category.category_id,
            "action": "edit_category",
        }
    # 🔳 Inline buttonlar admin_builder() orqali

    markup = admin_builder(details=details, row=3)
    kb = admin_builder(
        {
            "ortga🔙": {"section":"main"}
        }
    )
    markup.inline_keyboard += kb.inline_keyboard
    text = "‼️Tahrirlashni istagan categoryingizni tanlang‼️\n\n" + "\n".join(text_lines)
    
    await call.message.edit_text(text=text, reply_markup=markup)

@router.callback_query(AdminMenuCallback.filter(F.action == "edit_category"))
async def edit_selected_category(callback: CallbackQuery, callback_data: AdminMenuCallback, db: MDB):
    category_id = callback_data.category_id
    category = await db.categories.find_one({"category_id": category_id})
    with suppress(TelegramBadRequest):
        await callback.message.delete()

    if not category.photo:
        markup = admin_builder(
        {
            "Rasm qo'shish 🖼️" : {"section": "category_picture", "category_id": category_id,},
            "Nomini o'zgartirish ✏️" : {"section": "category_edit", "category_id": category_id},
            "Mahsulot qo'shish 🍜" : {"section": "add_product_to_category", "category_id": category_id},
            "ortga🔙" : {"section": "main"},
            "Category qo'shish ➕": {"section": "add_category"},
        },
        row=2
    )
    else:
        markup = admin_builder(
        {
            "Rasm O'zgartirish 🖼️" : {"section": "category_picture", "category_id": category_id},
            "Nomini o'zgartirish ✏️" : {"section": "category_edit", "category_id": category_id},
            "Mahsulot qo'shish 🍜" : {"section": "add_product_to_category", "category_id": category_id},
            "ortga🔙" : {"section": "main"},
            "Category qo'shish ➕": {"section": "add_category"},
        },
        row=2
    )


    await callback.message.answer(f"✅ | Category muvaffaqiyatli tanlandi!: {category.name}", reply_markup=markup)

@router.callback_query(AdminMenuCallback.filter(F.section=="category_edit"))
async def edit_category_name(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await call.message.edit_text(f"✅ | Categoryning yangi nomini kiriting!", reply_markup=admin_builder(
        {
            "Bekor qilish❌" : {"section": "main"}
        }
    ))
    await state.set_data(dict(category_id=callback_data.category_id))
    await state.set_state(CategoryEditState.EDIT)

@router.message(CategoryEditState.EDIT)
async def category_edited(message: Message, db: MDB, state: FSMContext):
    data = await state.get_data()

    category = await db.categories.find_one({"category_id": data['category_id']})

    category.name = message.text

    await db.categories.update_one({"category_id": category.category_id}, category.model_dump())

    with suppress(TelegramBadRequest):
        await message.delete()

    await message.answer(f"✅ | Category nomi muvaffaqiyatli o'zgartirildi!", reply_markup=admin_builder(
        {
            "ortga🔙" : {"section": "main"},
        }
    ))
    await state.clear()

@router.callback_query(AdminMenuCallback.filter(F.section=="add_product"))
async def add_product_menu(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await call.message.edit_text("✅ | Yangi mahsulot uchun nomni kiriting!", reply_markup=admin_builder(
        {
            "Bekor qilish❌" : {"section": "main"}
        }
    ))
    await state.set_state(ProductAddState.TITLE)

@router.message(ProductAddState.TITLE)
async def product_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    with suppress(TelegramBadRequest):
        await message.delete()
    await message.answer("✅ | Mahsulot uchun tavsifni kiriting!", reply_markup=admin_builder(
        {
            "Bekor qilish❌" : {"section": "main"}
        }
    ))
    await state.set_state(ProductAddState.DESCRIPTION)

@router.message(ProductAddState.DESCRIPTION)
async def product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    with suppress(TelegramBadRequest):
        await message.delete()
    await message.answer("✅ | Mahsulot uchun narxni kiriting! (faqat son) mislo: 25000, 50000", reply_markup=admin_builder(
        {
            "Bekor qilish❌" : {"section": "main"}
        }
    ))
    await state.set_state(ProductAddState.PRICE)

@router.message(ProductAddState.PRICE)
async def product_price(message: Message, state: FSMContext, db: MDB):
    if not message.text or not message.text.isdigit():
        await message.answer("❌ | Narx faqat sondan iborat bo'lishi kerak!\nIltimos, qayta kiriting.", reply_markup=admin_builder(
            {
                "Bekor qilish❌" : {"section": "main"}
            }
        ))
        return
    await state.update_data(price=int(message.text))
    data = await state.get_data()
    title = data['title']
    description = data['description']
    price = data['price']
    rndm = random.randint(1,100000)
    product = Products(
        id=rndm,
        title=title,
        description=description,
        price=price
    )
    await db.products.insert_one(product.model_dump())
    with suppress(TelegramBadRequest):
        await message.delete()
    await message.answer(f"✅ | Mahsulot muvaffaqiyatli qo'shildi!: {title}", reply_markup=admin_builder(
        {   
            "Rasm qo'shish 🖼️" : {"section": "product_picture", "product_id": rndm},
            "Mahsulot qo'shish 🍜": {"section": "add_product"},
            "ortga🔙" : {"section": "main"},
        },
        row=(2,1)
    ))
    await state.clear()

@router.callback_query(AdminMenuCallback.filter(F.section=="product_picture"))
async def add_product_picture(call: CallbackQuery, callback_data: AdminMenuCallback, db: MDB, state: FSMContext ):
    print(callback_data.product_id)
    await call.message.edit_text("✅ | Mahsulot uchun rasm yuboring!", reply_markup=admin_builder(
        {
            "❌Bekor qilish": {"section": "main"}
        }
    ))
    await state.set_data(dict(product_id=callback_data.product_id))
    await state.set_state(ProductAddState.PHOTO)

@router.message(ProductAddState.PHOTO)
async def product_photo(message: Message, db: MDB, state: FSMContext):

    if not message.photo:
        await message.answer("❌ | Iltimos rasm yuboring!", reply_markup=admin_builder(
            {
                "❌Bekor qilish": {"section": "main"}
            }
            ))
        return
    data = await state.get_data()
    product = await db.products.find_one({"id": data['product_id']})
    if config.DB_CHANNEL:
        photo = await message.copy_to(config.DB_CHANNEL)
        print(photo.message_id)
        channel = await bot.get_chat(config.DB_CHANNEL)
    product.photo = f"https://t.me/{channel.username}/{photo.message_id}"
        
    await db.products.update_one({"id": product.id}, product.model_dump())
    with suppress(TelegramBadRequest):
        await message.delete()
    await message.answer(f"✅ | Mahsulot rasmi saqlandi!", reply_markup=admin_builder(
        {
            "ortga🔙" : {"section": "main"},
            "Mahsulot qo'shish 🍜": {"section": "add_product"},
        },
        row=2
    ))
    await state.clear()

@router.callback_query(AdminMenuCallback.filter(F.section=="del_product"))
async def del_product(call: CallbackQuery, db: MDB):
    products = await db.products.find({})
    if not products:
        await call.message.edit_text("❌ | Mahsulotlar mavjud emas!\n\n✅ | Iltimos yangi mahsulot qo'shing!", reply_markup=admin_builder({"Mahsulot qo'shish 🍜": {"section": "add_product"},"ortga🔙": {"section":"main"}}))
        return
    
    text_lines = []
    details = {}

    for i, product in enumerate(products):
        text_lines.append(f"{i+1}. <b>{product.title}</b> — 🆔 <code>{product.id}</code>")

        # Har bir mahsulot uchun "❌ O‘chirish" tugmasi
        details[f"❌ {i + 1}"] = {
            "product_id": product.id,
            "action": "delete_product"
        }
    # 🔳 Inline buttonlar admin_builder() orqali

    markup = admin_builder(details=details, row=3)
    kb = admin_builder(
        {
            "ortga🔙": {"section":"main"}
        }
    )
    markup.inline_keyboard += kb.inline_keyboard
    text = "‼️O'chirmoqchi bo'lgan mahsulotingizni tanlang‼️\n\n" + "\n".join(text_lines)
    
    await call.message.edit_text(text=text, reply_markup=markup)

@router.callback_query(AdminMenuCallback.filter(F.action == "delete_product"))
async def delete_product(callback: CallbackQuery, callback_data: AdminMenuCallback, db: MDB):
    product_id = callback_data.product_id
    await db.products.delete_one({"id": product_id})
    await callback.answer(f"Mahsulot {product_id} o‘chirildi ✅")
    await del_product(callback, db)

@router.callback_query(AdminMenuCallback.filter(F.section=="edit_product"))
async def edit_product(call: CallbackQuery, db: MDB):
    products = await db.products.find({})
    if not products:
        await call.message.edit_text("❌ | Mahsulotlar mavjud emas!\n\n✅ | Iltimos yangi mahsulot qo'shing!", reply_markup=admin_builder({"Mahsulot qo'shish 🍜": {"section": "add_product"},"ortga🔙": {"section":"main"}}))
        return
    
    text_lines = []
    details = {}

    for i, product in enumerate(products):
        text_lines.append(f"{i+1}. <b>{product.title}</b> — 🆔 <code>{product.id}</code>")

        # Har bir mahsulot uchun "🛠 Tahrirlash" tugmasi
        details[f"🛠 {i + 1}"] = {
            "product_id": product.id,
            "action": "edit_product"
        }
    # 🔳 Inline buttonlar admin_builder() orqali

    markup = admin_builder(details=details, row=3)
    kb = admin_builder(
        {
            "ortga🔙": {"section":"main"}
        }
    )
    markup.inline_keyboard += kb.inline_keyboard
    text = "‼️Tahrirlashni istagan mahsulotingizni tanlang‼️\n\n" + "\n".join(text_lines)
    
    await call.message.edit_text(text=text, reply_markup=markup)

@router.callback_query(AdminMenuCallback.filter(F.action == "edit_product"))
async def edit_selected_product(callback: CallbackQuery, callback_data: AdminMenuCallback, db: MDB):
    product_id = callback_data.product_id
    product = await db.products.find_one({"id": product_id})
    with suppress(TelegramBadRequest):
        await callback.message.delete()

    if not product.photo:
        markup = admin_builder(
        {
            "Rasm qo'shish 🖼️" : {"section": "product_picture", "product_id": product_id},
            "nomini o'zgartirish ✏️" : {"section": "product_edit", "product_id": product_id, "action": "title"},
            "tavsifini o'zgartirish 🖇" : {"section": "product_edit", "product_id": product_id, "action": "description"},
            "narxini o'zgartirish 💰" : {"section": "product_edit", "product_id": product_id, "action": "price"},
            "ortga🔙" : {"section": "main"},
        },
        row=(2,2,1)
    )
    else:
        markup = admin_builder(
        {
            "Rasm O'zgartirish 🖼️" : {"section": "product_picture", "product_id": product_id},
            "nomini o'zgartirish ✏️" : {"section": "product_edit", "product_id": product_id, "action": "title"},
            "tavsifini o'zgartirish 🖇" : {"section": "product_edit", "product_id": product_id, "action": "description"},
            "narxini o'zgartirish 💰" : {"section": "product_edit", "product_id": product_id, "action": "price"},
            "ortga🔙" : {"section": "main"},
        },
        row=(2,2,1)
    )


    await callback.message.answer(f"✅ | Mahsulot muvaffaqiyatli tanlandi!: {product.title}", reply_markup=markup)

@router.callback_query(AdminMenuCallback.filter(F.section=="product_edit"))
async def edit_product_field(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    field = callback_data.action
    field_map = {
        "title": "nomini",
        "description": "tavsifini",
        "price": "narxini"
    }
    await call.message.edit_text(f"✅ | Mahsulotning yangi {field_map.get(field, 'maydonini')} kiriting!", reply_markup=admin_builder(
        {
            "Bekor qilish❌" : {"section": "main"}
        }
    ))
    await state.set_data(dict(product_id=callback_data.product_id, field=field))
    await state.set_state(ProductEditState.EDIT)

@router.message(ProductEditState.EDIT)
async def product_field_edited(message: Message, db: MDB, state: FSMContext):
    data = await state.get_data()
    product = await db.products.find_one({"id": data['product_id']})
    field = data['field']

    field_map = {
        "title": "nomi",
        "description": "tavsifi",
        "price": "narxi"
    }

    if field == "price":
        if not message.text or not message.text.isdigit():
            await message.answer("❌ | Narx faqat sondan iborat bo'lishi kerak!\nIltimos, qayta kiriting.", reply_markup=admin_builder(
                {
                    "Bekor qilish❌" : {"section": "main"}
                }
            ))
            return
        setattr(product, field, int(message.text))
    else:
        setattr(product, field, message.text)

    await db.products.update_one({"id": product.id}, product.model_dump())

    with suppress(TelegramBadRequest):
        await message.delete()

    await message.answer(f"✅ | Mahsulot {field_map.get(field, 'maydonini')} muvaffaqiyatli o'zgartirildi!", reply_markup=admin_builder(
        {
            "ortga🔙" : {"section": "main"},
        }
    ))
    await state.clear()