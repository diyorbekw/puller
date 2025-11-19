from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import logger, AD_PRICES, BOT_USERNAME
from app.database.db import (
    get_user, update_balance, add_ad_request, get_user_ad_requests,
    add_task
)
from app.keyboards.inline import (
    ads_menu_keyboard, ad_duration_keyboard, bot_check_keyboard,
    confirm_ad_keyboard, back_to_menu_keyboard, low_balance_keyboard
)

router = Router()

class AdStates(StatesGroup):
    awaiting_channel_name = State()
    awaiting_channel_username = State()
    awaiting_bot_check = State()
    awaiting_duration = State()
    awaiting_description = State()
    confirming = State()

@router.callback_query(F.data == "ads_menu")
async def show_ads_menu(call: types.CallbackQuery):
    try:
        logger.info(f"Ads menu: {call.from_user.id}")
        await call.message.edit_text(
            "📢 <b>Reklama Bo'limi</b>\n\n"
            "🎯 Kanalingizni reklama qiling va yangi obunchilarni jalb qiling!\n\n"
            "💡 <b>Qanday ishlaydi?</b>\n"
            "1. Kanalingiz ma'lumotlarini kiritasiz\n"
            "2. Botni kanalingizga qo'shasiz\n"
            "3. Reklama muddatini tanlaysiz\n"
            "4. Tavsif qo'shasiz\n"
            "5. Admin ma'qullagach, reklama boshlanadi\n\n"
            "💰 <b>Narxlar:</b>\n"
            "• 1 hafta - 2,000 so'm\n"
            "• 2 hafta - 3,500 so'm\n"
            "• 1 oy - 6,000 so'm",
            reply_markup=ads_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Ads menu error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data == "add_ad")
