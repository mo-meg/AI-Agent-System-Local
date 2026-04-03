"""
Background scheduler — runs two recurring jobs:
1. Daily plan push at configured time
2. Reminder check every 60 seconds
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from app.config import DAILY_PLAN_HOUR, DAILY_PLAN_MINUTE, ALLOWED_USER_IDS
from memory.store import get_pending_reminders, mark_reminder_sent
from agents import planner_agent

_scheduler = AsyncIOScheduler()
_bot_app = None   # set by telegram_bot.py at startup


def set_bot(app):
    global _bot_app
    _bot_app = app


async def _push_daily_plan():
    if not _bot_app or not ALLOWED_USER_IDS:
        return
    for uid in ALLOWED_USER_IDS:
        try:
            plan = planner_agent.run(user_id=uid)
            await _bot_app.bot.send_message(
                chat_id=uid,
                text=f"🌅 *Good morning! Here's your plan:*\n\n{plan}",
                parse_mode="Markdown",
            )
            logger.info(f"Daily plan sent to {uid}")
        except Exception as e:
            logger.error(f"Failed to send daily plan to {uid}: {e}")


async def _check_reminders():
    if not _bot_app:
        return
    pending = get_pending_reminders()
    for reminder in pending:
        try:
            await _bot_app.bot.send_message(
                chat_id=reminder.user_id,
                text=f"⏰ *Reminder:* {reminder.content}",
                parse_mode="Markdown",
            )
            mark_reminder_sent(reminder.id)
            logger.info(f"Reminder {reminder.id} fired for user {reminder.user_id}")
        except Exception as e:
            logger.error(f"Failed to send reminder {reminder.id}: {e}")


def start_scheduler():
    _scheduler.add_job(
        _push_daily_plan,
        trigger="cron",
        hour=DAILY_PLAN_HOUR,
        minute=DAILY_PLAN_MINUTE,
        id="daily_plan",
    )
    _scheduler.add_job(
        _check_reminders,
        trigger="interval",
        seconds=60,
        id="reminder_check",
    )
    _scheduler.start()
    logger.info("Scheduler started.")


def stop_scheduler():
    _scheduler.shutdown()
