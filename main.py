import json, os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.request import HTTPXRequest

TOKEN = os.environ.get("8860716931:AAEDiVT7cWHAg5DQuKVQUYtD0_K3dyWF-Zo")
ADMIN_IDS = [9054441429]

USERS_FILE = "users.json"
users_db = {}
pending = {}
anon_counter = 100

if os.path.exists(USERS_FILE):
    try:
        with open(USERS_FILE, "r") as f:
            data = json.load(f)
            users_db = {int(k): v for k, v in data.get("users_db", {}).items()}
            pending = {int(k): v for k, v in data.get("pending", {}).items()}
            anon_counter = data.get("anon_counter", 100)
    except:
        pass

def save_db():
    with open(USERS_FILE, "w") as f:
        json.dump({"users_db": users_db, "pending": pending, "anon_counter": anon_counter}, f)

def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_or_create_user(user):
    global anon_counter
    for k, v in users_db.items():
        if v['telegram_id'] == user.id:
            return k
    anon_counter += 1
    users_db[anon_counter] = {"telegram_id": user.id, "username": user.username, "name": user.full_name}
    save_db()
    return anon_counter

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to 1840 & Company Support\n\nYou are chatting with the 1840 Team.\n\nCommands:\n/message - Send a message to support\n/status - Check your last message status\n/faq - Quick answers\n/help - How this works\n\nYou can send text, pictures, or files. Just type /message first.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("How it works:\n1. Type /message\n2. Send your question, picture, or file\n3. 1840 & Company Support will reply here")

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 1840 & Company - FAQ\n\n"
        "1. How to Apply?\nSend /message and ask for open roles\n\n"
        "2. What roles do you have?\nVA, Customer Support, Marketing, Tech, Design\n\n"
        "3. How does payment work?\nWe pay via Bank Deposit and Crypto.\nSend /message to ask about payment details for your role.\n\n"
        "4. What payment methods do you accept?\n✅ Bank Deposit\n✅ Crypto (USDT / BTC)\n\n"
        "For personal help, use /message"
    )

async def message_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['waiting_for_message'] = True
    await update.message.reply_text("✍️ Send your message now. You can send text, picture, or file. It will go to 1840 & Company Support.")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    for anon_id, data in users_db.items():
        if data['telegram_id'] == user_id:
            status = "Pending - waiting for reply" if anon_id in pending else "Replied / Closed"
            await update.message.reply_text(f"Your last message (ID: {anon_id}) Status: {status}")
            return
    await update.message.reply_text("You have no messages yet. Use /message to send one.")

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['waiting_for_message'] = False
    await update.message.reply_text("Cancelled. Use /message to start again.")

