from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID, logger
from app.database.db import (
    get_withdraw_requests, update_withdraw_status, add_task, 
    get_active_tasks, get_all_withdraw_requests,
    get_total_users, get_pending_withdraw_count, get_active_tasks_count, get_total_balance,
    get_pending_ad_requests, get_ad_request, update_ad_request_status,
    get_pending_ad_requests_count, get_pending_support_count
)
from app.keyboards.inline import admin_keyboard, admin_ad_action_keyboard

router = Router()

class AddTaskStates(StatesGroup):
    awaiting_channel_link = State()
    awaiting_channel_username = State()
    awaiting_reward = State()
    awaiting_description = State()

class RejectAdStates(StatesGroup):
    awaiting_comment = State()

@router.message(Command("admin"))
async def admin_panel(msg: types.Message):
    try:
        logger.info(f"Admin panel: {msg.from_user.id} - {msg.from_user.full_name}")
        if msg.from_user.id != ADMIN_ID:
            await msg.answer("🚫 Siz admin emassiz.")
            return

        pending_withdrawals = get_pending_withdraw_count()
        pending_ads = get_pending_ad_requests_count()
        pending_support = get_pending_support_count()
        
        await msg.answer(
            f"👑 <b>Admin Panel</b>\n\n"
            f"📊 Statistika:\n"
            f"• 📭 Pul so'rovlari: {pending_withdrawals} ta\n"
            f"• 📢 Reklama so'rovlari: {pending_ads} ta\n"
            f"• 📩 Support xabarlari: {pending_support} ta\n\n"
            "Quyidagi bo'limlardan birini tanlang:",
            reply_markup=admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Admin panel error: {e}")
        await msg.answer("❌ Xatolik yuz berdi")

@router.callback_query(F.data == "admin_withdraw_requests")
async def admin_withdraw_requests(call: types.CallbackQuery):
    try:
        logger.info(f"Admin withdraw requests: {call.from_user.id}")
        if call.from_user.id != ADMIN_ID:
            await call.answer("🚫 Ruxsat yo'q")
            return

        requests = get_withdraw_requests()
        if not requests:
            await call.message.edit_text(
                "📭 Yangi pul yechish so'rovlari mavjud emas.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
                ])
            )
            return

        for r in requests:
            req_id, user_id, card, amount, commission, status, date = r
            await call.message.answer(
                f"💰 <b>So'rov #{req_id}</b>\n\n"
                f"👤 User ID: <code>{user_id}</code>\n"
                f"💳 Karta: <code>{card}</code>\n"
                f"💵 Miqdor: <b>{amount:,} so'm</b>\n"
                f"🧾 Komissiya: <b>{commission:,} so'm</b>\n"
                f"📅 Sana: {date}\n"
                f"📊 Holat: {status}",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="✅ To'landi", callback_data=f"paid_{req_id}"),
                        types.InlineKeyboardButton(text="❌ Rad etildi", callback_data=f"rej_{req_id}")
                    ],
                    [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
                ])
            )
    except Exception as e:
        logger.error(f"Admin withdraw requests error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data.startswith("paid_"))
async def paid(call: types.CallbackQuery):
    try:
        req_id = int(call.data.split("_")[1])
        logger.info(f"Withdraw paid: {call.from_user.id} - req_id: {req_id}")
        if call.from_user.id != ADMIN_ID:
            await call.answer("🚫 Ruxsat yo'q")
            return

        update_withdraw_status(req_id, "✅ To'landi")
        
        await call.message.edit_text(
            call.message.text + "\n\n✅ <b>To'lov tasdiqlandi</b>"
        )
        await call.answer("To'lov tasdiqlandi")
    except Exception as e:
        logger.error(f"Paid error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data.startswith("rej_"))
async def reject(call: types.CallbackQuery):
    try:
        req_id = int(call.data.split("_")[1])
        logger.info(f"Withdraw rejected: {call.from_user.id} - req_id: {req_id}")
        if call.from_user.id != ADMIN_ID:
            await call.answer("🚫 Ruxsat yo'q")
            return

        update_withdraw_status(req_id, "❌ Rad etildi")
        
        await call.message.edit_text(
            call.message.text + "\n\n❌ <b>So'rov rad etildi</b>"
        )
        await call.answer("So'rov rad etildi")
    except Exception as e:
        logger.error(f"Reject error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data == "admin_add_task")
async def add_task_start(call: types.CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Admin add task start: {call.from_user.id}")
        if call.from_user.id != ADMIN_ID:
            await call.answer("🚫 Ruxsat yo'q")
            return

        await state.set_state(AddTaskStates.awaiting_channel_link)
        await call.message.edit_text(
            "📝 <b>Yangi topshiriq qo'shish</b>\n\n"
            "1-qadam: Kanal linkini yuboring\n\n"
            "Masalan: <code>https://t.me/channel_username</code>",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="admin_back")]
            ])
        )
    except Exception as e:
        logger.error(f"Add task start error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.message(AddTaskStates.awaiting_channel_link)
async def process_channel_link(msg: types.Message, state: FSMContext):
    try:
        logger.info(f"Process channel link: {msg.from_user.id}")
        await state.update_data(channel_link=msg.text)
        await state.set_state(AddTaskStates.awaiting_channel_username)
        
        await msg.answer(
            "2-qadam: Kanal username'ini yuboring (@ belgisiz)\n\n"
            "Masalan: <code>channel_username</code>"
        )
    except Exception as e:
        logger.error(f"Process channel link error: {e}")
        await msg.answer("❌ Xatolik yuz berdi. Qaytadan boshlang.")

@router.message(AddTaskStates.awaiting_channel_username)
async def process_channel_username(msg: types.Message, state: FSMContext):
    try:
        logger.info(f"Process channel username: {msg.from_user.id}")
        await state.update_data(channel_username=msg.text)
        await state.set_state(AddTaskStates.awaiting_reward)
        
        await msg.answer(
            "3-qadam: Topshiriq mukofotini yuboring (so'mda)\n\n"
            "Masalan: <code>5000</code>"
        )
    except Exception as e:
        logger.error(f"Process channel username error: {e}")
        await msg.answer("❌ Xatolik yuz berdi. Qaytadan boshlang.")

@router.message(AddTaskStates.awaiting_reward)
async def process_reward(msg: types.Message, state: FSMContext):
    try:
        logger.info(f"Process reward: {msg.from_user.id}")
        reward = int(msg.text)
        if reward <= 0:
            await msg.answer("❌ Mukofot 0 dan katta bo'lishi kerak. Qayta kiriting:")
            return
            
        await state.update_data(reward=reward)
        await state.set_state(AddTaskStates.awaiting_description)
        
        await msg.answer(
            "4-qadam: Topshiriq tavsifini yuboring\n\n"
            "Masalan: <code>Kanalimizga obuna bo'ling va 3 ta post like bosing</code>"
        )
    except ValueError:
        await msg.answer("❌ Noto'g'ri format. Faqat raqam kiriting:")
    except Exception as e:
        logger.error(f"Process reward error: {e}")
        await msg.answer("❌ Xatolik yuz berdi. Qaytadan boshlang.")

@router.message(AddTaskStates.awaiting_description)
async def process_description(msg: types.Message, state: FSMContext):
    try:
        logger.info(f"Process description: {msg.from_user.id}")
        data = await state.get_data()
        
        task_id = add_task(
            data['channel_link'],
            data['channel_username'],
            data['reward'],
            msg.text
        )
        
        await state.clear()
        
        logger.info(f"New task added: {task_id} by {msg.from_user.id}")
        
        await msg.answer(
            f"✅ <b>Topshiriq muvaffaqiyatli qo'shildi!</b>\n\n"
            f"🎯 Topshiriq ID: <b>#{task_id}</b>\n"
            f"📢 Kanal: {data['channel_link']}\n"
            f"💰 Mukofot: <b>{data['reward']:,} so'm</b>\n"
            f"📝 Tavsif: {msg.text}",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="👑 Admin Panel", callback_data="admin_back")]
            ])
        )
    except Exception as e:
        logger.error(f"Process description error: {e}")
        await msg.answer("❌ Xatolik yuz berdi. Qaytadan boshlang.")

