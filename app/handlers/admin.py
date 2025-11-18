from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID, logger
from app.database.db import (
    get_withdraw_requests, update_withdraw_status, add_task, 
    get_active_tasks, get_all_withdraw_requests,
    get_total_users, get_pending_withdraw_count, get_active_tasks_count, get_total_balance
)
from app.keyboards.inline import admin_keyboard

router = Router()

class AddTaskStates(StatesGroup):
    awaiting_channel_link = State()
    awaiting_channel_username = State()
    awaiting_reward = State()
    awaiting_description = State()

@router.message(Command("admin"))
async def admin_panel(msg: types.Message):
    try:
        logger.info(f"Admin panel: {msg.from_user.id} - {msg.from_user.full_name}")
        if msg.from_user.id != ADMIN_ID:
            await msg.answer("🚫 Siz admin emassiz.")
            return

        await msg.answer(
            "👑 <b>Admin Panel</b>\n\n"
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
        
        await call.message.edit_text(
            f"📊 <b>Bot Statistikasi</b>\n\n"
            f"👥 Jami foydalanuvchilar: <b>{total_users}</b>\n"
            f"💰 Jami balans: <b>{total_balance:,} so'm</b>\n"
            f"📭 Kutilayotgan so'rovlar: <b>{pending_requests}</b>\n"
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