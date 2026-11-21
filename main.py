import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = (os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN") or os.getenv("TOKEN") or "").strip().strip('"').strip("'")

# CHANGE THIS
ADMIN_IDS = [9054441429]

DATA_FILE = "users.json"

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

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            users = {int(k): v for k, v in data.get("users", {}).items()}
            for u in users.values():
                if "warnings" not in u: u["warnings"] = []
            jobs = data.get("jobs", JOBS)
            return users, jobs, [data.get("next_id", 101)], set(data.get("banned", []))
    except Exception:
        return {}, JOBS, [101], set()

def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump({"users": USERS, "jobs": JOBS, "next_id": NEXT_SHORT_ID[0], "banned": list(BANNED)}, f)
    except Exception:
        pass

USERS, JOBS, NEXT_SHORT_ID, BANNED = load_data()

def is_admin(uid): return uid in ADMIN_IDS
def is_banned(uid): return uid in BANNED
def get_job(jid):
    for j in JOBS:
        if j["id"] == jid: return j
    return None
def get_user_by_short(short_id):
    for tg_id, u in USERS.items():
        if u.get("short_id") == short_id: return tg_id, u
    return None, None
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Jobs", callback_data="menu_jobs"), InlineKeyboardButton("Profile", callback_data="menu_profile")],
        [InlineKeyboardButton("My Job", callback_data="menu_myjobs"), InlineKeyboardButton("Message Admin", callback_data="menu_message")],
    ])

# ---------- HELP / FAQ / STATUS ----------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        await update.message.reply_text("Admin Help - 30 Admin Commands\n\n/users\n/userinfo 101\n/search Dan\n/assignjob 101 5\n/removejob 101 5\n/ban 101\n/unban 101\n/unbanall\n/deleteuser 101\n/stats\n/jobstats\n/broadcast Hello\n/export\n/backup\n/addjob\n/editjob 5 pay $600/mo\n/deletejob 5\n/setpay 5 $600/mo\n/settitle 5 New Title\n/setneeded 5 20\n/resetjobs\n/warn 101 Reason\n/warnings 101\n/clearwarnings 101\n/notify 101 Hello\n/reply 101 Hello\n/topusers\n/recent\n/bylocation\n/listadmins\n\nUser: /start /jobs /apply /myjob /profile /message /help /faq /status")
    else:
        await update.message.reply_text("Help - 1840 & Company\n\n/start - Register\n/jobs - View jobs\n/apply - Apply\n/myjob - My job\n/profile - My profile\n/message - Message admin\n/faq - FAQ\n/status - Status\n\nTo apply: Send /jobs, then tap Apply.")

async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Frequently Asked Questions\n\n1. How do I register?\nSend /start and follow the steps: Name, Location, Email.\n\n2. How do I get my ID?\nSend /profile.\n\n3. How do I apply?\nSend /jobs and tap Apply.\n\n4. How do I check my job?\nSend /myjob.\n\n5. How do I contact admin?\nSend /message followed by your message, or just send text, photo or file.\n\n6. When will I be paid?\nPayment details are confirmed by admin after assignment.\n\n7. I forgot my ID?\nSend /profile.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_admin(uid):
        total = sum(len(u.get("my_jobs", [])) for u in USERS.values())
        await update.message.reply_text(f"Bot Status - Admin\n\nBot: Online\nTotal Users: {len(USERS)}\nTotal Jobs: {len(JOBS)}\nTotal Applications: {total}\nBanned: {len(BANNED)}\nNext ID: {NEXT_SHORT_ID[0]}")
        return
    if uid not in USERS:
        await update.message.reply_text("You have not registered yet. Please send /start.")
        return
    u = USERS[uid]
    await update.message.reply_text(f"Your Status\n\nID: {u['short_id']}\nName: {u['name']}\nLocation: {u['location']}\nEmail: {u['email']}\nJobs: {len(u['my_jobs'])}\nWarnings: {len(u.get('warnings', []))}\nStatus: Active")

