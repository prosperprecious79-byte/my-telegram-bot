import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN") or os.getenv("TOKEN")

# CHANGE THIS
ADMIN_IDS = [9054441429]

JOBS = [
    {"id": 1, "title": "Virtual Assistant", "pay": "$400-$600/mo", "needed": 15, "joined": 3},
    {"id": 2, "title": "Customer Support Rep", "pay": "$500/mo", "needed": 20, "joined": 8},
    {"id": 3, "title": "Social Media Manager", "pay": "$600/mo", "needed": 8, "joined": 5},
    {"id": 4, "title": "Data Entry Specialist", "pay": "$350/mo", "needed": 10, "joined": 8},
    {"id": 5, "title": "Script Writing", "pay": "$450-$700/mo", "needed": 12, "joined": 0},
    {"id": 6, "title": "Video Editor", "pay": "$500-$800/mo", "needed": 10, "joined": 0},
    {"id": 7, "title": "Graphic Designer", "pay": "$450-$750/mo", "needed": 8, "joined": 0},
    {"id": 8, "title": "Content Writer", "pay": "$400-$650/mo", "needed": 12, "joined": 0},
    {"id": 9, "title": "Transcriptionist", "pay": "$300-$500/mo", "needed": 15, "joined": 0},
]

USERS = {}
# USERS[user_id] = {"name": "", "location": "", "email": "", "my_jobs": []}

def is_admin(uid):
    return uid in ADMIN_IDS

def get_job(jid):
    for j in JOBS:
        if j["id"] == jid:
            return j
    return None

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💼 Jobs", callback_data="menu_jobs"), InlineKeyboardButton("👤 Profile", callback_data="menu_profile")],
        [InlineKeyboardButton("📋 My Job", callback_data="menu_myjobs")],
    ])

# ---------- REGISTRATION: /start -> Name -> Location -> Email ----------
REG_NAME, REG_LOC, REG_EMAIL = range(3)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in USERS and USERS[uid].get("name"):
        u = USERS[uid]
        await update.message.reply_text(
            f"👋 Welcome back {u['name']} to 1840 & Company!\n\n"
            "💼 Find freelancing jobs here.\n\n"
            "Commands:\n"
            "/jobs - See jobs\n"
            "/apply - Apply for a job\n"
            "/myjob - My job\n"
            "/profile - My profile\n"
            "/support - Contact support",
            reply_markup=main_menu()
        )
        return ConversationHandler.END
    await update.message.reply_text("👋 Welcome to 1840 & Company!\n\nTo get started, what is your full name?")
    return REG_NAME

async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text.strip()
    await update.message.reply_text("Thanks! What is your location?\nExample: Lagos, Nigeria")
    return REG_LOC

async def reg_loc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_loc"] = update.message.text.strip()
    await update.message.reply_text("Last one, what is your email address?")
    return REG_EMAIL

async def reg_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if "@" not in email or "." not in email:
        await update.message.reply_text("That email no look correct. Send valid email, e.g: name@gmail.com")
        return REG_EMAIL
    uid = update.effective_user.id
    USERS[uid] = {
        "name": context.user_data["reg_name"],
        "location": context.user_data["reg_loc"],
        "email": email,
        "username": update.effective_user.username or "",
        "my_jobs": []
    }
    await update.message.reply_text(
        f"✅ Registration complete!\n\n"
        f"Name: {USERS[uid]['name']}\nLocation: {USERS[uid]['location']}\nEmail: {USERS[uid]['email']}\n\n"
        "Now use /jobs to see jobs and tap Apply.",
        reply_markup=main_menu()
    )
    # Notify admin
    for aid in ADMIN_IDS:
        try:
            await context.bot.send_message(aid, f"🆕 New User Registered\n\nName: {USERS[uid]['name']}\nLocation: {USERS[uid]['location']}\nEmail: {email}\nUsername: @{USERS[uid]['username']}\nID: {uid}")
        except Exception:
            pass
    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. Send /start to try again.")
    return ConversationHandler.END

