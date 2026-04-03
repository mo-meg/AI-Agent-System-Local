"""
Telegram bot interface — enhanced with:
- /start, /help, /tasks, /notes, /plan, /clear commands
- Voice note handling via Whisper
- Image handling via vision agent
- Per-user auth guard
- Typing indicator while processing
"""
import os
import tempfile

from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)
from loguru import logger

from orchestrator.router import route_task
from agents.vision_agent import describe_image
from tools.whisper_client import transcribe_ogg
from tools.scheduler import set_bot, start_scheduler
from memory.store import list_tasks, list_notes
from agents.planner_agent import run as run_plan
from app.config import TELEGRAM_TOKEN, ALLOWED_USER_IDS


# ── Auth guard ────────────────────────────────────────────────

def _is_allowed(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return True   # open if no whitelist configured
    return user_id in ALLOWED_USER_IDS


# ── Command handlers ──────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return
    await update.message.reply_text(
        "👋 *Personal AI OS online.*\n\n"
        "Send me anything — a URL to summarize, a task to save, "
        "a voice note, an image, or just chat.\n\n"
        "Type /help for all commands.",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return
    help_text = (
        "🤖 *Commands*\n"
        "/tasks — list pending tasks\n"
        "/notes — list recent notes\n"
        "/plan — generate today's plan\n"
        "/clear — clear conversation context\n\n"
        "💬 *Just say:*\n"
        "• Any URL → summarized\n"
        "• 'remind me in 1h to ...' → reminder set\n"
        "• 'save note: ...' → note stored\n"
        "• 'done 3' → mark task #3 complete\n"
        "• Send a 🎤 voice note → transcribed & processed\n"
        "• Send a 🖼 photo → described by vision AI\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def cmd_tasks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return
    tasks = list_tasks(user_id=uid, done=False)
    if not tasks:
        await update.message.reply_text("✅ No pending tasks.")
        return
    lines = [f"`{t.id}.` [{t.priority}] {t.content}" for t in tasks]
    await update.message.reply_text("📋 *Pending tasks:*\n" + "\n".join(lines), parse_mode="Markdown")


async def cmd_notes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return
    notes = list_notes(user_id=uid, limit=8)
    if not notes:
        await update.message.reply_text("📭 No notes yet.")
        return
    lines = [f"• {n.content[:100]}" for n in notes]
    await update.message.reply_text("📝 *Recent notes:*\n" + "\n".join(lines), parse_mode="Markdown")


async def cmd_plan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return
    await update.message.chat.send_action("typing")
    plan = run_plan(user_id=uid)
    await update.message.reply_text(f"🗓 *Your plan:*\n\n{plan}", parse_mode="Markdown")


async def cmd_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return
    from memory.store import Session, ConversationContext
    with Session() as s:
        s.query(ConversationContext).filter_by(user_id=uid).delete()
        s.commit()
    await update.message.reply_text("🧹 Conversation context cleared.")


# ── Message handlers ──────────────────────────────────────────

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _is_allowed(uid):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    text = update.message.text
    logger.info(f"[{uid}] text: {text[:80]}")

    await update.message.chat.send_action("typing")
    response = route_task(user_id=uid, text=text)
    await update.message.reply_text(response, parse_mode="Markdown")


async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return

    logger.info(f"[{uid}] voice note received")
    await update.message.chat.send_action("typing")

    voice = update.message.voice
    file = await ctx.bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        ogg_path = tmp.name

    try:
        with open(ogg_path, "rb") as f:
            ogg_bytes = f.read()
        transcription = transcribe_ogg(ogg_bytes)
    finally:
        os.unlink(ogg_path)

    if not transcription:
        await update.message.reply_text("⚠️ Couldn't transcribe the voice note.")
        return

    await update.message.reply_text(f"🎤 *Heard:* _{transcription}_", parse_mode="Markdown")
    response = route_task(user_id=uid, text=transcription)
    await update.message.reply_text(response, parse_mode="Markdown")


async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not _is_allowed(uid):
        return

    logger.info(f"[{uid}] photo received")
    await update.message.chat.send_action("typing")

    photo = update.message.photo[-1]   # largest resolution
    file = await ctx.bot.get_file(photo.file_id)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        img_path = tmp.name

    try:
        caption = update.message.caption or ""
        description = describe_image(img_path)
    finally:
        os.unlink(img_path)

    reply = f"🖼 *Image description:*\n{description}"
    if caption:
        # Route caption + description together
        combined = f"{caption}\n\nImage shows: {description}"
        result = route_task(user_id=uid, text=combined)
        reply += f"\n\n{result}"

    await update.message.reply_text(reply, parse_mode="Markdown")


# ── Bot setup ─────────────────────────────────────────────────

def run_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("tasks", cmd_tasks))
    app.add_handler(CommandHandler("notes", cmd_notes))
    app.add_handler(CommandHandler("plan", cmd_plan))
    app.add_handler(CommandHandler("clear", cmd_clear))

    # Register message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Attach scheduler
    set_bot(app)
    app.post_init = lambda _: start_scheduler()

    # Set bot command menu in Telegram
    async def _set_commands(app):
        await app.bot.set_my_commands([
            BotCommand("start",  "Welcome message"),
            BotCommand("help",   "Show all commands"),
            BotCommand("tasks",  "List pending tasks"),
            BotCommand("notes",  "List recent notes"),
            BotCommand("plan",   "Generate today's plan"),
            BotCommand("clear",  "Clear conversation memory"),
        ])

    app.post_init = _set_commands

    logger.info("Bot running...")
    app.run_polling()
