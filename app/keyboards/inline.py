from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_USERNAME, AD_PRICES

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Topshiriqlar", callback_data="tasks")],
        [InlineKeyboardButton(text="💰 Mening balansim", callback_data="my_balance")],
        [InlineKeyboardButton(text="👥 Referal", callback_data="referral")],
        [InlineKeyboardButton(text="📢 Reklama", callback_data="ads_menu")],
        [InlineKeyboardButton(text="💸 Pul yechish", callback_data="withdraw")],
        [InlineKeyboardButton(text="📞 Admin bilan bog'lanish", callback_data="contact_admin")],
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
        [InlineKeyboardButton(text="📢 Reklama so'rovlari", callback_data="admin_ad_requests")],
        [InlineKeyboardButton(text="📩 Support xabarlari", callback_data="admin_support_messages")],
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

# Reklama uchun yangi keyboardlar
def ads_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Reklama qo'shish", callback_data="add_ad")],
        [InlineKeyboardButton(text="📋 Mening reklamalarim", callback_data="my_ads")],
        [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu")]
    ])

def ad_duration_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 hafta - 2,000 so'm", callback_data="ad_duration_1_week")],
        [InlineKeyboardButton(text="2 hafta - 3,500 so'm", callback_data="ad_duration_2_weeks")],
        [InlineKeyboardButton(text="1 oy - 6,000 so'm", callback_data="ad_duration_1_month")],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="ads_menu")]
    ])

def bot_check_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, qo'shdim", callback_data="bot_added_yes")],
        [InlineKeyboardButton(text="❌ Yo'q", callback_data="bot_added_no")],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="ads_menu")]
    ])

def confirm_ad_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_ad")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="ads_menu")]
    ])

def admin_ad_action_keyboard(request_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ma'qullash", callback_data=f"ad_approve_{request_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"ad_reject_{request_id}")
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_ad_requests")]
    ])

# Support uchun yangi keyboardlar
def contact_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Admin bilan bog'lanish", callback_data="contact_admin")],
        [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu")]
    ])

def low_balance_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Balans to'ldirish", callback_data="contact_admin")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="ads_menu")]
    ])

def admin_support_action_keyboard(message_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Javob berish", callback_data=f"reply_support_{message_id}")],
        [InlineKeyboardButton(text="✅ Yopish", callback_data=f"close_support_{message_id}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_support_messages")]
    ])

def cancel_support_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_support")]
    ])