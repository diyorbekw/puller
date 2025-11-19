import logging

# Bot konfiguratsiyasi
TOKEN = "7694896433:AAEMFZL1HPBmnkiG88BpG3WPjeLr_pW7gIk"
ADMIN_ID = 5515940993 
BOT_USERNAME = "DiyorPortfolioBot"

# Pul yechish sozlamalari
MIN_WITHDRAW = 10000
NO_COMMISSION_LIMIT = 50000
REFERRAL_BONUS = 50

# Logger sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)