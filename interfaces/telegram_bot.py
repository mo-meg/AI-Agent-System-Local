import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from orchestrator.router import route_task
from loguru import logger
from app.config import TELEGRAM_TOKEN


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    logger.info(f"Incoming: {text}")

    try:
        response = await asyncio.to_thread(route_task, text)

        if not response:
            response = "⚠️ No response from agent"

    except Exception as e:
        logger.error(str(e))
        response = f"Error: {e}"

    await update.message.reply_text(response)


def run_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started...")
    app.run_polling()