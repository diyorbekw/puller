from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import logger, MIN_WITHDRAW, NO_COMMISSION_LIMIT
from app.database.db import get_user, update_balance, add_withdraw_request
from app.keyboards.inline import back_to_menu_keyboard, confirm_withdraw_keyboard

router = Router()

class WithdrawStates(StatesGroup):
    awaiting_card = State()
    confirming = State()

@router.callback_query(F.data == "withdraw")
async def withdraw_start(call: types.CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Withdraw start: {call.from_user.id}")
        user = get_user(call.from_user.id)
        balance = user[2]

        if balance < MIN_WITHDRAW:
            await call.message.edit_text(
                f"❌ <b>Pul yechish imkoni yo'q</b>\n\n"
                f"💰 Joriy balans: <b>{balance:,} so'm</b>\n"
                f"📊 Minimal yechish miqdori: <b>{MIN_WITHDRAW:,} so'm</b>\n\n"
                f"💡 Iltimos, balansingizni {MIN_WITHDRAW:,} so'mgacha yetkazing va qayta urinib ko'ring.",
                reply_markup=back_to_menu_keyboard()
            )
            return

        commission = int(balance * 0.1) if balance < NO_COMMISSION_LIMIT else 0
        amount = balance - commission

        await state.set_state(WithdrawStates.awaiting_card)
        await state.update_data(balance=balance, commission=commission, amount=amount)
        
        await call.message.edit_text(
            f"💸 <b>Pul Yechish</b>\n\n"
            f"💰 Joriy balans: <b>{balance:,} so'm</b>\n"
            f"🧾 Komissiya: <b>{commission:,} so'm</b>\n"
            f"💳 Olinadigan summa: <b>{amount:,} so'm</b>\n\n"
            f"📝 <b>Karta raqamingizni yuboring:</b>\n"
            f"(8600 bilan boshlanuvchi 16 xonali raqam)",
            reply_markup=back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Withdraw start error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.message(WithdrawStates.awaiting_card)
async def process_card(msg: types.Message, state: FSMContext):
    try:
        logger.info(f"Process card: {msg.from_user.id}")
        card = msg.text.strip()
        
        if not (card.isdigit() and card.startswith("8600") and len(card) == 16):
            await msg.answer("❌ <b>Noto'g'ri karta raqami!</b>\n\n"
                            "Iltimos, 8600 bilan boshlanuvchi 16 xonali raqam kiriting.\n"
                            "Masalan: <code>8600 1234 5678 9012</code>")
            return

        data = await state.get_data()
        balance = data['balance']
        commission = data['commission']
        amount = data['amount']

        await state.set_state(WithdrawStates.confirming)
        await state.update_data(card=card)
        
        await msg.answer(
            f"✅ <b>So'rovni tasdiqlang</b>\n\n"
            f"💳 Karta raqam: <code>{card}</code>\n"
            f"💰 Yechiladigan summa: <b>{amount:,} so'm</b>\n"
            f"🧾 Komissiya: <b>{commission:,} so'm</b>\n"
            f"📊 Joriy balans: <b>{balance:,} so'm</b>\n\n"
            f"⚠️ <i>So'rovni tasdiqlasangiz, balansingizdan {balance:,} so'm yechiladi</i>",
            reply_markup=confirm_withdraw_keyboard()
        )
    except Exception as e:
        logger.error(f"Process card error: {e}")
        await msg.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

@router.callback_query(WithdrawStates.confirming, F.data == "confirm_withdraw")
async def confirm_withdraw(call: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        card = data['card']
        balance = data['balance']
        commission = data['commission']
        amount = data['amount']

        # Balansni yangilash va so'rov qo'shish
        update_balance(call.from_user.id, -balance)
        req_id = add_withdraw_request(call.from_user.id, card, amount, commission)
        
        logger.info(f"Withdraw confirmed: {call.from_user.id} - amount: {amount} - req_id: {req_id}")
        
        await state.clear()
        
        await call.message.edit_text(
            f"✅ <b>So'rov muvaffaqiyatli yuborildi!</b>\n\n"
            f"📋 So'rov raqami: <b>#{req_id}</b>\n"
            f"💳 Karta: <code>{card}</code>\n"
            f"💰 Miqdor: <b>{amount:,} so'm</b>\n"
            f"🧾 Komissiya: <b>{commission:,} so'm</b>\n\n"
            f"⏳ So'rov admin tomonidan tekshirilmoqda.\n"
            f"💰 Pul kartangizga 1-24 soat ichida tushadi.\n\n"
            f"📞 Savollar bo'lsa: @avnadmin",
            reply_markup=back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Confirm withdraw error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data == "cancel_withdraw")
async def cancel_withdraw(call: types.CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Withdraw cancelled: {call.from_user.id}")
        await state.clear()
        await call.message.edit_text(
            "❌ Pul yechish bekor qilindi.",
            reply_markup=back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Cancel withdraw error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)