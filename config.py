import logging

# Bot konfiguratsiyasi
TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = 123456789 
BOT_USERNAME = "Bot_username" 

MIN_WITHDRAW = 10000
NO_COMMISSION_LIMIT = 50000
REFERRAL_BONUS = 50

AD_PRICES = {
    "1_week": 2000,
    "2_weeks": 3500,
    "1_month": 6000
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
