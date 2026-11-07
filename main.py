from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8860716931:AAFh65AzhHxbhYxwyHD24-6qa9ecZzSVy7Y"
ADMIN_IDS = [9054441429]
users_db = {}
pending = {}
anon_counter = 100

jobs_db = {
    1: {"title": "Virtual Assistant", "pay": "$400-$600/mo", "needed": 15, "available": 12},
    2: {"title": "Customer Support Rep", "pay": "$500/mo", "needed": 20, "available": 18},
    3: {"title": "Social Media Manager", "pay": "$600/mo", "needed": 8, "available": 8},
    4: {"title": "Data Entry Specialist", "pay": "$350/mo", "needed": 10, "available": 5},
}

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to 1840 & Company Support\n\n"
        "You are chatting with the 1840 Team.\n\n"
        "Commands:\n"
        "/message - Send a message to support\n"
        "/jobs - See freelancing jobs & workers available\n"
        "/status - Check your message status\n"
        "/faq - Quick answers\n"
        "/help - How this works"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Type /message to send a question. Type /jobs to see available freelancing jobs. You will only see '1840 & Company Support', not the staff's personal account.")

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 1840 FAQ\n\n1. How to Apply? - Send /message and ask for open roles\n2. Do you hire from Nigeria? - Yes, globally\n3. What roles? - VA, Support, Marketing, Tech\n4. Payment? - Per role, after vetting\n\nFor personal help, use /message")

async def message_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['waiting_for_message'] = True
    await update.message.reply_text("✍️ Type your message now. It will go to 1840 & Company Support.")

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

async def jobs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "💼 1840 & Company - Freelancing Jobs Available\n\n"
    total_needed = 0
    total_available = 0
    for job_id, job in jobs_db.items():
        status = "🟢 Hiring" if job['available'] < job['needed'] else "🔴 Full"
        slots_left = job['needed'] - job['available']
        text += f"{job_id}. {job['title']} - {job['pay']}\nWorkers Needed: {job['needed']} | Workers Joined: {job['available']} | Slots Left: {slots_left}\nStatus: {status}\n\n"
        total_needed += job['needed']
        total_available += job['available']
    text += f"📊 Total: {total_available} workers joined out of {total_needed} needed\n\nTo apply, send /message and type the job name."
    await update.message.reply_text(text)

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global anon_counter
    user = update.effective_user
    if is_admin(user.id):
        await update.message.reply_text("Admins: Use /reply [id] [message]. Use /list to see pending.")
        return
    if not context.user_data.get('waiting_for_message'):
        await update.message.reply_text("To send to support, type /message first.")
        return
    anon_id = None
    for k, v in users_db.items():
        if v['telegram_id'] == user.id:
            anon_id = k
            break
    if not anon_id:
        anon_counter += 1
        anon_id = anon_counter
        users_db[anon_id] = {"telegram_id": user.id, "username": user.username, "name": user.full_name}
    pending[anon_id] = update.message.text
    context.user_data['waiting_for_message'] = False
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(chat_id=admin_id, text=f"📩 NEW MESSAGE\n\nID: {anon_id}\nFrom: {user.full_name} (@{user.username})\nUser Telegram ID: {user.id}\n\nMessage:\n{update.message.text}\n\nReply with:\n/reply {anon_id} your reply here")
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

async def addjob_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    try:
        full = " ".join(context.args)
        parts = [p.strip() for p in full.split("|")]
        title, pay, needed, available = parts[0], parts[1], int(parts[2]), int(parts[3])
        new_id = max(jobs_db.keys()) + 1 if jobs_db else 1
        jobs_db[new_id] = {"title": title, "pay": pay, "needed": needed, "available": available}
        await update.message.reply_text(f"✅ Added Job {new_id}: {title}")
    except:
        await update.message.reply_text("Use: /addjob Title | Pay | Needed | Available\nExample: /addjob Graphic Designer | $500/mo | 10 | 3")

async def updatejob_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    try:
        job_id = int(context.args[0])
        new_available = int(context.args[1])
        jobs_db[job_id]["available"] = new_available
        await update.message.reply_text(f"✅ Updated {jobs_db[job_id]['title']}: Workers Joined now {new_available}")
    except:
        await update.message.reply_text("Use: /updatejob [id] [new number]\nExample: /updatejob 1 14")

async def removejob_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    try:
        job_id = int(context.args[0])
        removed = jobs_db.pop(job_id)
        await update.message.reply_text(f"✅ Removed: {removed['title']}")
    except:
        await update.message.reply_text("Use: /removejob [id]")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("faq", faq))
app.add_handler(CommandHandler("message", message_cmd))
app.add_handler(CommandHandler("status", status_cmd))
app.add_handler(CommandHandler("cancel", cancel_cmd))
app.add_handler(CommandHandler("jobs", jobs_cmd))
app.add_handler(CommandHandler("reply", reply_cmd))
app.add_handler(CommandHandler("list", list_cmd))
app.add_handler(CommandHandler("view", view_cmd))
app.add_handler(CommandHandler("close", close_cmd))
app.add_handler(CommandHandler("broadcast", broadcast_cmd))
app.add_handler(CommandHandler("stats", stats_cmd))
app.add_handler(CommandHandler("addjob", addjob_cmd))
app.add_handler(CommandHandler("updatejob", updatejob_cmd))
app.add_handler(CommandHandler("removejob", removejob_cmd))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
print("1840 Bot Running...")
app.run_polling()