@router.callback_query(F.data == "admin_ad_requests")
async def admin_ad_requests(call: types.CallbackQuery):
    try:
        logger.info(f"Admin ad requests: {call.from_user.id}")
        if call.from_user.id != ADMIN_ID:
            await call.answer("🚫 Ruxsat yo'q")
            return

        requests = get_pending_ad_requests()
        if not requests:
            await call.message.edit_text(
                "📭 Yangi reklama so'rovlari mavjud emas.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
                ])
            )
            return

        for r in requests:
            req_id, user_id, channel_name, channel_username, duration, description, price, status, admin_comment, created_date = r
            
            request_text = (
                f"📢 <b>Reklama So'rovi #{req_id}</b>\n\n"
                f"👤 Foydalanuvchi: <code>{user_id}</code>\n"
                f"📢 Kanal: <b>{channel_name}</b>\n"
                f"🔗 Username: @{channel_username}\n"
                f"⏳ Muddat: <b>{duration}</b>\n"
                f"💰 Narx: <b>{price:,} so'm</b>\n"
                f"📝 Tavsif: {description}\n"
                f"📅 Sana: {created_date}\n\n"
                f"Holat: {status}"
            )
            
            await call.message.answer(
                request_text,
                reply_markup=admin_ad_action_keyboard(req_id)
            )
    except Exception as e:
        logger.error(f"Admin ad requests error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data.startswith("ad_approve_"))
async def approve_ad_request(call: types.CallbackQuery, bot: Bot):
    try:
        request_id = int(call.data.split("_")[2])
        logger.info(f"Approve ad request: {call.from_user.id} - req_id: {request_id}")
        if call.from_user.id != ADMIN_ID:
            await call.answer("🚫 Ruxsat yo'q")
            return

        ad_request = get_ad_request(request_id)
        if not ad_request:
            await call.answer("❌ So'rov topilmadi")
            return

        req_id, user_id, channel_name, channel_username, duration, description, price, status, admin_comment, created_date = ad_request
        
        # Topshiriq sifatida qo'shish
        channel_link = f"https://t.me/{channel_username}"
        reward = 1000  # Standart mukofot
        
        task_id = add_task(channel_link, channel_username, reward, description)
        
        # So'rov holatini yangilash
        update_ad_request_status(request_id, "✅ Ma'qullandi")
        
        # Foydalanuvchiga xabar yuborish
        try:
            await bot.send_message(
                user_id,
                f"🎉 Tabriklaymiz! Sizning reklama so'rovingiz ma'qullandi!\n\n"
                f"📢 Kanal: {channel_name}\n"
                f"🔗 Username: @{channel_username}\n"
                f"⏳ Muddat: {duration}\n"
                f"💰 Sarflangan: {price:,} so'm\n\n"
                f"✅ Reklama endi topshiriqlar ro'yxatida ko'rinadi!\n"
                f"🎯 Har bir obuna uchun {reward:,} so'm mukofot beriladi."
            )
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")
        
        await call.message.edit_text(
            call.message.text + f"\n\n✅ <b>Reklama ma'qullandi!</b>\n🎯 Topshiriq ID: #{task_id}"
        )
        await call.answer("Reklama ma'qullandi")
    except Exception as e:
        logger.error(f"Approve ad request error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data.startswith("ad_reject_"))
async def reject_ad_request(call: types.CallbackQuery, state: FSMContext):
    try:
        request_id = int(call.data.split("_")[2])
        logger.info(f"Reject ad request: {call.from_user.id} - req_id: {request_id}")
        if call.from_user.id != ADMIN_ID:
            await call.answer("🚫 Ruxsat yo'q")
            return

        await state.set_state(RejectAdStates.awaiting_comment)
        await state.update_data(request_id=request_id)
        
        await call.message.edit_text(
            "📝 Reklama so'rovini rad etish uchun sababni yuboring:\n\n"
            "Masalan: <code>Kanal username noto'g'ri</code> yoki <code>Tavsif yetarli emas</code>"
        )
    except Exception as e:
        logger.error(f"Reject ad request error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.message(RejectAdStates.awaiting_comment)
async def process_reject_comment(msg: types.Message, state: FSMContext, bot: Bot):
    try:
        logger.info(f"Process reject comment: {msg.from_user.id}")
        data = await state.get_data()
        request_id = data['request_id']
        admin_comment = msg.text
        
        ad_request = get_ad_request(request_id)
        if not ad_request:
            await msg.answer("❌ So'rov topilmadi")
            await state.clear()
            return

        req_id, user_id, channel_name, channel_username, duration, description, price, status, old_comment, created_date = ad_request
        
        # So'rov holatini yangilash
        update_ad_request_status(request_id, "❌ Rad etildi", admin_comment)
        
        # Foydalanuvchiga xabar yuborish
        try:
            await bot.send_message(
                user_id,
                f"❌ Afsuski, sizning reklama so'rovingiz rad etildi.\n\n"
                f"📢 Kanal: {channel_name}\n"
                f"🔗 Username: @{channel_username}\n"
                f"💰 Sarflangan: {price:,} so'm\n\n"
                f"📝 <b>Admin izohi:</b>\n{admin_comment}\n\n"
                f"ℹ️ Pul qaytarilmaydi. Yangi so'rov yuborishingiz mumkin."
            )
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")
        
        await state.clear()
        await msg.answer(
            f"✅ <b>Reklama so'rovi rad etildi!</b>\n\n"
            f"📋 So'rov raqami: #{request_id}\n"
            f"👤 Foydalanuvchi: {user_id}\n"
            f"📝 Sabab: {admin_comment}",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="👑 Admin Panel", callback_data="admin_back")]
            ])
        )
    except Exception as e:
        logger.error(f"Process reject comment error: {e}")
        await msg.answer("❌ Xatolik yuz berdi")

