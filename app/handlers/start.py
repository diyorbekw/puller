from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import logger, BOT_USERNAME, REFERRAL_BONUS
from app.database.db import (
    add_user, get_user, get_active_tasks, get_user_pending_tasks, 
    get_user_completed_tasks, get_task, complete_user_task, 
    update_balance, check_user_task_completion, add_referral, 
    check_referral_exists, get_user_referrals, get_total_referral_earnings,
    mark_referral_reward_given, get_referrer_id, add_user_task,
    get_user_task_status
)
from app.keyboards.inline import main_menu, tasks_keyboard, task_detail_keyboard, back_to_menu_keyboard, referral_keyboard, contact_admin_keyboard

router = Router()

class TaskStates(StatesGroup):
    viewing_task = State()

@router.message(Command("start"))
async def start_cmd(msg: types.Message, command: CommandObject, bot: Bot):
    try:
        logger.info(f"Start command: {msg.from_user.id} - {msg.from_user.full_name}")
        
        # Referal parametrini tekshirish
        referrer_id = None
        if command.args and command.args.startswith("ref"):
            try:
                referrer_id = int(command.args[3:])
                # O'zini referal qilishni oldini olish
                if referrer_id != msg.from_user.id:
                    # Yangi referal qo'shish
                    if not check_referral_exists(msg.from_user.id):
                        add_referral(referrer_id, msg.from_user.id)
                        logger.info(f"New referral: {referrer_id} -> {msg.from_user.id}")
                        
                        # Referal bonusini berish
                        update_balance(referrer_id, REFERRAL_BONUS)
                        mark_referral_reward_given(msg.from_user.id)
                        
                        # Referalga xabar yuborish
                        try:
                            await bot.send_message(
                                referrer_id,
                                f"🎉 Tabriklaymiz! Sizning referal linkingiz orqali yangi foydalanuvchi qo'shildi!\n"
                                f"💰 Sizning balansingizga {REFERRAL_BONUS} so'm qo'shildi."
                            )
                        except:
                            pass
            except ValueError:
                pass
        
        add_user(msg.from_user.id, msg.from_user.username or "no_username", referrer_id)
        user = get_user(msg.from_user.id)
        
        welcome_text = (
            f"👋 Salom, <b>{msg.from_user.full_name}</b>!\n\n"
            f"💰 Balansingiz: <b>{user[2]:,}</b> so'm\n"
            f"📊 Sizning profilingiz:\n"
            f"• ID: <code>{user[0]}</code>\n"
            f"• Ism: {msg.from_user.full_name}\n"
            f"• Qo'shilgan sana: {user[3][:10]}\n\n"
        )
        
        # Agar referal orqali kelgan bo'lsa
        if referrer_id and referrer_id != msg.from_user.id:
            welcome_text += "🎁 Siz referal orqali qo'shildingiz! 50 so'm bonus oldingiz.\n\n"
        
        welcome_text += (
            "🎯 <b>Topshiriqlarni bajarib pul ishlang!</b>\n"
            "👥 <b>Do'stlaringizni taklif qiling va bonus oling!</b>\n"
            "📢 <b>Kanalingizni reklama qiling va obunchilarni oshiring!</b>\n"
            "💸 Yig'ilgan mablag'ingizni kartangizga yechib oling!"
        )
        
        await msg.answer(welcome_text, reply_markup=main_menu())
        
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
                "✅ Siz barcha topshiriqlarni bajarib bo'ldingiz!\n\n"
                "🔄 Yangi topshiriqlar paydo bo'lganda sizga xabar beramiz.",
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
        
        # Agar topshiriq allaqachon bajarilgan bo'lsa
        if check_user_task_completion(call.from_user.id, task_id):
            await call.answer("❌ Siz bu topshiriqni allaqachon bajargansiz", show_alert=True)
            await show_tasks(call)
            return
        
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
async def check_subscription(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    try:
        user_id = call.from_user.id
        task_id = int(call.data.split("_")[2])
        logger.info(f"Check subscription: {user_id} - task_{task_id}")
        
        # Avval topshiriq bajarilganligini tekshiramiz
        if check_user_task_completion(user_id, task_id):
            await call.answer("❌ Siz bu topshiriqni allaqachon bajargansiz", show_alert=True)
            await show_tasks(call)
            return
        
        task = get_task(task_id)
        if not task:
            await call.answer("❌ Topshiriq topilmadi", show_alert=True)
            return
            
        channel_username = task[2]
        reward = task[3]
        
        # Kanalga obuna bo'lganligini tekshirish
        try:
            if channel_username and channel_username.strip():
                clean_username = channel_username.replace('@', '').strip()
                chat_member = await bot.get_chat_member(f"@{clean_username}", user_id)
                is_subscribed = chat_member.status in ['member', 'administrator', 'creator']
            else:
                is_subscribed = True
        except Exception as e:
            logger.error(f"Subscription check error: {e}")
            is_subscribed = False
        
        if not is_subscribed:
            await call.answer("❌ Siz hali kanalga obuna bo'lmagansiz! Iltimos, avval obuna bo'ling va keyin tekshiring.", show_alert=True)
            return
        
        # Foydalanuvchi topshiriqni bajarganligini belgilash
        # 1. Avval user_tasks jadvaliga qo'shamiz (agar yo'q bo'lsa)
        add_user_task(user_id, task_id)
        
        # 2. Keyin complete qilamiz
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

@router.callback_query(F.data == "referral")
async def show_referral(call: types.CallbackQuery):
    try:
        logger.info(f"Referral menu: {call.from_user.id}")
        user_id = call.from_user.id
        referrals_count = get_user_referrals(user_id)
        referral_earnings = get_total_referral_earnings(user_id)
        
        referral_text = (
            f"👥 <b>Referal Tizimi</b>\n\n"
            f"📊 Sizning statistikangiz:\n"
            f"• Jami referallar: <b>{referrals_count} ta</b>\n"
            f"• Referallardan daromad: <b>{referral_earnings} so'm</b>\n\n"
            f"🎁 <b>Qanday ishlaydi?</b>\n"
            f"• Har bir do'stingizni taklif qiling - <b>50 so'm</b> oling\n"
            f"• Do'stingiz ham <b>50 so'm</b> bonus oladi\n"
            f"• Cheksiz do'st taklif qilishingiz mumkin!\n\n"
            f"📤 Quyidagi tugma orqali referal linkingizni ulashing:"
        )
        
        await call.message.edit_text(
            referral_text,
            reply_markup=referral_keyboard(user_id)
        )
    except Exception as e:
        logger.error(f"Referral error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data == "contact_admin")
async def contact_admin_info(call: types.CallbackQuery):
    try:
        logger.info(f"Contact admin info: {call.from_user.id}")
        await call.message.edit_text(
            "📞 <b>Admin bilan bog'lanish</b>\n\n"
            "ℹ️ Savol, taklif yoki shikoyatingiz bo'lsa, quyidagi tugma orqali xabar yuboring.\n\n"
            "📝 <b>Xabar yuborish uchun:</b>\n"
            "1. «Xabar yuborish» tugmasini bosing\n"
            "2. Xabaringizni yozing\n"
            "3. Xabar adminga yuboriladi\n"
            "4. Admin javobini kutishingiz kerak\n\n"
            "⏳ <b>Javob qancha kutiladi?</b>\n"
            "• Odatda 1-24 soat ichida\n"
            "• Ish vaqtlari: 09:00 - 18:00",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="📩 Xabar yuborish", callback_data="send_support_message")],
                [types.InlineKeyboardButton(text="📋 Mening xabarlarim", callback_data="my_support_messages")],
                [types.InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu")]
            ])
        )
    except Exception as e:
        logger.error(f"Contact admin info error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data == "stats")
async def show_stats(call: types.CallbackQuery):
    try:
        logger.info(f"Stats: {call.from_user.id}")
        user = get_user(call.from_user.id)
        completed_tasks = get_user_completed_tasks(call.from_user.id)
        pending_tasks = get_user_pending_tasks(call.from_user.id)
        referrals_count = get_user_referrals(call.from_user.id)
        referral_earnings = get_total_referral_earnings(call.from_user.id)
        
        stats_text = (
            f"📊 <b>Sizning Statistikangiz</b>\n\n"
            f"👤 Ism: <b>{call.from_user.full_name}</b>\n"
            f"🆔 ID: <code>{call.from_user.id}</code>\n"
            f"💰 Balans: <b>{user[2]:,} so'm</b>\n"
            f"✅ Bajarilgan topshiriqlar: <b>{len(completed_tasks)} ta</b>\n"
            f"📭 Qolgan topshiriqlar: <b>{len(pending_tasks)} ta</b>\n"
            f"👥 Taklif qilgan do'stlar: <b>{referrals_count} ta</b>\n"
            f"🎁 Referal daromadi: <b>{referral_earnings} so'm</b>\n"
            f"📅 Qo'shilgan sana: <b>{user[3][:10]}</b>"
        )
        
        await call.message.edit_text(
            stats_text,
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
            "❓ <b>Referal tizimi qanday ishlaydi?</b>\n"
            "→ Do'stlaringizni taklif qiling, ular ro'yxatdan o'tganda siz va ular 50 so'm bonus olasiz.\n\n"
            "❓ <b>Reklama qanday qo'shiladi?</b>\n"
            "→ «Reklama» bo'limiga o'ting va kanalingizni reklama qilish uchun so'rov yuboring.\n\n"
            "❓ <b>Admin bilan qanday bog'lansam bo'ladi?</b>\n"
            "→ «Admin bilan bog'lanish» bo'limiga o'ting va xabaringizni yuboring.\n\n"
            "❓ <b>To'lov qancha vaqtda tushadi?</b>\n"
            "→ To'lovlar admin tomonidan 1-24 soat ichida amalga oshiriladi.\n\n"
            "📞 <b>Qo'shimcha savollar bo'lsa:</b> Admin bilan bog'lanishingiz mumkin.",
            reply_markup=back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Help error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)