import asyncio

from typing import List, Any, Callable

from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramRetryAfter

from src.utils.keyboards import admin_builder

from data.data import SETTINGS_SCHEMA

async def build_cart_text( user, db,total: bool=False, max_len: int = 1024,) -> str:
    """
    🛒 Foydalanuvchining savatini qisqa va formatlangan holda qaytaradi.
    Telegram caption limiti (1024) dan oshmaydi.
    """

    user_from_db = await db.users.find_one({"id": user.id})
    savat = user_from_db.savat if user_from_db and user_from_db.savat else []

    if not savat:
        return None

    text_lines = ["🛒 Sizning savatingiz:\n"]
    total_sum = 0

    for item in savat:
        product_id = item.get("product_id") if isinstance(item, dict) else item.product_id
        count = item.get("count") if isinstance(item, dict) else item.count

        product = await db.products.find_one({"id": product_id})
        if not product:
            continue

        title = product.title
        price = product.price
        subtotal = price * count
        total_sum += subtotal

        # Qisqa format: nom + jami
        line = f"• {title[:20]} — {count} dona × {price:,} = {subtotal:,} so'm\n"
        text_lines.append(line)

        # Agar uzun bo‘lib ketsa, to‘xtatamiz
        if len(text_lines) > max_len:
            text_lines.append("... va boshqalar.")
            break

    text_lines.append(f"\n💵 Umumiy: {total_sum:,} so'm")
    print("\n".join(text_lines))
    if total:
        return total_sum
    return "\n".join(text_lines)

def build_settings_keyboard(settings: dict):
    details = {}

    for key, info in SETTINGS_SCHEMA.items():

        current = settings.get(key, info["default"])
        label = info["label"]

        # BOOLEAN SETTING
        if info["type"] == "bool":
            emoji = "✅" if current else "❌"
            new_value = not current

            details[f"{label}: {emoji}"] = {
                "section": "push_settings",
                "setting": key,
                "value": new_value
            }

        # CHOICE SETTING (HTML / Markdown / None ...)
        elif info["type"] == "choice":
            next_index = (info["choices"].index(current) + 1) % len(info["choices"])
            new_value = info["choices"][next_index]

            details[f"{label}: {current}"] = {  
                "section": "push_settings",
                "setting": key,
                "value": new_value
            }

    return admin_builder(details=details, row=2)



# --- User chunking (10k+ users) ---
def chunk_users(user_ids: List[int], chunk_size: int = 50) -> Any:
    """
    Large listni bo'laklarga bo'lib beradi.
    Spamdan saqlash uchun 20-100 oralig'i tavsiya etiladi.
    """
    for i in range(0, len(user_ids), chunk_size):
        yield user_ids[i:i + chunk_size]


# --- Message sender with error handling ---
async def safe_send(bot: Bot, user_id: int, send_func: Callable, *args, retries: int = 3, **kwargs) -> bool:
    for _ in range(retries):
        try:
            await send_func(user_id, *args, **kwargs)
            return True
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.timeout)
        except Exception as e:
            print(e)
            await asyncio.sleep(1)
    return False
# --- Mass broadcast ---
async def mass_broadcast(
    bot: Bot,
    user_ids: List[int],
    send_func: Callable,
    *args,
    delay: float = 0.05,
    chunk_size: int = 50,
    split: int = 10,
    progress_callback=None,
    **kwargs
) -> dict:
    """
    progress_callback(success_count, failed_count, checked_count) -> awaitable
    """

    success = 0
    failed = 0
    checked = 0

    for group in chunk_users(user_ids, chunk_size):
        tasks = [safe_send(bot, uid, send_func, *args, **kwargs) for uid in group]
        results = await asyncio.gather(*tasks)

        for r in results:
            checked += 1
            if r:
                success += 1
            else:
                failed += 1

        # Progress yangilash
        if progress_callback and checked%split==0:
            await progress_callback(success, failed, checked)

        await asyncio.sleep(delay)

    return {
        "sent": success,
        "failed": failed,
        "total": len(user_ids)
    }

async def create_progress_callback(message: Message):

    async def update(success: int, failed: int, checked: int):
        try:
            await message.edit_text(
                f"📤 *Yuborish jarayoni...*\n\n"
                f"✅ | Yuborildi: `{success}`\n"
                f"❌ | Yuborilmadi: `{failed}`\n"
                f"👁 | Tekshirilgan: `{checked}`\n",
                parse_mode="Markdown"
            )
        except:
            pass

    return update

# --- Admin notification logs ---
def format_broadcast_report(result: dict) -> str:
    return (
        f"📊 Broadcast Yakuni:\n"
        f"✅ | Yuborilgan: {result['sent']}\n"
        f"❌ | Yuborilmagan: {result['failed']}\n"
        f"👥 | Jami: {result['total']}"
    )