@router.callback_query(F.data == "admin_stats")
async def admin_stats(call: types.CallbackQuery):
    try:
        logger.info(f"Admin stats: {call.from_user.id}")
        if call.from_user.id != ADMIN_ID:
            await call.answer("🚫 Ruxsat yo'q")
            return

        total_users = get_total_users()
        pending_requests = get_pending_withdraw_count()
        active_tasks = get_active_tasks_count()
        total_balance = get_total_balance()
        pending_ads = get_pending_ad_requests_count()
        pending_support = get_pending_support_count()
        
        await call.message.edit_text(
            f"📊 <b>Bot Statistikasi</b>\n\n"
            f"👥 Jami foydalanuvchilar: <b>{total_users}</b>\n"
            f"💰 Jami balans: <b>{total_balance:,} so'm</b>\n"
            f"📭 Kutilayotgan pul so'rovlari: <b>{pending_requests}</b>\n"
            f"📢 Kutilayotgan reklama so'rovlari: <b>{pending_ads}</b>\n"
            f"📩 Kutilayotgan support xabarlari: <b>{pending_support}</b>\n"
            f"🎯 Faol topshiriqlar: <b>{active_tasks}</b>\n\n"
            f"🔄 Yangilangan: {call.message.date.strftime('%Y-%m-%d %H:%M')}",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
            ])
        )
    except Exception as e:
        logger.error(f"Admin stats error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data == "admin_back")
async def admin_back(call: types.CallbackQuery):
    try:
        logger.info(f"Admin back: {call.from_user.id}")
        await call.message.edit_text(
            "👑 <b>Admin Panel</b>\n\n"
            "Quyidagi bo'limlardan birini tanlang:",
            reply_markup=admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Admin back error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)