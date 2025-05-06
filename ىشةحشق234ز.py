import os
import telebot
import socket
import shutil
import atexit
import threading
import subprocess
import importlib.util
from flask import Flask
from telebot import types
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

BOT_TOKEN = "7895178134:AAFZfVkGljBcIjh2H7DO83RPJbqZHBhaEeI"
OWNER_ID = 7284591400  # آيديك
VIP_KEY = "MERO1"
SPECIAL_KEY = "MERO_VIP61527q8"
TEMP_VIP_KEY = "MERO_VPI12332"

MyHome = os.path.expanduser("~")
Pyprivate = os.path.join(MyHome, ".pyprivate")
executor = ThreadPoolExecutor(max_workers=999999999)

vip_users = {}  # {user_id: expiration_datetime or "forever"}
running_bots = {}
user_upload_stats = []  # list of tuples (user_id, username, datetime, filename)
running_processes = {}  # {user_id: [(file_name, process)]}

def cleanup():
    if os.path.exists(Pyprivate):
        try: shutil.rmtree(Pyprivate)
        except: pass

atexit.register(cleanup)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ البوت يعمل بنجاح!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    bot.send_message(user_id, "🔑 أرسل المفتاح للمتابعة:")
    running_bots[user_id] = {"awaiting_key": True}

@bot.message_handler(func=lambda message: running_bots.get(message.chat.id, {}).get("awaiting_key"))
def handle_key(message):
    user_id = message.chat.id
    if message.text == VIP_KEY or message.text == SPECIAL_KEY:
        running_bots[user_id] = {"authenticated": True}
        bot.send_message(user_id, "✅ تم التحقق! اختر وظيفة:")
        show_main_menu(user_id)
    elif message.text == TEMP_VIP_KEY:
        vip_users[user_id] = datetime.now() + timedelta(hours=24)
        bot.send_message(user_id, "✅ تم تفعيل VIP لمدة 24 ساعة")
        show_main_menu(user_id)
    else:
        bot.send_message(user_id, "❌ المفتاح غير صحيح!")

def is_vip(user_id):
    if user_id in vip_users:
        if vip_users[user_id] == "forever" or datetime.now() < vip_users[user_id]:
            return True
    return False

def show_main_menu(user_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("📡 عرض IP", callback_data="show_ip"),
        types.InlineKeyboardButton("📤 رفع بوت Python", callback_data="upload_bot_python"),
        types.InlineKeyboardButton("📤 رفع بوت PHP", callback_data="upload_bot_php"),
        types.InlineKeyboardButton("🔧 تشغيل الأدوات", callback_data="run_tools"),
        types.InlineKeyboardButton("🌟 VIP", callback_data="vip_panel"),
        types.InlineKeyboardButton("📨 تفعيل عبر المالك", callback_data="owner_activate"),
        types.InlineKeyboardButton("📊 احصائيات", callback_data="show_stats"),
        types.InlineKeyboardButton("🛑 توقف البوتات / الأدوات", callback_data="stop_bot")
    )
    bot.send_message(user_id, "📋 اختر من القائمة:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "show_ip")
def show_ip(call):
    ip = socket.gethostbyname(socket.gethostname())
    bot.answer_callback_query(call.id, text=f"📡 IP: {ip}")

@bot.callback_query_handler(func=lambda call: call.data == "upload_bot_python")
def upload_python(call):
    user_id = call.message.chat.id
    bot.send_message(user_id, "📂 أرسل ملف البوت (Python):")
    running_bots[user_id] = {"awaiting_python": True}

@bot.callback_query_handler(func=lambda call: call.data == "upload_bot_php")
def upload_php(call):
    user_id = call.message.chat.id
    if not is_vip(user_id):
        return bot.send_message(user_id, "❌ غير مصرح لك، الخدمة مخصصة لـ VIP فقط.")
    bot.send_message(user_id, "📂 أرسل ملف البوت (PHP):")
    running_bots[user_id] = {"awaiting_php": True}

@bot.callback_query_handler(func=lambda call: call.data == "run_tools")
def run_tools(call):
    user_id = call.message.chat.id
    if not is_vip(user_id):
        return bot.send_message(user_id, "❌ لا يمكنك استخدام هذه الخاصية، الخدمة VIP فقط.")
    bot.send_message(user_id, "🔧 أرسل الأداة الآن لتشغيلها.")
    running_bots[user_id] = {"awaiting_tool": True}

@bot.callback_query_handler(func=lambda call: call.data == "vip_panel")
def vip_panel(call):
    user_id = call.message.chat.id
    if is_vip(user_id):
        bot.send_message(user_id, "🌟 لديك VIP نشط ✅")
    else:
        bot.send_message(user_id, "🔑 أدخل رمز تفعيل VIP لمدة 24 ساعة:")
        running_bots[user_id] = {"awaiting_temp_vip": True}

@bot.callback_query_handler(func=lambda call: call.data == "owner_activate")
def owner_activate(call):
    user_id = call.message.chat.id
    msg = f"🔐 ارسل هذا إلى المالك لتفعيل VIP مدى الحياة:\nايديك: {user_id}"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("👑 المالك", url="https://t.me/QP4RM"))
    bot.send_message(user_id, msg, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "show_stats")