# ---------- PROFILE / MYJOB ----------
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in USERS:
        await update.message.reply_text("You never register yet. Send /start to register.")
        return
    u = USERS[uid]
    await update.message.reply_text(
        f"👤 My Profile\n\nName: {u['name']}\nLocation: {u['location']}\nEmail: {u['email']}\nUsername: @{u['username']}\nID: {uid}\nJobs: {len(u['my_jobs'])}"
    )

async def myjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in USERS:
        await update.message.reply_text("Send /start to register first.")
        return
    if not USERS[uid]["my_jobs"]:
        await update.message.reply_text("You never get any job yet.\nUse /jobs and tap Apply.")
        return
    lines = ["📋 My Job:\n"]
    for jid in USERS[uid]["my_jobs"]:
        j = get_job(jid)
        if j:
            lines.append(f"{j['id']}. {j['title']} - {j['pay']}")
    await update.message.reply_text("\n".join(lines))

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🆘 Support\n\nMessage admin: @1840support")

# ---------- JOBS + APPLY BY BUTTON ----------
async def jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not JOBS:
        await update.message.reply_text("No jobs available now. Check back later.")
        return
    text = "💼 1840 & Company - Jobs Available\n\nTap Apply under any job:\n"
    kb = []
    for j in JOBS:
        left = j["needed"] - j["joined"]
        status = "🔴 Full" if left <= 0 else "🟢 Hiring"
        text += f"\n{j['id']}. {j['title']} - {j['pay']}\nNeeded: {j['needed']} | Joined: {j['joined']} | Left: {max(0, left)} | {status}\n"
        if left > 0:
            kb.append([InlineKeyboardButton(f"✅ Apply - {j['title']}", callback_data=f"apply_{j['id']}")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def apply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # No more /apply 1 - just show jobs with Apply buttons
    await jobs_command(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data
    if data == "menu_jobs":
        await jobs_command(q, context) if False else None
        # Reuse jobs text for button click
        await q.message.reply_text("Send /jobs to see jobs with Apply buttons.")
        return
    if data == "menu_profile":
        if uid not in USERS:
            await q.message.reply_text("Send /start to register first.")
            return
        u = USERS[uid]
        await q.message.reply_text(f"👤 My Profile\n\nName: {u['name']}\nLocation: {u['location']}\nEmail: {u['email']}\nID: {uid}")
        return
    if data == "menu_myjobs":
        if uid not in USERS or not USERS[uid]["my_jobs"]:
            await q.message.reply_text("You never get any job yet. Use /jobs and tap Apply.")
            return
        lines = ["📋 My Job:\n"]
        for jid in USERS[uid]["my_jobs"]:
            j = get_job(jid)
            if j:
                lines.append(f"{j['id']}. {j['title']} - {j['pay']}")
        await q.message.reply_text("\n".join(lines))
        return
    if data.startswith("apply_"):
        if uid not in USERS:
            await q.message.reply_text("Send /start to register first before you apply.")
            return
        jid = int(data.replace("apply_", ""))
        j = get_job(jid)
        if not j:
            await q.message.reply_text("Job not found.")
            return
        if jid in USERS[uid]["my_jobs"]:
            await q.message.reply_text("You already applied for this job.")
            return
        if j["joined"] >= j["needed"]:
            await q.message.reply_text("❌ Sorry, this job is Full.")
            return
        j["joined"] += 1
        USERS[uid]["my_jobs"].append(jid)
        await q.message.reply_text(f"✅ You applied for {j['title']} - {j['pay']}\nCheck /myjob to see am. Admin will contact you.")
        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(aid, f"📥 New Application\n\n{USERS[uid]['name']} applied for {j['title']}\nLocation: {USERS[uid]['location']}\nEmail: {USERS[uid]['email']}\nID: {uid}")
            except Exception:
                pass

# ---------- ADMIN: SEE USERS ----------
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admin.")
        return
    if not USERS:
        await update.message.reply_text("No users yet.")
        return
    lines = ["👥 All Registered Users:\n"]
    for uid, u in USERS.items():
        jobs = ", ".join([str(x) for x in u["my_jobs"]]) or "None"
        lines.append(f"ID: {uid}\nName: {u['name']}\nLocation: {u['location']}\nEmail: {u['email']}\nUsername: @{u['username']}\nJobs: {jobs}\n---")
    await update.message.reply_text("\n".join(lines))

# ---------- ADMIN: GIVE JOB TO USER ----------
async def assignjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admin.")
        return
    try:
        user_id = int(context.args[0])
        job_id = int(context.args[1])
    except Exception:
        await update.message.reply_text("Usage:\n/assignjob <user_id> <job_id>\nExample: /assignjob 123456789 5\n\nGet user ID from /users")
        return
    if user_id not in USERS:
        await update.message.reply_text("User not found. Check /users for correct ID.")
        return
    j = get_job(job_id)
    if not j:
        await update.message.reply_text("Job not found. Check /jobs")
        return
    if job_id in USERS[user_id]["my_jobs"]:
        await update.message.reply_text("User already get this job.")
        return
    USERS[user_id]["my_jobs"].append(job_id)
    j["joined"] += 1
    await update.message.reply_text(f"✅ Gave {j['title']} to {USERS[user_id]['name']} (ID: {user_id})")
    try:
        await context.bot.send_message(user_id, f"🎉 Congratulations {USERS[user_id]['name']}!\n\nYou have been given a job:\n{j['title']} - {j['pay']}\n\nCheck /myjob to see am.")
    except Exception:
        pass

# ---------- ADMIN: ADD / EDIT / DELETE JOB ----------
ADD_TITLE, ADD_PAY, ADD_NEEDED = range(3, 6)

async def addjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admin.")
        return ConversationHandler.END
    await update.message.reply_text("What is the job title?\nExample: Script Writing")
    return ADD_TITLE

async def addjob_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_title"] = update.message.text
    await update.message.reply_text("What is the pay?\nExample: $500/mo")
    return ADD_PAY

async def addjob_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_pay"] = update.message.text
    await update.message.reply_text("How many workers needed?\nExample: 10")
    return ADD_NEEDED

async def addjob_needed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        needed = int(update.message.text)
    except Exception:
        await update.message.reply_text("Send number only, e.g: 10")
        return ADD_NEEDED
    new_id = max([j["id"] for j in JOBS], default=0) + 1
    JOBS.append({"id": new_id, "title": context.user_data["new_title"], "pay": context.user_data["new_pay"], "needed": needed, "joined": 0})
    await update.message.reply_text(f"✅ Job added:\n{new_id}. {context.user_data['new_title']} - {context.user_data['new_pay']}")
    return ConversationHandler.END

async def editjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admin.")
        return
    try:
        job_id = int(context.args[0]); field = context.args[1].lower(); value = " ".join(context.args[2:])
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
        await update.message.reply_text("❌ Only admin.")
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

def build_app():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("jobs", jobs_command))
    app.add_handler(CommandHandler("apply", apply_command))
    app.add_handler(CommandHandler("myjob", myjob_command))
    app.add_handler(CommandHandler("myjobs", myjob_command))
    app.add_handler(CommandHandler("support", support_command))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("assignjob", assignjob_command))
    app.add_handler(CommandHandler("editjob", editjob_command))
    app.add_handler(CommandHandler("deletejob", deletejob_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    # Registration conversation
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)], REG_LOC: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_loc)], REG_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_email)]},
        fallbacks=[CommandHandler("cancel", cancel_command)],
    ))
    # Add job conversation
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("addjob", addjob_command)],
        states={ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addjob_title)], ADD_PAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, addjob_pay)], ADD_NEEDED: [MessageHandler(filters.TEXT & ~filters.COMMAND, addjob_needed)]},
        fallbacks=[CommandHandler("cancel", cancel_command)],
    ))
    return app

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: BOT_TOKEN not set!")
    else:
        print("1840 Bot Running...")
        build_app().run_polling()
