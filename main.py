import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN") or os.getenv("TOKEN")

# --- CHANGE THIS ---
ADMIN_IDS = [123456789]

# --- DATA (in-memory) ---
JOBS = [
    {"id": 1, "title": "Virtual Assistant", "pay": "$400-$600/mo", "needed": 15, "joined": 3},
    {"id": 2, "title": "Customer Support Rep", "pay": "$500/mo", "needed": 20, "joined": 8},
    {"id": 3, "title": "Social Media Manager", "pay": "$600/mo", "needed": 8, "joined": 5},
    {"id": 4, "title": "Data Entry Specialist", "pay": "$350/mo", "needed": 10, "joined": 8},
    {"id": 5, "title": "Script Writing", "pay": "$450-$700/mo", "needed": 12, "joined": 0},
    {"id": 6, "title": "Video Editor", "pay": "$500-$800/mo", "needed": 10, "joined": 0},
    {"id": 7, "title": "Graphic Designer", "pay": "$450-$750/mo", "needed": 8, "joined": 0},
    {"id": 8, "title": "Content Writer / Blog Writer", "pay": "$400-$650/mo", "needed": 12, "joined": 0},
    {"id": 9, "title": "Transcriptionist", "pay": "$300-$500/mo", "needed": 15, "joined": 0},
]
USERS = {}
TASKS = [
    {"id": 1, "title": "Join our Telegram Channel", "reward": "$2"},
    {"id": 2, "title": "Follow us on Instagram", "reward": "$2"},
    {"id": 3, "title": "Invite 3 Friends", "reward": "$5"},
]
WITHDRAW_MIN = 10

def get_user(user):
    uid = user.id
    if uid not in USERS:
        USERS[uid] = {"name": user.first_name or "User", "username": user.username or "", "balance": 0.0, "referrals": 0, "my_jobs": []}
    return USERS[uid]

def is_admin(uid):
    return uid in ADMIN_IDS

def jobs_text():
    lines = ["💼 1840 & Company - Freelancing Jobs Available\n"]
    for j in JOBS:
        left = j["needed"] - j["joined"]
        status = "🔴 Full" if left <= 0 else "🟢 Hiring"
        lines.append(f'{j["id"]}. {j["title"]} - {j["pay"]}\nWorkers Needed: {j["needed"]} | Workers Joined: {j["joined"]} | Slots Left: {max(0, left)}\nStatus: {status}\n')
    return "\n".join(lines)

# --- MAIN ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user)
    # referral
    if context.args and context.args[0].startswith("ref_"):
        try:
            ref_id = int(context.args[0].replace("ref_", ""))
            if ref_id != update.effective_user.id and ref_id in USERS:
                USERS[ref_id]["referrals"] += 1
                USERS[ref_id]["balance"] += 2.0
        except Exception:
            pass
    kb = [
        [InlineKeyboardButton("💼 Jobs", callback_data="jobs"), InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance"), InlineKeyboardButton("🎁 Referral", callback_data="referral")],
        [InlineKeyboardButton("📋 Tasks", callback_data="tasks"), InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("🆘 Support", callback_data="support")],
    ]
    await update.message.reply_text(
        f"👋 Welcome {user['name']} to 1840 & Company!\n\n"
        "💼 Find freelancing jobs, earn, and withdraw.\n\n"
        "Commands:\n"
        "/jobs - See jobs\n"
        "/apply 1 - Apply for job\n"
        "/myjobs - My jobs\n"
        "/profile - My profile\n"
        "/balance - My balance\n"
        "/tasks - Earn tasks\n"
        "/referral - Invite & earn $2\n"
        "/withdraw - Withdraw money\n"
        "/support - Contact support\n\n"
        "Admin: /addjob /editjob /deletejob",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /start to see menu.\n/jobs - jobs\n/apply 1 - apply\n/profile - profile\n/balance - balance\n/tasks - tasks\n/referral - referral\n/withdraw - withdraw")

async def jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(jobs_text())

async def myjobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user)
    if not u["my_jobs"]:
        await update.message.reply_text("You have not applied for any job yet.\nUse /jobs then /apply 1")
        return
    lines = ["📋 My Jobs:\n"]
    for jid in u["my_jobs"]:
        for j in JOBS:
            if j["id"] == jid:
                lines.append(f"{j['id']}. {j['title']} - {j['pay']}")
    await update.message.reply_text("\n".join(lines))

async def apply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user)
    try:
        job_id = int(context.args[0])
    except Exception:
        await update.message.reply_text("Usage: /apply 1")
        return
    for j in JOBS:
        if j["id"] == job_id:
            if job_id in u["my_jobs"]:
                await update.message.reply_text("You already applied for this job.")
                return
            if j["joined"] >= j["needed"]:
                await update.message.reply_text("❌ Sorry, this job is Full.")
                return
            j["joined"] += 1
            u["my_jobs"].append(job_id)
            await update.message.reply_text(f"✅ Applied for {j['title']} - {j['pay']}\nAdmin will contact you soon.")
            return
    await update.message.reply_text("Job not found. Use /jobs")

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user)
    await update.message.reply_text(f"👤 Profile\n\nName: {u['name']}\nUsername: @{u['username']}\nID: {update.effective_user.id}\nBalance: ${u['balance']:.2f}\nReferrals: {u['referrals']}\nJobs Applied: {len(u['my_jobs'])}")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user)
    await update.message.reply_text(f"💰 Your Balance: ${u['balance']:.2f}\nMin Withdraw: ${WITHDRAW_MIN}\nUse /withdraw to cash out.")

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["📋 Tasks - Complete & Earn:\n"]
    for t in TASKS:
        lines.append(f"{t['id']}. {t['title']} - {t['reward']}")
    lines.append("\nSend /claim <task number> after you complete it.\nExample: /claim 1")
    await update.message.reply_text("\n".join(lines))

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user)
    try:
        tid = int(context.args[0])
        for t in TASKS:
            if t["id"] == tid:
                reward = float(t["reward"].replace("$", ""))
                u["balance"] += reward
                await update.message.reply_text(f"✅ Task claimed! +${reward}\nNew Balance: ${u['balance']:.2f}")
                return
        await update.message.reply_text("Task not found.")
    except Exception:
        await update.message.reply_text("Usage: /claim 1")

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user)
    bot_name = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_name}?start=ref_{update.effective_user.id}"
    await update.message.reply_text(f"🎁 Referral\n\nYour link:\n{link}\n\nYou earn $2 per friend.\nYour Referrals: {u['referrals']}\nYour Balance: ${u['balance']:.2f}")

