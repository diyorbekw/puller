from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import logger, ADMIN_ID
from app.database.db import (
    add_support_message, get_user_support_messages,
    get_user, update_support_message_status, get_support_message
)
from app.keyboards.inline import (
    contact_admin_keyboard, cancel_support_keyboard,
    back_to_menu_keyboard, admin_support_action_keyboard
)

router = Router()

class SupportStates(StatesGroup):
    awaiting_message = State()
    awaiting_reply = State()

@router.callback_query(F.data == "send_support_message")
async def start_support_message(call: types.CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Start support message: {call.from_user.id}")
        await state.set_state(SupportStates.awaiting_message)
        await call.message.edit_text(
            "📝 <b>Xabar yuborish</b>\n\n"
            "Iltimos, adminga yubormoqchi bo'lgan xabaringizni yozing:\n\n"
            "💡 <b>Masalan:</b>\n"
            "• Balans to'ldirish haqida\n"
            "• Texnik muammo haqida\n"
            "• Taklif yoki shikoyat\n"
            "• Boshqa savollar",
            reply_markup=cancel_support_keyboard()
        )
    except Exception as e:
        logger.error(f"Start support message error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.message(SupportStates.awaiting_message)
async def process_support_message(msg: types.Message, state: FSMContext, bot: Bot):
    try:
        logger.info(f"Process support message: {msg.from_user.id}")
        user = get_user(msg.from_user.id)
        
        # Support xabarini qo'shish
        message_id = add_support_message(msg.from_user.id, msg.text)
        
        # Adminga xabar yuborish
        admin_text = (
            f"📩 <b>Yangi Support Xabari</b>\n\n"
            f"🆔 ID: <code>{msg.from_user.id}</code>\n"
            f"👤 Foydalanuvchi: {msg.from_user.full_name}\n"
            f"📅 Vaqt: {msg.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"📋 Xabar ID: #{message_id}\n\n"
            f"💬 Xabar:\n{msg.text}\n\n"
            f"💰 Balans: {user[2]:,} so'm"
        )
        
        try:
            await bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_support_action_keyboard(message_id))
        except Exception as e:
            logger.error(f"Failed to send message to admin: {e}")
        
        await state.clear()
        
        await msg.answer(
            f"✅ <b>Xabaringiz muvaffaqiyatli yuborildi!</b>\n\n"
            f"📋 Xabar raqami: <b>#{message_id}</b>\n"
            f"⏳ Admin javobini kuting.\n"
            f"📞 Javob 1-24 soat ichida keladi.\n\n"
            f"🔄 Xabar holatini «Mening xabarlarim» bo'limida ko'rishingiz mumkin.",
            reply_markup=contact_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Process support message error: {e}")
        await msg.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

@router.callback_query(F.data == "my_support_messages")
async def show_my_support_messages(call: types.CallbackQuery):
    try:
        logger.info(f"Show my support messages: {call.from_user.id}")
        user_messages = get_user_support_messages(call.from_user.id)
        
        if not user_messages:
            await call.message.edit_text(
                "📭 Siz hali hech qanday xabar yubormagansiz.\n\n"
                "📞 Savolingiz bo'lsa, «Xabar yuborish» tugmasini bosing.",
                reply_markup=contact_admin_keyboard()
            )
            return
        
        messages_text = "📋 <b>Mening Xabarlarim</b>\n\n"
        
        for msg in user_messages[:5]:  # Oxirgi 5 ta xabarni ko'rsatish
            msg_id, user_id, message, status, admin_reply, created_date = msg
            
            messages_text += (
                f"📩 <b>Xabar #{msg_id}</b>\n"
                f"• Holat: {status}\n"
                f"• Sana: {created_date[:16]}\n"
                f"• Xabar: {message[:50]}...\n"
            )
            
            if admin_reply:
                messages_text += f"• Admin javobi: {admin_reply[:50]}...\n"
            
            messages_text += "\n"
        
        await call.message.edit_text(
            messages_text,
            reply_markup=contact_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Show my support messages error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data == "cancel_support")
async def cancel_support(call: types.CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Cancel support: {call.from_user.id}")
        await state.clear()
        await call.message.edit_text(
            "❌ Xabar yuborish bekor qilindi.",
            reply_markup=contact_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Cancel support error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

# Admin qismlari
@router.callback_query(F.data == "admin_support_messages")
async def admin_support_messages(call: types.CallbackQuery):
    try:
        logger.info(f"Admin support messages: {call.from_user.id}")
        if call.from_user.id != ADMIN_ID:
            await call.answer("🚫 Ruxsat yo'q")
            return

        from app.database.db import get_pending_support_messages, get_pending_support_count
        
        pending_count = get_pending_support_count()
        messages = get_pending_support_messages()
        
        if not messages:
            await call.message.edit_text(
                "📭 Yangi support xabarlari mavjud emas.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
                ])
            )
            return

        await call.message.edit_text(
            f"📩 <b>Support Xabarlari</b>\n\n"
            f"📊 Kutilayotgan xabarlar: <b>{pending_count} ta</b>\n\n"
            f"Quyidagi xabarlarni ko'rib chiqing:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
            ])
        )

        for msg in messages:
            msg_id, user_id, message, status, admin_reply, created_date = msg
            user = get_user(user_id)
            username = user[1] if user else "Noma'lum"
            
            message_text = (
                f"📩 <b>Support Xabari #{msg_id}</b>\n\n"
                f"👤 Foydalanuvchi: <code>{user_id}</code>\n"
                f"📛 Username: @{username}\n"
                f"📅 Vaqt: {created_date}\n"
                f"💰 Balans: {user[2]:,} so'm\n\n"
                f"💬 Xabar:\n{message}\n\n"
                f"📊 Holat: {status}"
            )
            
            await call.message.answer(
                message_text,
                reply_markup=admin_support_action_keyboard(msg_id)
            )
    except Exception as e:
        logger.error(f"Admin support messages error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data.startswith("reply_support_"))
async def start_reply_support(call: types.CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Start reply support: {call.from_user.id}")
        if call.from_user.id != ADMIN_ID:
            await call.answer("🚫 Ruxsat yo'q")
            return

        message_id = int(call.data.split("_")[2])
        await state.set_state(SupportStates.awaiting_reply)
        await state.update_data(message_id=message_id)
        
        await call.message.edit_text(
            f"✍️ <b>Javob yozish</b>\n\n"
            f"Xabar #{message_id} uchun javobingizni yuboring:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_support_messages")]
            ])
        )
    except Exception as e:
        logger.error(f"Start reply support error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.message(SupportStates.awaiting_reply)
async def process_support_reply(msg: types.Message, state: FSMContext, bot: Bot):
    try:
        logger.info(f"Process support reply: {msg.from_user.id}")
        data = await state.get_data()
        message_id = data['message_id']
        
        support_message = get_support_message(message_id)
        if not support_message:
            await msg.answer("❌ Xabar topilmadi")
            await state.clear()
            return

        msg_id, user_id, message, status, admin_reply, created_date = support_message
        
        # Support xabarini yangilash
        update_support_message_status(message_id, "✅ Javob berildi", msg.text)
        
        # Foydalanuvchiga javob yuborish
        try:
            user_text = (
                f"📨 <b>Admin Javobi</b>\n\n"
                f"💬 Sizning xabaringiz:\n{message}\n\n"
                f"👤 Admin javobi:\n{msg.text}\n\n"
                f"📅 Javob vaqti: {msg.date.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"ℹ️ Qo'shimcha savollar bo'lsa, yana xabar yuborishingiz mumkin."
            )
            await bot.send_message(user_id, user_text)
        except Exception as e:
            logger.error(f"Failed to send reply to user: {e}")
        
        await state.clear()
        
        await msg.answer(
            f"✅ <b>Javob muvaffaqiyatli yuborildi!</b>\n\n"
            f"📋 Xabar raqami: #{message_id}\n"
            f"👤 Foydalanuvchi: {user_id}\n"
            f"💬 Javob: {msg.text[:50]}...",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="📩 Boshqa xabarlar", callback_data="admin_support_messages")]
            ])
        )
    except Exception as e:
        logger.error(f"Process support reply error: {e}")
        await msg.answer("❌ Xatolik yuz berdi")

@router.callback_query(F.data.startswith("close_support_"))
async def close_support_message(call: types.CallbackQuery, bot: Bot):
    try:
        logger.info(f"Close support message: {call.from_user.id}")
        if call.from_user.id != ADMIN_ID:
            await call.answer("🚫 Ruxsat yo'q")
            return

        message_id = int(call.data.split("_")[2])
        
        support_message = get_support_message(message_id)
        if not support_message:
            await call.answer("❌ Xabar topilmadi")
            return

        msg_id, user_id, message, status, admin_reply, created_date = support_message
        
        # Support xabarini yopish
        update_support_message_status(message_id, "✅ Yopildi", "Javobsiz yopildi")
        
        await call.message.edit_text(
            call.message.text + "\n\n✅ <b>Xabar yopildi</b>"
        )
        await call.answer("Xabar yopildi")
    except Exception as e:
        logger.error(f"Close support message error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)