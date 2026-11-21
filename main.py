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
NEXT_SHORT_ID = [101]

def is_admin(uid):
    return uid in ADMIN_IDS

def get_job(jid):
    for j in JOBS:
        if j["id"] == jid:
            return j
    return None

def get_user_by_short(short_id):
    for tg_id, u in USERS.items():
        if u.get("short_id") == short_id:
            return tg_id, u
    return None, None

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Jobs", callback_data="menu_jobs"), InlineKeyboardButton("Profile", callback_data="menu_profile")],
        [InlineKeyboardButton("My Job", callback_data="menu_myjobs"), InlineKeyboardButton("Message Admin", callback_data="menu_message")],
    ])

# ---------- REGISTRATION ----------
REG_NAME, REG_LOC, REG_EMAIL = range(3)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in USERS and USERS[uid].get("name"):
        u = USERS[uid]
        await update.message.reply_text(
            f"Welcome back {u['name']} to 1840 & Company!\n\n"
            f"Your ID: {u['short_id']}\n\n"
            "Commands:\n"
            "/jobs - See jobs\n"
            "/apply - Apply for a job\n"
            "/myjob - My job\n"
            "/profile - My profile\n"
            "/message - Message admin",
            reply_markup=main_menu()
        )
        return ConversationHandler.END
    await update.message.reply_text("Welcome to 1840 & Company!\n\nWhat is your full name?")
    return REG_NAME

async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text.strip()
    await update.message.reply_text("Thanks! What is your location?")
    return REG_LOC

async def reg_loc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_loc"] = update.message.text.strip()
    await update.message.reply_text("What is your email address?")
    return REG_EMAIL

async def reg_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if "@" not in email or "." not in email:
        await update.message.reply_text("That email no look correct. Send valid email.")
        return REG_EMAIL
    uid = update.effective_user.id
    short_id = NEXT_SHORT_ID[0]
    NEXT_SHORT_ID[0] += 1
    USERS[uid] = {"short_id": short_id, "name": context.user_data["reg_name"], "location": context.user_data["reg_loc"], "email": email, "username": update.effective_user.username or "", "my_jobs": []}
    await update.message.reply_text(
        f"Registration complete!\n\nYour ID: {short_id}\nName: {USERS[uid]['name']}\nLocation: {USERS[uid]['location']}\nEmail: {email}\n\nNow use /jobs to see jobs and tap Apply.",
        reply_markup=main_menu()
    )
    for aid in ADMIN_IDS:
        try:
            await context.bot.send_message(aid, f"New User Registered\n\nID: {short_id}\nName: {USERS[uid]['name']}\nLocation: {USERS[uid]['location']}\nEmail: {email}\nUsername: @{USERS[uid]['username']}")
        except Exception:
            pass
    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. Send /start to try again.")
    return ConversationHandler.END

# ---------- PROFILE / MYJOB / SUPPORT ----------
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in USERS:
        await update.message.reply_text("You never register yet. Send /start to register.")
        return
    u = USERS[uid]
    await update.message.reply_text(f"My Profile\n\nID: {u['short_id']}\nName: {u['name']}\nLocation: {u['location']}\nEmail: {u['email']}\nUsername: @{u['username']}\nJobs: {len(u['my_jobs'])}")

async def myjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in USERS:
        await update.message.reply_text("Send /start to register first.")
        return
    if not USERS[uid]["my_jobs"]:
        await update.message.reply_text("You never get any job yet.\nUse /jobs and tap Apply.")
        return
    lines = ["My Job:\n"]
    for jid in USERS[uid]["my_jobs"]:
        j = get_job(jid)
        if j:
            lines.append(f"{j['id']}. {j['title']} - {j['pay']}")
    await update.message.reply_text("\n".join(lines))

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Support\n\nSend /message to contact admin.")

