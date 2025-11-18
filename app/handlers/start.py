from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import logger
from app.database.db import (
    add_user, get_user, get_active_tasks, get_user_pending_tasks, 
    get_user_completed_tasks, get_task, complete_user_task, 
    update_balance, check_user_task_completion
)
from app.keyboards.inline import main_menu, tasks_keyboard, task_detail_keyboard, back_to_menu_keyboard

router = Router()

class TaskStates(StatesGroup):
    viewing_task = State()

@router.message(Command("start"))
async def start_cmd(msg: types.Message):
    try:
        logger.info(f"Start command: {msg.from_user.id} - {msg.from_user.full_name}")
        add_user(msg.from_user.id, msg.from_user.username or "no_username")
        user = get_user(msg.from_user.id)
        
        await msg.answer(
            f"👋 Salom, <b>{msg.from_user.full_name}</b>!\n\n"
            f"💰 Balansingiz: <b>{user[2]:,}</b> so'm\n"
            f"📊 Sizning profilingiz:\n"
            f"• ID: <code>{user[0]}</code>\n"
            f"• Ism: {msg.from_user.full_name}\n"
            f"• Qo'shilgan sana: {user[3][:10]}\n\n"
            "🎯 <b>Topshiriqlarni bajarib pul ishlang!</b>\n"
            "💸 Yig'ilgan mablag'ingizni kartangizga yechib oling!",
            reply_markup=main_menu()
        )
    except Exception as e:
        logger.error(f"Start command error: {e}")
        await msg.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

