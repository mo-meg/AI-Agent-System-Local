from loguru import logger
from memory.store import init_db
from interfaces.telegram_bot import run_bot

if __name__ == "__main__":
    logger.add("logs/app.log", rotation="10 MB", retention="7 days", level="INFO")
    logger.info("Initializing database...")
    init_db()
    logger.info("Starting Mego :) Personal AI OS...")
    run_bot()