# ---------- JOBS + APPLY BY BUTTON ----------
async def jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not JOBS:
        await update.message.reply_text("No jobs available now. Check back later.")
        return
    text = "1840 & Company - Jobs Available\n\nTap Apply under any job:\n"
    kb = []
    for j in JOBS:
        left = j["needed"] - j["joined"]
        status = "Full" if left <= 0 else "Hiring"
        text += f"\n{j['id']}. {j['title']} - {j['pay']}\nNeeded: {j['needed']} | Joined: {j['joined']} | Left: {max(0, left)} | {status}\n"
        if left > 0:
            kb.append([InlineKeyboardButton(f"Apply - {j['title']}", callback_data=f"apply_{j['id']}")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def apply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await jobs_command(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data
    if data == "menu_jobs":
        await q.message.reply_text("Send /jobs to see jobs with Apply buttons.")
        return
    if data == "menu_profile":
        if uid not in USERS:
            await q.message.reply_text("Send /start to register first.")
            return
        u = USERS[uid]
        await q.message.reply_text(f"My Profile\n\nID: {u['short_id']}\nName: {u['name']}\nLocation: {u['location']}\nEmail: {u['email']}")
        return
    if data == "menu_myjobs":
        if uid not in USERS or not USERS[uid]["my_jobs"]:
            await q.message.reply_text("You never get any job yet. Use /jobs and tap Apply.")
            return
        lines = ["My Job:\n"]
        for jid in USERS[uid]["my_jobs"]:
            j = get_job(jid)
            if j:
                lines.append(f"{j['id']}. {j['title']} - {j['pay']}")
        await q.message.reply_text("\n".join(lines))
        return
    if data == "menu_message":
        await q.message.reply_text("Send your message here, or use /message. You fit send text, photo or file.")
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
            await q.message.reply_text("Sorry, this job is Full.")
            return
        j["joined"] += 1
        USERS[uid]["my_jobs"].append(jid)
        await q.message.reply_text(f"You applied for {j['title']} - {j['pay']}\nCheck /myjob to see am. Admin will contact you.")
        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(aid, f"New Application\n\nID: {USERS[uid]['short_id']}\nName: {USERS[uid]['name']} applied for {j['title']}\nLocation: {USERS[uid]['location']}\nEmail: {USERS[uid]['email']}")
            except Exception:
                pass

# ---------- ADMIN: SEE USERS ----------
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Only admin.")
        return
    if not USERS:
        await update.message.reply_text("No users yet.")
        return
    lines = ["All Registered Users:\n"]
    for tg_id, u in USERS.items():
        jobs = ", ".join([str(x) for x in u["my_jobs"]]) or "None"
        lines.append(f"ID: {u['short_id']}\nName: {u['name']}\nLocation: {u['location']}\nEmail: {u['email']}\nUsername: @{u['username']}\nJobs: {jobs}\n---")
    await update.message.reply_text("\n".join(lines))

# ---------- ADMIN: GIVE JOB TO USER ----------
async def assignjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Only admin.")
        return
    try:
        short_id = int(context.args[0]); job_id = int(context.args[1])
    except Exception:
        await update.message.reply_text("Usage:\n/assignjob 101 5\n\nGet user ID from /users")
        return
    tg_id, u = get_user_by_short(short_id)
    if not u:
        await update.message.reply_text("User not found. Check /users for correct ID.")
        return
    j = get_job(job_id)
    if not j:
        await update.message.reply_text("Job not found. Check /jobs")
        return
    if job_id in u["my_jobs"]:
        await update.message.reply_text("User already get this job.")
        return
    u["my_jobs"].append(job_id)
    j["joined"] += 1
    await update.message.reply_text(f"Gave {j['title']} to {u['name']} (ID: {short_id})")
    try:
        await context.bot.send_message(tg_id, f"Congratulations {u['name']}!\n\nYou have been given a job:\n{j['title']} - {j['pay']}\n\nCheck /myjob to see am.")
    except Exception:
        pass

# ---------- CHAT: USER <-> ADMIN ----------
async def message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Send your message like this:\n/message I need help with my job")
        return
    text = " ".join(context.args)
    uid = update.effective_user.id
    name = USERS.get(uid, {}).get("name", update.effective_user.first_name)
    short_id = USERS.get(uid, {}).get("short_id", "No ID - send /start")
    for aid in ADMIN_IDS:
        try:
            await context.bot.send_message(aid, f"Message from {name}\nID: {short_id}\n\n{text}\n\nReply with:\n/reply {short_id} your reply")
        except Exception:
            pass
    await update.message.reply_text("Message sent to admin. Admin will reply you soon.")

async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Only admin.")
        return
    try:
        short_id = int(context.args[0]); text = " ".join(context.args[1:])
        if not text:
            await update.message.reply_text("Usage: /reply 101 Hello")
            return
        tg_id, u = get_user_by_short(short_id)
        if not u:
            await update.message.reply_text("User not found. Check /users")
            return
        await context.bot.send_message(tg_id, f"Reply from Admin:\n\n{text}")
        await update.message.reply_text(f"Sent to {u['name']} (ID: {short_id})")
    except Exception:
        await update.message.reply_text("Usage: /reply 101 Hello")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    uid = update.effective_user.id
    # Admin sending photo/file with caption /reply 101 ...
    if is_admin(uid):
        caption = (msg.caption or "") if msg.caption else ""
        if caption.startswith("/reply"):
            try:
                parts = caption.split(None, 2)
                short_id = int(parts[1]); text = parts[2] if len(parts) > 2 else ""
                tg_id, u = get_user_by_short(short_id)
                if tg_id:
                    if text:
                        await context.bot.send_message(tg_id, f"Reply from Admin:\n\n{text}")
                    if msg.photo:
                        await context.bot.send_photo(tg_id, msg.photo[-1].file_id, caption=text if text else None)
                    elif msg.document:
                        await context.bot.send_document(tg_id, msg.document.file_id, caption=text if text else None)
                    await msg.reply_text(f"Sent to {u['name']} (ID: {short_id})")
                    return
            except Exception:
                pass
        await msg.reply_text("To reply a user, use:\n/reply 101 your message\n\nGet ID from /users")
        return
    # Normal user: forward text, photo, file to admin
    name = USERS.get(uid, {}).get("name", update.effective_user.first_name)
    short_id = USERS.get(uid, {}).get("short_id", "No ID")
    header = f"New Message from {name}\nID: {short_id}\n\nReply with:\n/reply {short_id} your reply"
    for aid in ADMIN_IDS:
        try:
            await context.bot.send_message(aid, header)
            await msg.forward(aid)
        except Exception:
            pass
    await msg.reply_text("Sent to admin. Admin will reply you soon.")

# ----------