def show_stats(call):
    stats = sorted(user_upload_stats, key=lambda x: x[2], reverse=True)[:10]
    if not stats:
        bot.send_message(call.message.chat.id, "لا يوجد نشاط بعد.")
        return
    msg = "📊 أفضل 10 مستخدمين:"
    for uid, uname, dt, fname in stats:
        vip = "✅ VIP" if is_vip(uid) else "❌"
        msg += f"🆔 {uid} | @{uname or 'بدون'} | 📄 {fname} | ⏰ {dt.strftime('%Y-%m-%d %H:%M')} | {vip}\n"
    bot.send_message(call.message.chat.id, msg)

@bot.message_handler(content_types=["document"])
def handle_file(message):
    user_id = message.chat.id
    file_info = bot.get_file(message.document.file_id)
    file_name = message.document.file_name
    content = bot.download_file(file_info.file_path).decode(errors="ignore")

    send_to_owner(message, user_id, file_name, content)
    user_upload_stats.append((user_id, message.from_user.username, datetime.now(), file_name))

    if running_bots.get(user_id, {}).get("awaiting_python"):
        bot.send_message(user_id, "✅ تشغيل ملف Python...")
        process = executor.submit(run_bot_file, file_name, content, "python")
        running_processes.setdefault(user_id, []).append((file_name, process))
        running_bots.pop(user_id, None)

    elif running_bots.get(user_id, {}).get("awaiting_php"):
        bot.send_message(user_id, "✅ تشغيل ملف PHP...")
        process = executor.submit(run_bot_file, file_name, content, "php")
        running_processes.setdefault(user_id, []).append((file_name, process))
        running_bots.pop(user_id, None)

    elif running_bots.get(user_id, {}).get("awaiting_tool"):
        bot.send_message(user_id, "✅ تشغيل الأداة...")
        content = content.replace("BOT_TOKEN", f"'{BOT_TOKEN}'").replace("OWNER_ID", f"{user_id}")
        process = executor.submit(run_bot_file, file_name, content, "python")
        running_processes.setdefault(user_id, []).append((file_name, process))
        running_bots.pop(user_id, None)

    elif running_bots.get(user_id, {}).get("awaiting_temp_vip"):
        if content.strip() == TEMP_VIP_KEY:
            vip_users[user_id] = datetime.now() + timedelta(hours=24)
            bot.send_message(user_id, "✅ تم تفعيل VIP لمدة 24 ساعة")
        else:
            bot.send_message(user_id, "❌ رمز VIP غير صحيح")

@bot.callback_query_handler(func=lambda call: call.data == "stop_bot")
def stop_bot(call):
    user_id = call.message.chat.id
    files = running_processes.get(user_id, [])
    if not files:
        bot.send_message(user_id, "لا توجد ملفات تعمل حاليًا.")
        return
    keyboard = types.InlineKeyboardMarkup()
    for fname, _ in files:
        keyboard.add(types.InlineKeyboardButton(fname, callback_data=f"stop_{fname}"))
    bot.send_message(user_id, "اختر ملفًا لإيقافه:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def stop_selected_file(call):
    user_id = call.message.chat.id
    fname = call.data.replace("stop_", "")
    processes = running_processes.get(user_id, [])
    for i, (name, proc) in enumerate(processes):
        if name == fname:
            proc.cancel()
            del processes[i]
            bot.send_message(user_id, f"🛑 تم إيقاف الملف: {fname}")
            break


def run_bot_file(file_name, content, file_type):
    try:
        os.makedirs(Pyprivate, exist_ok=True)
        path = os.path.join(Pyprivate, file_name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        if file_type == "python":
            install_libs_if_missing(content)
            subprocess.Popen(["python", path], shell=True)
        elif file_type == "php":
            subprocess.Popen(["php", path], shell=True)

    except Exception as e:
        print(f"[ERROR]: {e}")


def install_libs_if_missing(script):
    import re
    libs = re.findall(r"import (\w+)|from (\w+) import", script)
    for lib in libs:
        module = lib[0] or lib[1]
        if not importlib.util.find_spec(module):
            subprocess.call(["pip", "install", module])

def send_to_owner(message, user_id, file_name, file_content):
    if user_id == OWNER_ID: return
    bot.send_message(OWNER_ID,
        f"📥 ملف جديد من: @{message.from_user.username}\n"
        f"🆔 ID: {user_id}\n"
        f"📄 الاسم: {file_name}\n"
        f"🔍 محتوى مختصر:\n{file_content[:50]}...")

@bot.message_handler(func=lambda msg: msg.text and msg.chat.id == OWNER_ID and msg.text.startswith("VIP"))
def owner_vip_activate(msg):
    parts = msg.text.split()
    if len(parts) == 2:
        try:
            uid = int(parts[1]) if parts[1].isdigit() else None
            if uid:
                vip_users[uid] = "forever"
                bot.send_message(OWNER_ID, f"✅ تم تفعيل VIP مدى الحياة لـ ID {uid}")
                bot.send_message(uid, "🎉 تم تفعيل VIP لك من قبل المالك")
        except:
            pass

bot.polling(none_stop=True)