# ---------- REGISTRATION ----------
REG_NAME, REG_LOC, REG_EMAIL = range(3)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_banned(uid):
        await update.message.reply_text("Your account has been restricted. Please contact admin.")
        return ConversationHandler.END
    if uid in USERS and USERS[uid].get("name"):
        u = USERS[uid]
        await update.message.reply_text(f"Welcome back {u['name']} to 1840 & Company!\n\nYour ID: {u['short_id']}\n\n/jobs - View jobs\n/apply - Apply\n/myjob - My job\n/profile - Profile\n/message - Message admin\n/help - Help\n/faq - FAQ\n/status - Status", reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text("Welcome to 1840 & Company!\n\nWhat is your full name?")
    return REG_NAME
async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text.strip()
    await update.message.reply_text("Thank you. What is your location?")
    return REG_LOC
async def reg_loc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_loc"] = update.message.text.strip()
    await update.message.reply_text("What is your email address?")
    return REG_EMAIL
async def reg_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if "@" not in email or "." not in email:
        await update.message.reply_text("That email address appears to be invalid. Please send a valid email address.")
        return REG_EMAIL
    uid = update.effective_user.id
    short_id = NEXT_SHORT_ID[0]; NEXT_SHORT_ID[0] += 1
    USERS[uid] = {"short_id": short_id, "name": context.user_data["reg_name"], "location": context.user_data["reg_loc"], "email": email, "username": update.effective_user.username or "", "my_jobs": [], "warnings": []}
    save_data()
    await update.message.reply_text(f"Registration complete!\n\nYour ID: {short_id}\nName: {USERS[uid]['name']}\nLocation: {USERS[uid]['location']}\nEmail: {email}\n\nPlease use /jobs to view jobs and tap Apply.", reply_markup=main_menu())
    for aid in ADMIN_IDS:
        try: await context.bot.send_message(aid, f"New User Registered\n\nID: {short_id}\nName: {USERS[uid]['name']}\nLocation: {USERS[uid]['location']}\nEmail: {email}\nUsername: @{USERS[uid]['username']}")
        except Exception: pass
    return ConversationHandler.END
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. Please send /start to try again.")
    return ConversationHandler.END

# ---------- USER COMMANDS ----------
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in USERS:
        await update.message.reply_text("You have not registered yet. Please send /start.")
        return
    u = USERS[uid]
    await update.message.reply_text(f"My Profile\n\nID: {u['short_id']}\nName: {u['name']}\nLocation: {u['location']}\nEmail: {u['email']}\nUsername: @{u['username']}\nJobs: {len(u['my_jobs'])}")
async def myjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in USERS:
        await update.message.reply_text("Please send /start to register first.")
        return
    if not USERS[uid]["my_jobs"]:
        await update.message.reply_text("You have not received any job yet.\nPlease use /jobs and tap Apply.")
        return
    lines = ["My Job:\n"]
    for jid in USERS[uid]["my_jobs"]:
        j = get_job(jid)
        if j: lines.append(f"{j['id']}. {j['title']} - {j['pay']}")
    await update.message.reply_text("\n".join(lines))
async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Support\n\nPlease send /message to contact admin.")
async def jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not JOBS:
        await update.message.reply_text("No jobs are available at the moment. Please check back later.")
        return
    text = "1840 & Company - Jobs Available\n\nPlease tap Apply under any job:\n"
    kb = []
    for j in JOBS:
        left = j["needed"] - j["joined"]
        status = "Full" if left <= 0 else "Hiring"
        text += f"\n{j['id']}. {j['title']} - {j['pay']}\nNeeded: {j['needed']} | Joined: {j['joined']} | Left: {max(0, left)} | {status}\n"
        if left > 0: kb.append([InlineKeyboardButton(f"Apply - {j['title']}", callback_data=f"apply_{j['id']}")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
async def apply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await jobs_command(update, context)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; data = q.data
    if is_banned(uid):
        await q.message.reply_text("Your account has been restricted. Please contact admin.")
        return
    if data == "menu_jobs":
        await q.message.reply_text("Please send /jobs to view jobs.")
        return
    if data == "menu_profile":
        if uid not in USERS:
            await q.message.reply_text("Please send /start first.")
            return
        u = USERS[uid]
        await q.message.reply_text(f"My Profile\n\nID: {u['short_id']}\nName: {u['name']}\nLocation: {u['location']}\nEmail: {u['email']}")
        return
    if data == "menu_myjobs":
        if uid not in USERS or not USERS[uid]["my_jobs"]:
            await q.message.reply_text("You have not received any job yet.")
            return
        lines = ["My Job:\n"]
        for jid in USERS[uid]["my_jobs"]:
            j = get_job(jid)
            if j: lines.append(f"{j['id']}. {j['title']} - {j['pay']}")
        await q.message.reply_text("\n".join(lines))
        return
    if data == "menu_message":
        await q.message.reply_text("Please send your message here, or use /message. You can send text, photos or files.")
        return
    if data.startswith("apply_"):
        if uid not in USERS:
            await q.message.reply_text("Please send /start first before you apply.")
            return
        jid = int(data.replace("apply_", "")); j = get_job(jid)
        if not j:
            await q.message.reply_text("Job not found.")
            return
        if jid in USERS[uid]["my_jobs"]:
            await q.message.reply_text("You have already applied for this job.")
            return
        if j["joined"] >= j["needed"]:
            await q.message.reply_text("Sorry, this job is Full.")
            return
        j["joined"] += 1; USERS[uid]["my_jobs"].append(jid); save_data()
        await q.message.reply_text(f"You have applied for {j['title']} - {j['pay']}\nPlease check /myjob. Admin will contact you.")
        for aid in ADMIN_IDS:
            try: await context.bot.send_message(aid, f"New Application\n\nID: {USERS[uid]['short_id']}\nName: {USERS[uid]['name']} applied for {j['title']}\nLocation: {USERS[uid]['location']}\nEmail: {USERS[uid]['email']}")
            except Exception: pass

# ---------- ADMIN 1-10 ----------
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    if not USERS:
        await update.message.reply_text("No users yet."); return
    lines = ["All Registered Users:\n"]
    for tg_id, u in USERS.items():
        jobs = ", ".join([str(x) for x in u["my_jobs"]]) or "None"
        status = "Banned" if tg_id in BANNED else "Active"
        lines.append(f"ID: {u['short_id']}\nName: {u['name']}\nLocation: {u['location']}\nEmail: {u['email']}\nUsername: @{u['username']}\nJobs: {jobs}\nStatus: {status}\n---")
    await update.message.reply_text("\n".join(lines))
async def userinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try: short_id = int(context.args[0])
    except Exception:
        await update.message.reply_text("Usage: /userinfo 101"); return
    tg_id, u = get_user_by_short(short_id)
    if not u:
        await update.message.reply_text("User not found."); return
    jobs_text = "\n".join([f"- {get_job(jid)['title']} ({get_job(jid)['pay']})" if get_job(jid) else f"- Job {jid}" for jid in u["my_jobs"]]) or "None"
    await update.message.reply_text(f"User Details\n\nID: {u['short_id']}\nName: {u['name']}\nLocation: {u['location']}\nEmail: {u['email']}\nUsername: @{u['username']}\nTelegram ID: {tg_id}\nStatus: {'Banned' if tg_id in BANNED else 'Active'}\nWarnings: {len(u.get('warnings', []))}\nJobs:\n{jobs_text}")
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    if not context.args:
        await update.message.reply_text("Usage: /search Dan"); return
    query = " ".join(context.args).lower()
    found = []
    for tg_id, u in USERS.items():
        if query in u["name"].lower() or query in u["email"].lower() or query in u["location"].lower() or query in str(u["short_id"]):
            found.append(f"ID: {u['short_id']} | {u['name']} | {u['location']} | {u['email']}")
    if not found:
        await update.message.reply_text("No user found."); return
    await update.message.reply_text("Search Results:\n\n" + "\n".join(found))
async def assignjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try: short_id = int(context.args[0]); job_id = int(context.args[1])
    except Exception:
        await update.message.reply_text("Usage: /assignjob 101 5"); return
    tg_id, u = get_user_by_short(short_id)
    if not u:
        await update.message.reply_text("User not found."); return
    j = get_job(job_id)
    if not j:
        await update.message.reply_text("Job not found."); return
    if job_id in u["my_jobs"]:
        await update.message.reply_text("This user already has this job."); return
    u["my_jobs"].append(job_id); j["joined"] += 1; save_data()
    await update.message.reply_text(f"Assigned {j['title']} to {u['name']} (ID: {short_id})")
    try: await context.bot.send_message(tg_id, f"Congratulations {u['name']}!\n\nYou have been assigned a job:\n{j['title']} - {j['pay']}\n\nPlease check /myjob.")
    except Exception: pass
async def removejob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try: short_id = int(context.args[0]); job_id = int(context.args[1])
    except Exception:
        await update.message.reply_text("Usage: /removejob 101 5"); return
    tg_id, u = get_user_by_short(short_id)
    if not u:
        await update.message.reply_text("User not found."); return
    if job_id not in u["my_jobs"]:
        await update.message.reply_text("This user does not have this job."); return
    u["my_jobs"].remove(job_id)
    j = get_job(job_id)
    if j and j["joined"] > 0: j["joined"] -= 1
    save_data()
    await update.message.reply_text(f"Removed job {job_id} from {u['name']} (ID: {short_id})")
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try: short_id = int(context.args[0])
    except Exception:
        await update.message.reply_text("Usage: /ban 101"); return
    tg_id, u = get_user_by_short(short_id)
    if not u:
        await update.message.reply_text("User not found."); return
    BANNED.add(tg_id); save_data()
    await update.message.reply_text(f"Banned {u['name']} (ID: {short_id})")
    try: await context.bot.send_message(tg_id, "Your account has been restricted. Please contact admin.")
    except Exception: pass
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try: short_id = int(context.args[0])
    except Exception:
        await update.message.reply_text("Usage: /unban 101"); return
    tg_id, u = get_user_by_short(short_id)
    if not u:
        await update.message.reply_text("User not found."); return
    BANNED.discard(tg_id); save_data()
    await update.message.reply_text(f"Unbanned {u['name']} (ID: {short_id})")
async def unbanall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    count = len(BANNED); BANNED.clear(); save_data()
    await update.message.reply_text(f"Unbanned all users. Total unbanned: {count}")
async def deleteuser_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try: short_id = int(context.args[0])
    except Exception:
        await update.message.reply_text("Usage: /deleteuser 101"); return
    tg_id, u = get_user_by_short(short_id)
    if not u:
        await update.message.reply_text("User not found."); return
    for jid in u["my_jobs"]:
        j = get_job(jid)
        if j and j["joined"] > 0: j["joined"] -= 1
    del USERS[tg_id]; BANNED.discard(tg_id); save_data()
    await update.message.reply_text(f"Deleted user {u['name']} (ID: {short_id})")
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    total = sum(len(u.get("my_jobs", [])) for u in USERS.values())
    await update.message.reply_text(f"Statistics\n\nTotal Users: {len(USERS)}\nTotal Jobs: {len(JOBS)}\nTotal Applications: {total}\nBanned: {len(BANNED)}\nNext ID: {NEXT_SHORT_ID[0]}")

# ---------- ADMIN 11-20 ----------
async def jobstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    lines = ["Job Statistics:\n"]
    for j in JOBS:
        lines.append(f"{j['id']}. {j['title']}\nNeeded: {j['needed']} | Joined: {j['joined']} | Left: {max(0, j['needed']-j['joined'])}\n---")
    await update.message.reply_text("\n".join(lines))
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast Hello everyone"); return
    text = " ".join(context.args); sent = 0; failed = 0
    for tg_id in list(USERS.keys()):
        if tg_id in BANNED: continue
        try:
            await context.bot.send_message(tg_id, f"Announcement from 1840 & Company:\n\n{text}"); sent += 1
        except Exception: failed += 1
    await update.message.reply_text(f"Broadcast complete.\nSent: {sent}\nFailed: {failed}")
async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    if not USERS:
        await update.message.reply_text("No users to export."); return
    lines = ["ID,Name,Location,Email,Username,Jobs,Status"]
    for tg_id, u in USERS.items():
        jobs = ";".join([str(x) for x in u["my_jobs"]])
        status = "Banned" if tg_id in BANNED else "Active"
        lines.append(f"{u['short_id']},{u['name']},{u['location']},{u['email']},@{u['username']},{jobs},{status}")
    with open("export_users.txt", "w") as f: f.write("\n".join(lines))
    await update.message.reply_document(update.effective_chat.id, open("export_users.txt", "rb"), caption=f"Exported {len(USERS)} users.")
async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    save_data()
    try:
        await update.message.reply_document(update.effective_chat.id, open(DATA_FILE, "rb"), caption="Backup - users.json")
    except Exception:
        await update.message.reply_text("No backup file found yet.")
async def setpay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try:
        job_id = int(context.args[0]); value = " ".join(context.args[1:])
        j = get_job(job_id)
        if not j:
            await update.message.reply_text("Job not found."); return
        j["pay"] = value; save_data()
        await update.message.reply_text(f"Updated pay for {j['title']} to {value}")
    except Exception:
        await update.message.reply_text("Usage: /setpay 5 $600/mo")
async def settitle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try:
        job_id = int(context.args[0]); value = " ".join(context.args[1:])
        j = get_job(job_id)
        if not j:
            await update.message.reply_text("Job not found."); return
        j["title"] = value; save_data()
        await update.message.reply_text(f"Updated title for job {job_id} to {value}")
    except Exception:
        await update.message.reply_text("Usage: /settitle 5 New Title")
async def setneeded_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try:
        job_id = int(context.args[0]); value = int(context.args[1])
        j = get_job(job_id)
        if not j:
            await update.message.reply_text("Job not found."); return
        j["needed"] = value; save_data()
        await update.message.reply_text(f"Updated needed for {j['title']} to {value}")
    except Exception:
        await update.message.reply_text("Usage: /setneeded 5 20")
async def resetjobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    for j in JOBS: j["joined"] = 0
    save_data()
    await update.message.reply_text("All job Joined counts have been reset to 0. User assignments were not removed. Use /removejob to remove assignments.")

# ---------- ADMIN 21-30 ----------
async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try:
        short_id = int(context.args[0]); reason = " ".join(context.args[1:]) or "No reason given"
        tg_id, u = get_user_by_short(short_id)
        if not u:
            await update.message.reply_text("User not found."); return
        u.setdefault("warnings", []).append(reason); save_data()
        await update.message.reply_text(f"Warned {u['name']} (ID: {short_id})\nReason: {reason}\nTotal warnings: {len(u['warnings'])}")
        try: await context.bot.send_message(tg_id, f"Warning from Admin:\n\n{reason}\n\nTotal warnings: {len(u['warnings'])}")
        except Exception: pass
    except Exception:
        await update.message.reply_text("Usage: /warn 101 Reason")
async def warnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try: short_id = int(context.args[0])
    except Exception:
        await update.message.reply_text("Usage: /warnings 101"); return
    tg_id, u = get_user_by_short(short_id)
    if not u:
        await update.message.reply_text("User not found."); return
    warns = u.get("warnings", [])
    if not warns:
        await update.message.reply_text(f"{u['name']} (ID: {short_id}) has no warnings.")
        return
    await update.message.reply_text(f"Warnings for {u['name']} (ID: {short_id}):\n\n" + "\n".join([f"{i+1}. {w}" for i, w in enumerate(warns)]))
async def clearwarnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try: short_id = int(context.args[0])
    except Exception:
        await update.message.reply_text("Usage: /clearwarnings 101"); return
    tg_id, u = get_user_by_short(short_id)
    if not u:
        await update.message.reply_text("User not found."); return
    u["warnings"] = []; save_data()
    await update.message.reply_text(f"Cleared all warnings for {u['name']} (ID: {short_id})")
async def notify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try:
        short_id = int(context.args[0]); text = " ".join(context.args[1:])
        if not text:
            await update.message.reply_text("Usage: /notify 101 Hello"); return
        tg_id, u = get_user_by_short(short_id)
        if not u:
            await update.message.reply_text("User not found."); return
        await context.bot.send_message(tg_id, f"Notification from 1840 & Company:\n\n{text}")
        await update.message.reply_text(f"Notification sent to {u['name']} (ID: {short_id})")
    except Exception:
        await update.message.reply_text("Usage: /notify 101 Hello")
async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try:
        short_id = int(context.args[0]); text = " ".join(context.args[1:])
        if not text:
            await update.message.reply_text("Usage: /reply 101 Hello"); return
        tg_id, u = get_user_by_short(short_id)
        if not u:
            await update.message.reply_text("User not found."); return
        await context.bot.send_message(tg_id, f"Reply from Admin:\n\n{text}")
        await update.message.reply_text(f"Sent to {u['name']} (ID: {short_id})")
    except Exception:
        await update.message.reply_text("Usage: /reply 101 Hello")
async def topusers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    if not USERS:
        await update.message.reply_text("No users yet."); return
    sorted_users = sorted(USERS.values(), key=lambda x: len(x.get("my_jobs", [])), reverse=True)[:10]
    lines = ["Top Users - Most Jobs:\n"]
    for u in sorted_users:
        lines.append(f"ID: {u['short_id']} | {u['name']} | Jobs: {len(u['my_jobs'])}")
    await update.message.reply_text("\n".join(lines))
async def recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    if not USERS:
        await update.message.reply_text("No users yet."); return
    recent = sorted(USERS.values(), key=lambda x: x["short_id"], reverse=True)[:5]
    lines = ["Recent Users - Last 5:\n"]
    for u in recent:
        lines.append(f"ID: {u['short_id']} | {u['name']} | {u['location']} | {u['email']}")
    await update.message.reply_text("\n".join(lines))
async def bylocation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    if not USERS:
        await update.message.reply_text("No users yet."); return
    counts = {}
    for u in USERS.values():
        loc = u["location"] or "Unknown"
        counts[loc] = counts.get(loc, 0) + 1
    lines = ["Users by Location:\n"]
    for loc, c in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"{loc}: {c}")
    await update.message.reply_text("\n".join(lines))
async def listadmins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    await update.message.reply_text("Admin IDs:\n\n" + "\n".join([str(a) for a in ADMIN_IDS]))

# ---------- CHAT ----------
async def message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please send your message in this format:\n/message I need help with my job")
        return
    text = " ".join(context.args)
    uid = update.effective_user.id
    name = USERS.get(uid, {}).get("name", update.effective_user.first_name)
    short_id = USERS.get(uid, {}).get("short_id", "No ID - please send /start")
    for aid in ADMIN_IDS:
        try: await context.bot.send_message(aid, f"Message from {name}\nID: {short_id}\n\n{text}\n\nReply with:\n/reply {short_id} your reply")
        except Exception: pass
    await update.message.reply_text("Your message has been sent to admin. Admin will reply to you soon.")
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message; uid = update.effective_user.id
    if is_admin(uid):
        caption = (msg.caption or "") if msg.caption else ""
        if caption.startswith("/reply"):
            try:
                parts = caption.split(None, 2)
                short_id = int(parts[1]); text = parts[2] if len(parts) > 2 else ""
                tg_id, u = get_user_by_short(short_id)
                if tg_id:
                    if text: await context.bot.send_message(tg_id, f"Reply from Admin:\n\n{text}")
                    if msg.photo: await context.bot.send_photo(tg_id, msg.photo[-1].file_id, caption=text if text else None)
                    elif msg.document: await context.bot.send_document(tg_id, msg.document.file_id, caption=text if text else None)
                    await msg.reply_text(f"Sent to {u['name']} (ID: {short_id})")
                    return
            except Exception: pass
        await msg.reply_text("To reply to a user, please use:\n/reply 101 your message\n\nPlease get the ID from /users")
        return
    if is_banned(uid):
        await msg.reply_text("Your account has been restricted. Please contact admin.")
        return
    name = USERS.get(uid, {}).get("name", update.effective_user.first_name)
    short_id = USERS.get(uid, {}).get("short_id", "No ID")
    header = f"New Message from {name}\nID: {short_id}\n\nReply with:\n/reply {short_id} your reply"
    for aid in ADMIN_IDS:
        try:
            await context.bot.send_message(aid, header)
            await msg.forward(aid)
        except Exception: pass
    await msg.reply_text("Your message has been sent to admin. Admin will reply to you soon.")

# ---------- ADD / EDIT / DELETE JOB ----------
ADD_TITLE, ADD_PAY, ADD_NEEDED = range(3, 6)
async def addjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only.")
        return ConversationHandler.END
    await update.message.reply_text("What is the job title?")
    return ADD_TITLE
async def addjob_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_title"] = update.message.text
    await update.message.reply_text("What is the pay?")
    return ADD_PAY
async def addjob_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_pay"] = update.message.text
    await update.message.reply_text("How many workers are needed?")
    return ADD_NEEDED
async def addjob_needed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: needed = int(update.message.text)
    except Exception:
        await update.message.reply_text("Please send a number only.")
        return ADD_NEEDED
    new_id = max([j["id"] for j in JOBS], default=0) + 1
    JOBS.append({"id": new_id, "title": context.user_data["new_title"], "pay": context.user_data["new_pay"], "needed": needed, "joined": 0})
    save_data()
    await update.message.reply_text(f"Job added:\n{new_id}. {context.user_data['new_title']} - {context.user_data['new_pay']}")
    return ConversationHandler.END
async def editjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try:
        job_id = int(context.args[0]); field = context.args[1].lower(); value = " ".join(context.args[2:])
        for j in JOBS:
            if j["id"] == job_id:
                if field in ["needed", "joined"]: j[field] = int(value)
                elif field in ["title", "pay"]: j[field] = value
                else:
                    await update.message.reply_text("Field must be: title | pay | needed | joined"); return
                save_data()
                await update.message.reply_text(f"Updated:\n{j['id']}. {j['title']} - {j['pay']}")
                return
        await update.message.reply_text("Job not found.")
    except Exception:
        await update.message.reply_text("Usage:\n/editjob 5 pay $600/mo\n/editjob 5 needed 20")
async def deletejob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Access denied. Admin only."); return
    try:
        job_id = int(context.args[0])
        for j in JOBS:
            if j["id"] == job_id:
                JOBS.remove(j); save_data()
                await update.message.reply_text(f"Deleted job {job_id}: {j['title']}")
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
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("faq", faq_command))
    app.add_handler(CommandHandler("status", status_command))
    # 30 Admin
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("userinfo", userinfo_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("assignjob", assignjob_command))
    app.add_handler(CommandHandler("removejob", removejob_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("unbanall", unbanall_command))
    app.add_handler(CommandHandler("deleteuser", deleteuser_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("jobstats", jobstats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("export", export_command))
    app.add_handler(CommandHandler("backup", backup_command))
    app.add_handler(CommandHandler("addjob", addjob_command))
    app.add_handler(CommandHandler("editjob", editjob_command))
    app.add_handler(CommandHandler("deletejob", deletejob_command))
    app.add_handler(CommandHandler("setpay", setpay_command))
    app.add_handler(CommandHandler("settitle", settitle_command))
    app.add_handler(CommandHandler("setneeded", setneeded_command))
    app.add_handler(CommandHandler("resetjobs", resetjobs_command))
    app.add_handler(CommandHandler("warn", warn_command))
    app.add_handler(CommandHandler("warnings", warnings_command))
    app.add_handler(CommandHandler("clearwarnings", clearwarnings_command))
    app.add_handler(CommandHandler("notify", notify_command))
    app.add_handler(CommandHandler("reply", reply_command))
    app.add_handler(CommandHandler("topusers", topusers_command))
    app.add_handler(CommandHandler("recent", recent_command))
    app.add_handler(CommandHandler("bylocation", bylocation_command))
    app.add_handler(CommandHandler("listadmins", listadmins_command))
    app.add_handler(CommandHandler("message", message_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(ConversationHandler(entry_points=[CommandHandler("start", start_command)], states={REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)], REG_LOC: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_loc)], REG_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_email)]}, fallbacks=[CommandHandler("cancel", cancel_command)]))
    app.add_handler(ConversationHandler(entry_points=[CommandHandler("addjob", addjob_command)], states={ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addjob_title)], ADD_PAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, addjob_pay)], ADD_NEEDED: [MessageHandler(filters.TEXT & ~filters.COMMAND, addjob_needed)]}, fallbacks=[CommandHandler("cancel", cancel_command)]))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_messages))
    return app

if __name__ == "__main__":
    print(f"TOKEN present: {bool(TOKEN)} len={len(TOKEN) if TOKEN else 0}", flush=True)
    if not TOKEN:
        print("ERROR: BOT_TOKEN not set! Please check FadeHost Env Vars", flush=True)
        import time
        while True: time.sleep(60)
    else:
        print("1840 Bot Running...", flush=True)
        build_app().run_polling()
