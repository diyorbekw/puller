TOKEN = "7694896433:AAEMFZL1HPBmnkiG88BpG3WPjeLr_pW7gIk"
ADMIN_ID = 5515940993

# Pul yechish limitlari
MIN_WITHDRAW = 10000
NO_COMMISSION_LIMIT = 20000

# Bot konfiguratsiyasi
BOT_USERNAME = "DiyorPortfolioBot"

# Logging konfiguratsiyasi
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)