async def handle_admin_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    caption = msg.caption or ""
    parts = caption.split(maxsplit=2)
    if len(parts) < 2:
        await update.message.reply_text("Use caption: /reply [id] [message]")
        return
    try:
        anon_id = int(parts[1])
        reply_text = parts[2] if len(parts) > 2 else ""
        user_data = users_db.get(anon_id)
        if not user_data:
            await update.message.reply_text("User not found.")
            return
        chat_id = user_data['telegram_id']
        prefix = f"💬 1840 & Company Support:\n\n{reply_text}"
        if msg.photo:
            await context.bot.send_photo(chat_id=chat_id, photo=msg.photo[-1].file_id, caption=prefix)
        elif msg.document:
            await context.bot.send_document(chat_id=chat_id, document=msg.document.file_id, caption=prefix)
        elif msg.video:
            await context.bot.send_video(chat_id=chat_id, video=msg.video.file_id, caption=prefix)
        elif msg.voice:
            await context.bot.send_voice(chat_id=chat_id, voice=msg.voice.file_id)
            if reply_text:
                await context.bot.send_message(chat_id=chat_id, text=prefix)
        elif msg.audio:
            await context.bot.send_audio(chat_id=chat_id, audio=msg.audio.file_id, caption=prefix)
        if anon_id in pending:
            del pending[anon_id]
        save_db()
        await update.message.reply_text(f"✅ Sent media to {anon_id}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    if is_admin(user.id):
        if msg.caption and msg.caption.startswith("/reply"):
            await handle_admin_media(update, context)
        else:
            await update.message.reply_text("Admins: Use /reply [id] [message] to reply. For photo/file, send it with caption: /reply 123 your text")
        return
    if not context.user_data.get('waiting_for_message'):
        await update.message.reply_text("To send to support, type /message first.")
        return
    anon_id = get_or_create_user(user)
    label = msg.text or msg.caption or "[Photo / File]"
    pending[anon_id] = label
    context.user_data['waiting_for_message'] = False
    save_db()
    header = f"📩 NEW MESSAGE\n\nID: {anon_id}\nFrom: {user.full_name} (@{user.username})\nUser Telegram ID: {user.id}\n\n"
    for admin_id in ADMIN_IDS:
        try:
            if msg.photo:
                await context.bot.send_photo(chat_id=admin_id, photo=msg.photo[-1].file_id, caption=header + f"Message:\n{msg.caption or ''}\n\nReply with:\n/reply {anon_id} your reply here")
            elif msg.document:
                await context.bot.send_document(chat_id=admin_id, document=msg.document.file_id, caption=header + f"File: {msg.document.file_name}\nCaption: {msg.caption or ''}\n\nReply with:\n/reply {anon_id} your reply here")
            elif msg.video:
                await context.bot.send_video(chat_id=admin_id, video=msg.video.file_id, caption=header + f"Caption: {msg.caption or ''}\n\nReply with:\n/reply {anon_id} your reply here")
            elif msg.voice:
                await context.bot.send_voice(chat_id=admin_id, voice=msg.voice.file_id, caption=header + "Voice message")
            elif msg.audio:
                await context.bot.send_audio(chat_id=admin_id, audio=msg.audio.file_id, caption=header + f"Caption: {msg.caption or ''}")
            elif msg.sticker:
                await context.bot.send_sticker(chat_id=admin_id, sticker=msg.sticker.file_id)
                await context.bot.send_message(chat_id=admin_id, text=header + f"Sticker from {anon_id}\n\nReply with:\n/reply {anon_id} your reply here")
            else:
                await context.bot.send_message(chat_id=admin_id, text=header + f"Message:\n{msg.text}\n\nReply with:\n/reply {anon_id} your reply here")
        except Exception as e:
            await context.bot.send_message(chat_id=admin_id, text=header + f"Message:\n{label}\n\n(Forward failed: {e})")
    await update.message.reply_text("✅ Sent to 1840 & Company Support. You will get a reply here soon.")

async def reply_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Use: /reply [id] [message]\nExample: /reply 101 Hello, send your CV")
        return
    try:
        anon_id = int(context.args[0])
        reply_text = " ".join(context.args[1:])
        user_data = users_db.get(anon_id)
        if not user_data:
            await update.message.reply_text("User not found.")
            return
        await context.bot.send_message(chat_id=user_data['telegram_id'], text=f"💬 1840 & Company Support:\n\n{reply_text}")
        if anon_id in pending:
            del pending[anon_id]
        save_db()
        await update.message.reply_text(f"✅ Replied to {anon_id} as 1840 & Company Support")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not pending:
        await update.message.reply_text("No pending messages.")
        return
    text = "📋 PENDING MESSAGES:\n\n"
    for anon_id, msg in pending.items():
        u = users_db[anon_id]
        text += f"ID: {anon_id} - {u['name']} (@{u['username']})\nMsg: {msg}\n---\n"
    await update.message.reply_text(text)

async def view_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Use: /view [id]")
        return
    anon_id = int(context.args[0])
    u = users_db.get(anon_id)
    if u:
        await update.message.reply_text(f"User {anon_id}\nName: {u['name']}\nUsername: @{u['username']}\nTelegram ID: {u['telegram_id']}\nPending: {pending.get(anon_id, 'None')}")
    else:
        await update.message.reply_text("Not found.")

async def close_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    anon_id = int(context.args[0])
    if anon_id in pending:
        del pending[anon_id]
    save_db()
    await update.message.reply_text(f"Closed conversation {anon_id}")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    msg = " ".join(context.args)
    for anon_id, u in users_db.items():
        await context.bot.send_message(chat_id=u['telegram_id'], text=f"📢 1840 & Company Support:\n\n{msg}")
    await update.message.reply_text("Broadcast sent.")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(f"Total Users: {len(users_db)}\nPending: {len(pending)}")

def build_app():
    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0, write_timeout=30.0, pool_timeout=30.0)
    app = ApplicationBuilder().token(TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("faq", faq))
    app.add_handler(CommandHandler("message", message_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CommandHandler("reply", reply_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("view", view_cmd))
    app.add_handler(CommandHandler("close", close_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd)) 
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL | filters.VIDEO | filters.VOICE | filters.AUDIO | filters.Sticker.ALL, handle_user_message))
    return app

if __name__ == "__main__":
    print("1840 Bot Running...")
    if not TOKEN:
        print("ERROR: BOT_TOKEN not set!")
    else:
        app = build_app()
        app.run_polling(drop_pending_updates=True)
