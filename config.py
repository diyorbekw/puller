import logging

# Bot konfiguratsiyasi
TOKEN = "7694896433:AAEMFZL1HPBmnkiG88BpG3WPjeLr_pW7gIk"
ADMIN_ID = 5515940993 
BOT_USERNAME = "DiyorPortfolioBot" 

MIN_WITHDRAW = 10000
NO_COMMISSION_LIMIT = 50000
REFERRAL_BONUS = 50

AD_PRICES = {
    "1_week": 50,
    "2_weeks": 75,
    "1_month": 100
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