@router.callback_query(F.data == "main_menu")
async def main_menu_handler(call: types.CallbackQuery):
    try:
        logger.info(f"Main menu: {call.from_user.id} - {call.from_user.full_name}")
        user = get_user(call.from_user.id)
        await call.message.edit_text(
            f"👋 Salom, <b>{call.from_user.full_name}</b>!\n\n"
            f"💰 Balansingiz: <b>{user[2]:,}</b> so'm\n\n"
            "🎯 Quyidagi menyudan kerakli bo'limni tanlang:",
            reply_markup=main_menu()
        )
    except Exception as e:
        logger.error(f"Main menu error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data == "tasks")
async def show_tasks(call: types.CallbackQuery):
    try:
        logger.info(f"Tasks menu: {call.from_user.id} - {call.from_user.full_name}")
        user_id = call.from_user.id
        pending_tasks = get_user_pending_tasks(user_id)
        completed_tasks = get_user_completed_tasks(user_id)
        
        if not pending_tasks:
            await call.message.edit_text(
                "📭 Hozircha yangi topshiriqlar mavjud emas.\n\n"
                "🔄 Keyinroq tekshirib ko'ring yoki admin yangi topshiriqlar qo'shguncha kuting.",
                reply_markup=back_to_menu_keyboard()
            )
            return
        
        await call.message.edit_text(
            f"🎯 <b>Mavjud Topshiriqlar</b>\n\n"
            f"📋 Yangi topshiriqlar: <b>{len(pending_tasks)} ta</b>\n"
            f"✅ Bajarilgan: <b>{len(completed_tasks)} ta</b>\n\n"
            "Quyidagi topshiriqlardan birini tanlang:",
            reply_markup=tasks_keyboard(pending_tasks)
        )
    except Exception as e:
        logger.error(f"Tasks error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data.startswith("task_"))
async def show_task_detail(call: types.CallbackQuery, state: FSMContext):
    try:
        task_id = int(call.data.split("_")[1])
        logger.info(f"Task detail: {call.from_user.id} - task_{task_id}")
        task = get_task(task_id)
        
        if not task:
            await call.answer("❌ Topshiriq topilmadi")
            return
        
        task_id, channel_link, channel_username, reward, description, created_date, is_active = task
        
        await state.set_state(TaskStates.viewing_task)
        await state.update_data(current_task_id=task_id)
        
        await call.message.edit_text(
            f"🎯 <b>Topshiriq #{task_id}</b>\n\n"
            f"📝 <b>Talab:</b>\n{description}\n\n"
            f"📢 <b>Kanal:</b> {channel_link}\n"
            f"💰 <b>Mukofot:</b> {reward:,} so'm\n\n"
            f"📋 <b>Qanday bajariladi?</b>\n"
            f"1. Yuqoridagi kanalga obuna bo'ling\n"
            f"2. «Tekshirish» tugmasini bosing\n"
            f"3. Agar bajargan bo'lsangiz, mukofot balansingizga qo'shiladi",
            reply_markup=task_detail_keyboard(task_id, channel_username)
        )
    except Exception as e:
        logger.error(f"Task detail error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data.startswith("check_sub_"))
async def check_subscription(call: types.CallbackQuery, state: FSMContext):
    try:
        user_id = call.from_user.id
        task_id = int(call.data.split("_")[2])
        logger.info(f"Check subscription: {user_id} - task_{task_id}")
        
        if check_user_task_completion(user_id, task_id):
            await call.answer("❌ Siz bu topshiriqni allaqachon bajargansiz", show_alert=True)
            return
        
        task = get_task(task_id)
        if not task:
            await call.answer("❌ Topshiriq topilmadi", show_alert=True)
            return
            
        channel_username = task[2]
        reward = task[3]
        
        # Foydalanuvchi topshiriqni bajarganligini belgilash
        complete_user_task(user_id, task_id)
        update_balance(user_id, reward)
        
        logger.info(f"Task completed: {user_id} - task_{task_id} - reward: {reward}")
        
        await call.message.edit_text(
            f"✅ <b>Tabriklaymiz!</b>\n\n"
            f"🎯 Topshiriq muvaffaqiyatli bajarildi!\n"
            f"💰 Sizning balansingizga <b>{reward:,} so'm</b> qo'shildi\n\n"
            f"💳 Joriy balans: <b>{get_user(user_id)[2]:,} so'm</b>",
            reply_markup=back_to_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Check subscription error: {e}")
        await call.answer(f"❌ Xatolik yuz berdi: {str(e)}", show_alert=True)

@router.callback_query(F.data == "my_balance")
async def show_balance(call: types.CallbackQuery):
    try:
        logger.info(f"Balance check: {call.from_user.id}")
        user = get_user(call.from_user.id)
        completed_tasks = get_user_completed_tasks(call.from_user.id)
        
        await call.message.edit_text(
            f"💰 <b>Mening Balansim</b>\n\n"
            f"💳 Joriy balans: <b>{user[2]:,} so'm</b>\n"
            f"✅ Bajarilgan topshiriqlar: <b>{len(completed_tasks)} ta</b>\n\n"
            f"💸 Agar balansingiz 10,000 so'mdan ko'p bo'lsa, pul yechish imkoniyati mavjud.",
            reply_markup=back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Balance error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data == "stats")
async def show_stats(call: types.CallbackQuery):
    try:
        logger.info(f"Stats: {call.from_user.id}")
        user = get_user(call.from_user.id)
        completed_tasks = get_user_completed_tasks(call.from_user.id)
        pending_tasks = get_user_pending_tasks(call.from_user.id)
        
        await call.message.edit_text(
            f"📊 <b>Sizning Statistikangiz</b>\n\n"
            f"👤 Ism: <b>{call.from_user.full_name}</b>\n"
            f"🆔 ID: <code>{call.from_user.id}</code>\n"
            f"💰 Balans: <b>{user[2]:,} so'm</b>\n"
            f"✅ Bajarilgan topshiriqlar: <b>{len(completed_tasks)} ta</b>\n"
            f"📭 Qolgan topshiriqlar: <b>{len(pending_tasks)} ta</b>\n"
            f"📅 Qo'shilgan sana: <b>{user[3][:10]}</b>",
            reply_markup=back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data == "help")
async def show_help(call: types.CallbackQuery):
    try:
        logger.info(f"Help: {call.from_user.id}")
        await call.message.edit_text(
            "ℹ️ <b>Yordam va Ko'p So'raladigan Savollar</b>\n\n"
            "❓ <b>Qanday pul ishlay olaman?</b>\n"
            "→ «Topshiriqlar» bo'limiga o'ting va mavjud topshiriqlarni bajarishni boshlang.\n\n"
            "❓ <b>Pulni qanday yechib olaman?</b>\n"
            "→ Balansingiz 10,000 so'mdan ko'p bo'lsa, «Pul yechish» bo'limi orqali kartangizga pul o'tkazishingiz mumkin.\n\n"
            "❓ <b>Topshiriqni bajarganimni qanday tekshiraman?</b>\n"
            "→ Topshiriq sahifasida «Tekshirish» tugmasi bor. Obuna bo'lganingizdan so'ng shu tugmani bosing.\n\n"
            "❓ <b>To'lov qancha vaqtda tushadi?</b>\n"
            "→ To'lovlar admin tomonidan 1-24 soat ichida amalga oshiriladi.\n\n"
            "📞 <b>Qo'shimcha savollar bo'lsa:</b> @admin",
            reply_markup=back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Help error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)