async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user)
    if u["balance"] < WITHDRAW_MIN:
        await update.message.reply_text(f"❌ Min withdraw is ${WITHDRAW_MIN}.\nYour balance: ${u['balance']:.2f}\nDo tasks or referrals to earn more.")
        return
    await update.message.reply_text(f"💸 Withdraw Request: ${u['balance']:.2f}\n\nSend your wallet / bank details like this:\n/withdrawdetails Your Bank - Account Number - Name\n\nAdmin will process it.")
    return

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🆘 Support\n\nMessage admin here: @1840support\nOr send /help for commands.")

# --- ADMIN: ADD JOB ---
TITLE, PAY, NEEDED = range(3)

async def addjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admin can do this.")
        return ConversationHandler.END
    await update.message.reply_text("What is the job title?\nExample: Script Writing")
    return TITLE

async def addjob_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_title"] = update.message.text
    await update.message.reply_text("What is the pay?\nExample: $500/mo")
    return PAY

async def addjob_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_pay"] = update.message.text
    await update.message.reply_text("How many workers needed?\nExample: 10")
    return NEEDED

async def addjob_needed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        needed = int(update.message.text)
    except Exception:
        await update.message.reply_text("Send number only, e.g: 10")
        return NEEDED
    new_id = max([j["id"] for j in JOBS], default=0) + 1
    JOBS.append({"id": new_id, "title": context.user_data["new_title"], "pay": context.user_data["new_pay"], "needed": needed, "joined": 0})
    await update.message.reply_text(f"✅ Job added:\n{new_id}. {context.user_data['new_title']} - {context.user_data['new_pay']}")
    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

async def editjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admin can do this.")
        return
    try:
        job_id = int(context.args[0])
        field = context.args[1].lower()
        value = " ".join(context.args[2:])
        for j in JOBS:
            if j["id"] == job_id:
                if field in ["needed", "joined"]:
                    j[field] = int(value)
                elif field in ["title", "pay"]:
                    j[field] = value
                else:
                    await update.message.reply_text("Field must be: title | pay | needed | joined")
                    return
                await update.message.reply_text(f"✅ Updated:\n{j['id']}. {j['title']} - {j['pay']}")
                return
        await update.message.reply_text("Job not found.")
    except Exception:
        await update.message.reply_text("Usage:\n/editjob 5 pay $600/mo\n/editjob 5 needed 20\n/editjob 5 title New Title")

async def deletejob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admin can do this.")
        return
    try:
        job_id = int(context.args[0])
        for j in JOBS:
            if j["id"] == job_id:
                JOBS.remove(j)
                await update.message.reply_text(f"✅ Deleted job {job_id}: {j['title']}")
                return
        await update.message.reply_text("Job not found.")
    except Exception:
        await update.message.reply_text("Usage: /deletejob 5")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "jobs":
        await q.message.reply_text(jobs_text())
    elif q.data == "profile":
        await profile_command(update, context)
    elif q.data == "balance":
        await balance_command(update, context)
    elif q.data == "referral":
        await referral_command(update, context)
    elif q.data == "tasks":
        await tasks_command(update, context)
    elif q.data == "withdraw":
        await withdraw_command(update, context)
    elif q.data == "support":
        await support_command(update, context)

def build_app():
    from telegram.ext import CallbackQueryHandler
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("jobs", jobs_command))
    app.add_handler(CommandHandler("myjobs", myjobs_command))
    app.add_handler(CommandHandler("apply", apply_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("tasks", tasks_command))
    app.add_handler(CommandHandler("claim", claim_command))
    app.add_handler(CommandHandler("referral", referral_command))
    app.add_handler(CommandHandler("withdraw", withdraw_command))
    app.add_handler(CommandHandler("support", support_command))
    app.add_handler(CommandHandler("editjob", editjob_command))
    app.add_handler(CommandHandler("deletejob", deletejob_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("addjob", addjob_command)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addjob_title)],
            PAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, addjob_pay)],
            NEEDED: [MessageHandler(filters.TEXT & ~filters.COMMAND, addjob_needed)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    ))
    return app

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: BOT_TOKEN not set!")
    else:
        print("1840 Bot Running...")
        build_app().run_polling()