async def start_add_ad(call: types.CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Start add ad: {call.from_user.id}")
        user = get_user(call.from_user.id)
        
        if user[2] < min(AD_PRICES.values()):
            await call.message.edit_text(
                f"❌ <b>Balansingiz yetarli emas!</b>\n\n"
                f"💰 Joriy balans: <b>{user[2]:,} so'm</b>\n"
                f"💳 Minimal reklama narxi: <b>{min(AD_PRICES.values()):,} so'm</b>\n\n"
                f"💡 Balansingizni to'ldirish uchun admin bilan bog'lanishingiz mumkin.",
                reply_markup=low_balance_keyboard()
            )
            return
        
        await state.set_state(AdStates.awaiting_channel_name)
        await call.message.edit_text(
            "📝 <b>Reklama qo'shish</b>\n\n"
            "1-qadam: Kanal nomini yuboring\n\n"
            "Masalan: <code>Python Dasturlash</code>",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="ads_menu")]
            ])
        )
    except Exception as e:
        logger.error(f"Start add ad error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.message(AdStates.awaiting_channel_name)
async def process_channel_name(msg: types.Message, state: FSMContext):
    try:
        logger.info(f"Process channel name: {msg.from_user.id}")
        await state.update_data(channel_name=msg.text)
        await state.set_state(AdStates.awaiting_channel_username)
        
        await msg.answer(
            "2-qadam: Kanal username'ini yuboring (@ belgisiz)\n\n"
            "Masalan: <code>python_dasturlash</code>"
        )
    except Exception as e:
        logger.error(f"Process channel name error: {e}")
        await msg.answer("❌ Xatolik yuz berdi. Qaytadan boshlang.")

@router.message(AdStates.awaiting_channel_username)
async def process_channel_username(msg: types.Message, state: FSMContext):
    try:
        logger.info(f"Process channel username: {msg.from_user.id}")
        channel_username = msg.text.strip().replace('@', '')
        await state.update_data(channel_username=channel_username)
        await state.set_state(AdStates.awaiting_bot_check)
        
        await msg.answer(
            f"3-qadam: Botni kanalingizga qo'shdingizmi?\n\n"
            f"📢 Kanal: @{channel_username}\n"
            f"🤖 Bot: @{BOT_USERNAME}\n\n"
            f"Botni kanalingizga administrator qilib qo'shing va "
            f"«Ha, qo'shdim» tugmasini bosing.",
            reply_markup=bot_check_keyboard()
        )
    except Exception as e:
        logger.error(f"Process channel username error: {e}")
        await msg.answer("❌ Xatolik yuz berdi. Qaytadan boshlang.")

@router.callback_query(AdStates.awaiting_bot_check, F.data == "bot_added_yes")
async def check_bot_membership(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    try:
        logger.info(f"Check bot membership: {call.from_user.id}")
        data = await state.get_data()
        channel_username = data['channel_username']
        
        # Botni kanalda borligini tekshirish
        try:
            chat_member = await bot.get_chat_member(f"@{channel_username}", bot.id)
            is_admin = chat_member.status in ['administrator', 'creator']
            
            if not is_admin:
                await call.answer("❌ Bot kanalda administrator emas! Iltimos, botni administrator qilib qo'shing.", show_alert=True)
                return
                
        except Exception as e:
            logger.error(f"Bot membership check error: {e}")
            await call.answer("❌ Botni kanalda topa olmadim! Iltimos, botni kanalga qo'shganingizni tekshiring.", show_alert=True)
            return
        
        await state.set_state(AdStates.awaiting_duration)
        await call.message.edit_text(
            "4-qadam: Reklama muddatini tanlang\n\n"
            "💰 <b>Narxlar:</b>\n"
            "• 1 hafta - 2,000 so'm\n"
            "• 2 hafta - 3,500 so'm\n"
            "• 1 oy - 6,000 so'm",
            reply_markup=ad_duration_keyboard()
        )
    except Exception as e:
        logger.error(f"Check bot membership error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(AdStates.awaiting_bot_check, F.data == "bot_added_no")
async def bot_not_added(call: types.CallbackQuery):
    await call.answer("❌ Iltimos, avval botni kanalga qo'shing!", show_alert=True)

@router.callback_query(AdStates.awaiting_duration, F.data.startswith("ad_duration_"))
async def process_duration(call: types.CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Process duration: {call.from_user.id}")
        duration_key = call.data.replace("ad_duration_", "")
        
        duration_map = {
            "1_week": "1 hafta",
            "2_weeks": "2 hafta", 
            "1_month": "1 oy"
        }
        
        price = AD_PRICES[duration_key]
        duration_text = duration_map[duration_key]
        
        await state.update_data(duration=duration_text, price=price)
        await state.set_state(AdStates.awaiting_description)
        
        await call.message.edit_text(
            f"5-qadam: Reklama tavsifini yuboring\n\n"
            f"📊 Ma'lumotlar:\n"
            f"• Kanal: {(await state.get_data())['channel_name']}\n"
            f"• Username: @{(await state.get_data())['channel_username']}\n"
            f"• Muddat: {duration_text}\n"
            f"• Narx: {price:,} so'm\n\n"
            f"📝 <b>Tavsif misoli:</b>\n"
            f"<code>Python dasturlash tilini o'rganish uchun ajoyib kanal. "
            f"Har kuni yangi darslar va loyihalar. Obuna bo'ling!</code>"
        )
    except Exception as e:
        logger.error(f"Process duration error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.message(AdStates.awaiting_description)
async def process_description(msg: types.Message, state: FSMContext):
    try:
        logger.info(f"Process description: {msg.from_user.id}")
        await state.update_data(description=msg.text)
        await state.set_state(AdStates.confirming)
        
        data = await state.get_data()
        
        confirm_text = (
            f"✅ <b>Reklama ma'lumotlari</b>\n\n"
            f"📢 Kanal nomi: <b>{data['channel_name']}</b>\n"
            f"🔗 Username: @{data['channel_username']}\n"
            f"⏳ Muddat: <b>{data['duration']}</b>\n"
            f"💰 Narx: <b>{data['price']:,} so'm</b>\n"
            f"📝 Tavsif: {data['description']}\n\n"
            f"⚠️ <b>Diqqat!</b>\n"
            f"• So'rov admin tomonidan tekshiriladi\n"
            f"• Ma'qullangach, reklama boshlanadi\n"
            f"• Rad etilgan taqdirda, pul qaytarilmaydi\n\n"
            f"Tasdiqlaysizmi?"
        )
        
        await msg.answer(confirm_text, reply_markup=confirm_ad_keyboard())
    except Exception as e:
        logger.error(f"Process description error: {e}")
        await msg.answer("❌ Xatolik yuz berdi. Qaytadan boshlang.")

@router.callback_query(AdStates.confirming, F.data == "confirm_ad")
async def confirm_ad_request(call: types.CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Confirm ad request: {call.from_user.id}")
        data = await state.get_data()
        user = get_user(call.from_user.id)
        
        # Balansni tekshirish
        if user[2] < data['price']:
            await call.answer("❌ Balansingiz yetarli emas!", show_alert=True)
            await state.clear()
            await show_ads_menu(call)
            return
        
        # Balansdan yechish
        update_balance(call.from_user.id, -data['price'])
        
        # Reklama so'rovini qo'shish
        request_id = add_ad_request(
            call.from_user.id,
            data['channel_name'],
            data['channel_username'],
            data['duration'],
            data['description'],
            data['price']
        )
        
        await state.clear()
        
        logger.info(f"Ad request added: {request_id} by {call.from_user.id}")
        
        await call.message.edit_text(
            f"✅ <b>Reklama so'rovi muvaffaqiyatli yuborildi!</b>\n\n"
            f"📋 So'rov raqami: <b>#{request_id}</b>\n"
            f"💰 To'lov: <b>{data['price']:,} so'm</b>\n"
            f"💳 Qolgan balans: <b>{get_user(call.from_user.id)[2]:,} so'm</b>\n\n"
            f"⏳ So'rov admin tomonidan tekshirilmoqda.\n"
            f"📞 Natijani 1-24 soat ichida olasiz.\n\n"
            f"ℹ️ Savollar bo'lsa admin bilan bog'lanishingiz mumkin.",
            reply_markup=ads_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Confirm ad request error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)

@router.callback_query(F.data == "my_ads")
async def show_my_ads(call: types.CallbackQuery):
    try:
        logger.info(f"Show my ads: {call.from_user.id}")
        user_ads = get_user_ad_requests(call.from_user.id)
        
        if not user_ads:
            await call.message.edit_text(
                "📭 Siz hali hech qanday reklama so'rovi yubormagansiz.\n\n"
                "📢 Birinchi reklamangizni qo'shish uchun «Reklama qo'shish» tugmasini bosing.",
                reply_markup=ads_menu_keyboard()
            )
            return
        
        ad_text = "📋 <b>Mening Reklama So'rovlarim</b>\n\n"
        
        for ad in user_ads[:10]:  # Oxirgi 10 ta so'rovni ko'rsatish
            req_id, user_id, channel_name, channel_username, duration, description, price, status, admin_comment, created_date = ad
            
            ad_text += (
                f"📢 <b>So'rov #{req_id}</b>\n"
                f"• Kanal: {channel_name}\n"
                f"• Username: @{channel_username}\n"
                f"• Muddat: {duration}\n"
                f"• Narx: {price:,} so'm\n"
                f"• Holat: {status}\n"
            )
            
            if admin_comment:
                ad_text += f"• Izoh: {admin_comment}\n"
            
            ad_text += f"• Sana: {created_date[:10]}\n\n"
        
        await call.message.edit_text(ad_text, reply_markup=ads_menu_keyboard())
    except Exception as e:
        logger.error(f"Show my ads error: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)