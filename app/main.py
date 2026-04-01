from interfaces.telegram_bot import run_bot
from loguru import logger

if __name__ == "__main__":
    logger.add("logs/app.log")
    run_bot()