from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_USERNAME

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Topshiriqlar", callback_data="tasks")],
        [InlineKeyboardButton(text="💰 Mening balansim", callback_data="my_balance")],
        [InlineKeyboardButton(text="👥 Referal", callback_data="referral")],
        [InlineKeyboardButton(text="💸 Pul yechish", callback_data="withdraw")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton(text="ℹ️ Yordam", callback_data="help")]
    ])

def back_to_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu")]
    ])

def tasks_keyboard(tasks):
    keyboard = []
    for task in tasks:
        task_id, channel_link, channel_username, reward, description, created_date, is_active = task
        keyboard.append([
            InlineKeyboardButton(
                text=f"🎯 {reward:,} so'm - {description[:20]}...", 
                callback_data=f"task_{task_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def task_detail_keyboard(task_id, channel_username):
    keyboard = []
    if channel_username:
        # @ belgisini olib tashlash
        clean_username = channel_username.replace('@', '')
        keyboard.append([
            InlineKeyboardButton(
                text="📢 Kanalga o'tish", 
                url=f"https://t.me/{clean_username}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton(text="✅ Tekshirish", callback_data=f"check_sub_{task_id}")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="tasks")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def confirm_withdraw_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_withdraw"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_withdraw")
        ]
    ])

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Pul yechish so'rovlari", callback_data="admin_withdraw_requests")],
        [InlineKeyboardButton(text="🎯 Topshiriq qo'shish", callback_data="admin_add_task")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu")]
    ])

def referral_keyboard(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📤 Referal linkni ulashish",
                url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}?start=ref{user_id}"
            )
        ],
        [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu")]
    ])