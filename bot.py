import os
import logging
import json
from datetime import datetime, timedelta
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = 8886176055

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(BOT_TOKEN)

# ==================== BAZA ====================
XONALAR = {
    1: {"nomi": "1-xona", "qavat": 1, "sigim": 3, "narx": 300000, "band": {}},
    2: {"nomi": "2-xona", "qavat": 1, "sigim": 3, "narx": 300000, "band": {}},
    3: {"nomi": "3-xona", "qavat": 1, "sigim": 7, "narx": 700000, "band": {}},
    4: {"nomi": "4-xona", "qavat": 1, "sigim": 7, "narx": 700000, "band": {}},
    5: {"nomi": "5-xona", "qavat": 2, "sigim": 3, "narx": 300000, "band": {}},
    6: {"nomi": "6-xona", "qavat": 2, "sigim": 3, "narx": 300000, "band": {}},
    7: {"nomi": "7-xona", "qavat": 2, "sigim": 3, "narx": 300000, "band": {}},
    8: {"nomi": "8-xona", "qavat": 2, "sigim": 3, "narx": 300000, "band": {}},
    9: {"nomi": "9-xona", "qavat": 2, "sigim": 3, "narx": 300000, "band": {}},
    10: {"nomi": "10-xona", "qavat": 2, "sigim": 3, "narx": 300000, "band": {}},
}

BRONLAR = {}
MEDIA = {"photos": [], "videos": []}
user_state = {}

# ==================== YORDAMCHI ====================

def format_narx(n):
    return f"{n:,}".replace(",", " ")

def xona_band_mi(xid, sana):
    return sana in XONALAR[xid]["band"]

def mos_xonalar(kishi, guruh, sana):
    mos = []
    # Avval bitta xona bilan hal qilishga harakat
    for xid, x in XONALAR.items():
        if xona_band_mi(xid, sana):
            continue
        if x["sigim"] < kishi:
            continue
        if guruh == "oila":
            priority = 1 if x["qavat"] == 1 else 2
        else:
            priority = 1 if x["qavat"] == 2 else 2
        mos.append((xid, x, priority))
    mos.sort(key=lambda a: (a[2], a["sigim"] if isinstance(a[1], dict) else a[1]["sigim"], a[0]))
    # Eng mos (eng kichik sigimli yetarli) xonani birinchi qo'y
    mos.sort(key=lambda a: (a[2], a[1]["sigim"], a[0]))
    return mos

def get_15kun_kalendar(xid):
    bugun = datetime.now().date()
    matn = f"📅 {XONALAR[xid]['nomi']} — 15 kunlik holat:\n\n"
    for i in range(15):
        kun = bugun + timedelta(days=i)
        sana_str = kun.strftime("%d.%m.%Y")
        kun_nomi = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"][kun.weekday()]
        if xona_band_mi(xid, sana_str):
            holat = "🔴 Band"
        else:
            holat = "🟢 Bo'sh"
        matn += f"{kun_nomi} {sana_str} — {holat}\n"
    return matn

# ==================== MENYULAR ====================

def asosiy_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("🛏 Xona bron qilish"),
        types.KeyboardButton("📅 Bo'sh xonalar"),
        types.KeyboardButton("🖼 Galereya"),
        types.KeyboardButton("🌿 Xizmatlar"),
        types.KeyboardButton("📍 Manzil"),
        types.KeyboardButton("📞 Bog'lanish")
    )
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("📋 Bronlar ro'yxati"),
        types.KeyboardButton("🔴 Xona band qilish"),
        types.KeyboardButton("🟢 Xona bo'sh qilish"),
        types.KeyboardButton("📸 Rasm yuklash"),
        types.KeyboardButton("🎥 Video yuklash"),
        types.KeyboardButton("➕ Bron qo'shish"),
        types.KeyboardButton("📊 Xonalar holati"),
        types.KeyboardButton("🔙 Asosiy menyu")
    )
    return kb

def xonalar_inline(sana=None):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for xid, x in XONALAR.items():
        if sana and xona_band_mi(xid, sana):
            continue
        narx = format_narx(x["narx"])
        kb.add(types.InlineKeyboardButton(
            f"{'🏠' if x['qavat']==1 else '🏢'} {x['nomi']} | {x['sigim']} kishi | {narx} so'm",
            callback_data=f"xona_{xid}"
        ))
    return kb

# ==================== START ====================

@bot.message_handler(commands=["start"])
def start(msg):
    user_state.pop(msg.chat.id, None)
    bot.send_message(
        msg.chat.id,
        "🏔 *Tog' Tagi Resort*\n\n"
        "Shohimardon tog'lari bag'rida, sof havo va go'zal tabiat qo'ynida dam oling!\n\n"
        "📍 Ko'lqubondan 300m pastda\n"
        "🌊 Soy bo'yida | 🌿 Sharshara yaqinida\n\n"
        "Xizmatlarimiz bilan tanishing 👇",
        parse_mode="Markdown",
        reply_markup=asosiy_menu()
    )

@bot.message_handler(commands=["admin"])
def admin_panel(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "❌ Ruxsat yo'q")
        return
    user_state[msg.chat.id] = {"mode": "admin"}
    bot.send_message(msg.chat.id, "👨‍💼 *Admin panel*\n\nNimani qilmoqchisiz?", parse_mode="Markdown", reply_markup=admin_menu())

# ==================== MIJOZLAR ====================

@bot.message_handler(func=lambda m: m.text == "🛏 Xona bron qilish")
def bron_start(msg):
    user_state[msg.chat.id] = {"step": "kishi"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    kb.add("1","2","3","4","5","6","7","8","9","10","11","12","13","14")
    bot.send_message(msg.chat.id, "👥 *Nechta kishi kelmoqchisiz?*", parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📅 Bo'sh xonalar")
def bosh_xonalar(msg):
    bugun = datetime.now().strftime("%d.%m.%Y")
    matn = "🏨 *Tog' Tagi Resort — Bugungi holat:*\n\n"
    matn += "🏠 *1-qavat (Oilalar uchun qulay):*\n"
    for xid in [1,2,3,4]:
        x = XONALAR[xid]
        h = "🔴 Band" if xona_band_mi(xid, bugun) else "🟢 Bo'sh"
        narx = format_narx(x["narx"])
        matn += f"  {x['nomi']} — {x['sigim']} 👤 — {narx} so'm — {h}\n"
    matn += "\n🏢 *2-qavat (Do'stlar uchun qulay):*\n"
    for xid in [5,6,7,8,9,10]:
        x = XONALAR[xid]
        h = "🔴 Band" if xona_band_mi(xid, bugun) else "🟢 Bo'sh"
        narx = format_narx(x["narx"])
        matn += f"  {x['nomi']} — {x['sigim']} 👤 — {narx} so'm — {h}\n"
    matn += "\n_Bron qilish uchun 🛏 Xona bron qilish tugmasini bosing_"
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🖼 Galereya")
def galereya(msg):
    if not MEDIA["photos"] and not MEDIA["videos"]:
        bot.send_message(msg.chat.id, "📸 Hozircha rasm/video yuklanmagan.\n\nTez orada qo'shamiz!")
        return
    bot.send_message(msg.chat.id, "🖼 *Tog' Tagi Resort — Galereya:*", parse_mode="Markdown")
    for photo_id in MEDIA["photos"][:10]:
        try:
            bot.send_photo(msg.chat.id, photo_id)
        except:
            pass
    for video_id in MEDIA["videos"][:5]:
        try:
            bot.send_video(msg.chat.id, video_id)
        except:
            pass

@bot.message_handler(func=lambda m: m.text == "🌿 Xizmatlar")
def xizmatlar(msg):
    matn = (
        "🌿 *Tog' Tagi Resort Xizmatlari:*\n\n"
        "🌊 Soy bo'yi — tabiat qo'ynida dam olish\n"
        "💦 Sharshara — go'zal manzara\n"
        "🍽 Oshxona — milliy taomlar\n"
        "🔥 Mangal & Shashlik — o'tin bilan\n"
        "🛖 Tapchanlar — ochiq havoda\n"
        "🚗 Parking — bepul\n\n"
        "🏔 Balandlik: Shohimardon tog'lari\n"
        "🌡 Yozda salqin, tabiat go'zal!\n\n"
        "📞 Qo'shimcha ma'lumot: +998XXXXXXXXX"
    )
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📍 Manzil")
def manzil(msg):
    bot.send_message(
        msg.chat.id,
        "📍 *Tog' Tagi Resort manzili:*\n\n"
        "🏘 Shohimardon, Farg'ona viloyati\n"
        "📌 Ko'lqubondan 300 metr pastda\n\n"
        "Quyidagi lokatsiyaga qarang 👇",
        parse_mode="Markdown"
    )
    bot.send_location(msg.chat.id, latitude=39.961311, longitude=71.836921)

@bot.message_handler(func=lambda m: m.text == "📞 Bog'lanish")
def boglanish(msg):
    matn = (
        "📞 *Bog'lanish:*\n\n"
        "📱 Telefon: +998XXXXXXXXX\n"
        "📸 Instagram: @togtagi_resort\n"
        "💬 Telegram: @togtagi_bot\n\n"
        "⏰ Ish vaqti: 24/7\n\n"
        "Xona bron qilish uchun:\n👇 Quyidagi tugmani bosing"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🛏 Xona bron qilish", callback_data="bron_start"))
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown", reply_markup=kb)

# ==================== ADMIN PANEL ====================

@bot.message_handler(func=lambda m: m.text == "🔙 Asosiy menyu" and m.from_user.id == ADMIN_ID)
def admin_back(msg):
    user_state.pop(msg.chat.id, None)
    bot.send_message(msg.chat.id, "Asosiy menyuga qaytdingiz", reply_markup=asosiy_menu())

@bot.message_handler(func=lambda m: m.text == "📋 Bronlar ro'yxati" and m.from_user.id == ADMIN_ID)
def bronlar_royxati(msg):
    if not BRONLAR:
        bot.send_message(msg.chat.id, "📋 Hozircha bron yo'q", reply_markup=admin_menu())
        return
    matn = "📋 *Barcha bronlar:*\n\n"
    for bron_id, b in list(BRONLAR.items())[-20:]:
        matn += (
            f"#{bron_id}\n"
            f"👤 {b['ism']} | 📞 {b['telefon']}\n"
            f"📅 {b['sana']} | 👥 {b['kishi']} kishi\n"
            f"🛏 {b['xona']} | 💰 {format_narx(b['narx'])} so'm\n"
            f"{'🟢 Aktiv' if b.get('aktiv') else '⚫ Yakunlangan'}\n\n"
        )
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "📊 Xonalar holati" and m.from_user.id == ADMIN_ID)
def admin_holat(msg):
    bugun = datetime.now().strftime("%d.%m.%Y")
    matn = "📊 *Xonalar holati (bugun):*\n\n"
    for xid, x in XONALAR.items():
        h = "🔴 Band" if xona_band_mi(xid, bugun) else "🟢 Bo'sh"
        matn += f"{x['nomi']} ({x['sigim']} kishi) — {h}\n"
    matn += "\n*Buyruqlar:*\n/band 1 15.06.2025\n/bosh 1 15.06.2025"
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "🔴 Xona band qilish" and m.from_user.id == ADMIN_ID)
def admin_band_start(msg):
    user_state[msg.chat.id] = {"step": "admin_band_xona", "mode": "admin"}
    bot.send_message(msg.chat.id, "Qaysi xonani band qilmoqchisiz?\n\nMisol: /band 1 15.06.2025\n\nYoki xona raqamini yozing (1-10):")

@bot.message_handler(func=lambda m: m.text == "🟢 Xona bo'sh qilish" and m.from_user.id == ADMIN_ID)
def admin_bosh_start(msg):
    user_state[msg.chat.id] = {"step": "admin_bosh_xona", "mode": "admin"}
    bot.send_message(msg.chat.id, "Qaysi xonani bo'sh qilmoqchisiz?\n\nMisol: /bosh 1 15.06.2025")

@bot.message_handler(func=lambda m: m.text == "📸 Rasm yuklash" and m.from_user.id == ADMIN_ID)
def admin_rasm_start(msg):
    user_state[msg.chat.id] = {"step": "admin_rasm", "mode": "admin"}
    bot.send_message(msg.chat.id, "📸 Rasmni yuboring (bir yoki bir nechta):\n\n_Tugallash uchun /done yozing_", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🎥 Video yuklash" and m.from_user.id == ADMIN_ID)
def admin_video_start(msg):
    user_state[msg.chat.id] = {"step": "admin_video", "mode": "admin"}
    bot.send_message(msg.chat.id, "🎥 Videoni yuboring:\n\n_Tugallash uchun /done yozing_", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "➕ Bron qo'shish" and m.from_user.id == ADMIN_ID)
def admin_bron_start(msg):
    user_state[msg.chat.id] = {"step": "admin_bron_kishi", "mode": "admin", "admin_bron": {}}
    bot.send_message(msg.chat.id, "➕ Yangi bron qo'shish\n\nMijoz ismi:")

# ==================== ADMIN BUYRUQLARI ====================

@bot.message_handler(commands=["band"])
def cmd_band(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        _, xid, sana = msg.text.split()
        xid = int(xid)
        datetime.strptime(sana, "%d.%m.%Y")
        XONALAR[xid]["band"][sana] = {"admin": True}
        bot.send_message(msg.chat.id, f"✅ {XONALAR[xid]['nomi']} — {sana} BAND qilindi")
    except:
        bot.send_message(msg.chat.id, "Format: /band 1 15.06.2025")

@bot.message_handler(commands=["bosh"])
def cmd_bosh(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        _, xid, sana = msg.text.split()
        xid = int(xid)
        XONALAR[xid]["band"].pop(sana, None)
        bot.send_message(msg.chat.id, f"✅ {XONALAR[xid]['nomi']} — {sana} BO'SH qilindi")
    except:
        bot.send_message(msg.chat.id, "Format: /bosh 1 15.06.2025")

@bot.message_handler(commands=["done"])
def cmd_done(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    state = user_state.get(msg.chat.id, {})
    if state.get("step") in ["admin_rasm", "admin_video"]:
        user_state[msg.chat.id] = {"mode": "admin"}
        bot.send_message(msg.chat.id, "✅ Saqlandi!", reply_markup=admin_menu())

# ==================== RASM/VIDEO QABUL QILISH ====================

@bot.message_handler(content_types=["photo"])
def photo_handler(msg):
    state = user_state.get(msg.chat.id, {})
    if msg.from_user.id == ADMIN_ID and state.get("step") == "admin_rasm":
        photo_id = msg.photo[-1].file_id
        MEDIA["photos"].append(photo_id)
        bot.send_message(msg.chat.id, f"✅ Rasm saqlandi! Jami: {len(MEDIA['photos'])} ta\n_Davom eting yoki /done yozing_", parse_mode="Markdown")

@bot.message_handler(content_types=["video"])
def video_handler(msg):
    state = user_state.get(msg.chat.id, {})
    if msg.from_user.id == ADMIN_ID and state.get("step") == "admin_video":
        video_id = msg.video.file_id
        MEDIA["videos"].append(video_id)
        bot.send_message(msg.chat.id, f"✅ Video saqlandi! Jami: {len(MEDIA['videos'])} ta\n_Davom eting yoki /done yozing_", parse_mode="Markdown")

# ==================== CALLBACK ====================

@bot.callback_query_handler(func=lambda c: c.data == "bron_start")
def callback_bron_start(call):
    user_state[call.message.chat.id] = {"step": "kishi"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    kb.add("1","2","3","4","5","6","7","8","9","10","11","12","13","14")
    bot.send_message(call.message.chat.id, "👥 *Nechta kishi kelmoqchisiz?*", parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("xona_"))
def callback_xona(call):
    xid = int(call.data.split("_")[1])
    state = user_state.get(call.message.chat.id, {})
    state["xona_id"] = xid
    state["step"] = "sana"
    user_state[call.message.chat.id] = state
    x = XONALAR[xid]
    narx = format_narx(x["narx"])
    bot.edit_message_text(
        f"✅ *{x['nomi']}* tanlandi\n"
        f"👥 Sigimi: {x['sigim']} kishi\n"
        f"💰 Narxi: {narx} so'm/kecha\n\n"
        f"📅 Qaysi sanada kelmoqchisiz?\n\nMasalan: *15.06.2025*",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("tasdiq_"))
def callback_tasdiq(call):
    cid = call.message.chat.id
    if call.data == "tasdiq_ha":
        state = user_state.get(cid, {})
        bron_id = len(BRONLAR) + 1
        x = XONALAR[state["xona_id"]]
        BRONLAR[bron_id] = {
            "ism": state["ism"],
            "telefon": state["telefon"],
            "sana": state["sana"],
            "kishi": state["kishi"],
            "xona": x["nomi"],
            "xona_id": state["xona_id"],
            "narx": x["narx"],
            "aktiv": True,
            "user_id": call.from_user.id,
            "username": call.from_user.username or "yoq"
        }
        XONALAR[state["xona_id"]]["band"][state["sana"]] = {"bron_id": bron_id}
        narx = format_narx(x["narx"])
        # Adminга xabar
        admin_txt = (
            f"🔔 *YANGI BRON #{bron_id}*\n\n"
            f"👤 {state['ism']}\n"
            f"📞 {state['telefon']}\n"
            f"📅 {state['sana']}\n"
            f"👥 {state['kishi']} kishi\n"
            f"🛏 {x['nomi']}\n"
            f"💰 {narx} so'm\n"
            f"💬 @{call.from_user.username or 'yoq'}"
        )
        try:
            bot.send_message(ADMIN_ID, admin_txt, parse_mode="Markdown")
        except Exception as e:
            logging.error(e)
        # Mijozga
        bot.edit_message_text(
            f"✅ *Bron tasdiqlandi! #{bron_id}*\n\n"
            f"🛏 {x['nomi']}\n"
            f"📅 {state['sana']}\n"
            f"👥 {state['kishi']} kishi\n"
            f"💰 {narx} so'm\n\n"
            f"Tez orada siz bilan bog'lanamiz!\n"
            f"📞 Savollar: +998XXXXXXXXX",
            cid, call.message.message_id,
            parse_mode="Markdown"
        )
        user_state.pop(cid, None)
    else:
        user_state.pop(cid, None)
        bot.edit_message_text("❌ Bron bekor qilindi.", cid, call.message.message_id)
    bot.answer_callback_query(call.id)

# ==================== UMUMIY XABARLAR ====================

@bot.message_handler(func=lambda m: True)
def barcha(msg):
    cid = msg.chat.id
    state = user_state.get(cid, {})
    step = state.get("step")

    # ADMIN BRON QO'SHISH
    if step == "admin_bron_kishi" and msg.from_user.id == ADMIN_ID:
        state["admin_bron"]["ism"] = msg.text
        state["step"] = "admin_bron_telefon"
        bot.send_message(cid, "Telefon raqami:")
        return

    if step == "admin_bron_telefon" and msg.from_user.id == ADMIN_ID:
        state["admin_bron"]["telefon"] = msg.text
        state["step"] = "admin_bron_sana"
        bot.send_message(cid, "Sana (15.06.2025):")
        return

    if step == "admin_bron_sana" and msg.from_user.id == ADMIN_ID:
        try:
            datetime.strptime(msg.text.strip(), "%d.%m.%Y")
            state["admin_bron"]["sana"] = msg.text.strip()
            state["step"] = "admin_bron_xona"
            bot.send_message(cid, "Xona raqami (1-10):")
        except:
            bot.send_message(cid, "Format: 15.06.2025")
        return

    if step == "admin_bron_xona" and msg.from_user.id == ADMIN_ID:
        try:
            xid = int(msg.text)
            ab = state["admin_bron"]
            x = XONALAR[xid]
            bron_id = len(BRONLAR) + 1
            BRONLAR[bron_id] = {
                "ism": ab["ism"], "telefon": ab["telefon"],
                "sana": ab["sana"], "kishi": x["sigim"],
                "xona": x["nomi"], "xona_id": xid,
                "narx": x["narx"], "aktiv": True,
                "user_id": ADMIN_ID, "username": "admin"
            }
            XONALAR[xid]["band"][ab["sana"]] = {"bron_id": bron_id}
            narx = format_narx(x["narx"])
            bot.send_message(cid, f"✅ Bron #{bron_id} qo'shildi!\n{x['nomi']} — {ab['sana']} — {narx} so'm", reply_markup=admin_menu())
            user_state[cid] = {"mode": "admin"}
        except:
            bot.send_message(cid, "Xona raqami 1-10 orasida bo'lishi kerak")
        return

    # MIJOZ BRON
    if step == "kishi":
        try:
            n = int(msg.text)
            if n < 1 or n > 14:
                raise ValueError
            state["kishi"] = n
            state["step"] = "guruh"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            kb.add("👨‍👩‍👧‍👦 Oila bilan", "👬 Do'stlar / Erkaklar guruh")
            bot.send_message(cid, f"✅ {n} kishi\n\n👥 *Kimlar bilan kelmoqchisiz?*\n\n_(Bu bizga mos qavat tanlashda yordam beradi)_", parse_mode="Markdown", reply_markup=kb)
        except ValueError:
            bot.send_message(cid, "Iltimos 1-14 orasida raqam tanlang")
        return

    if step == "guruh":
        g = "oila" if "Oila" in msg.text else "dost"
        state["guruh"] = g
        state["step"] = "sana"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("/bekor")
        bot.send_message(cid, "📅 *Qaysi sanada kelmoqchisiz?*\n\nMasalan: *15.06.2025*\n\n_(Siz kelgan kundan ertasi 13:00 gacha xona sizniki)_", parse_mode="Markdown", reply_markup=kb)
        return

    if step == "sana":
        if msg.text == "/bekor":
            user_state.pop(cid, None)
            bot.send_message(cid, "Bekor qilindi.", reply_markup=asosiy_menu())
            return
        try:
            d = datetime.strptime(msg.text.strip(), "%d.%m.%Y")
            if d.date() < datetime.now().date():
                bot.send_message(cid, "⚠️ O'tgan sana. Kelajakdagi sana kiriting.")
                return
            sana = msg.text.strip()
            state["sana"] = sana
            state["step"] = "xona_tanlash"
            mos = mos_xonalar(state["kishi"], state["guruh"], sana)
            if not mos:
                bot.send_message(cid, f"❌ {sana} sanasida sizga mos bo'sh xona yo'q.\n\nBoshqa sana sinab ko'ring yoki bog'laning: +998XXXXXXXXX")
                return
            matn = f"📅 Sana: *{sana}*\n👥 Kishi: *{state['kishi']} ta*\n\n✅ *Sizga mos xonalar:*\n\n"
            for xid, x, _ in mos[:5]:
                qavat = "🏠 1-qavat" if x["qavat"] == 1 else "🏢 2-qavat"
                narx = format_narx(x["narx"])
                matn += f"{qavat} | {x['nomi']} | {x['sigim']} 👤 | {narx} so'm\n"
            matn += "\n👇 Xonani tanlang:"
            bot.send_message(cid, matn, parse_mode="Markdown", reply_markup=xonalar_inline(sana))
        except ValueError:
            bot.send_message(cid, "⚠️ Format to'g'ri emas. Masalan: *15.06.2025*", parse_mode="Markdown")
        return

    if step == "ism":
        state["ism"] = msg.text.strip()
        state["step"] = "telefon"
        bot.send_message(cid, "📞 *Telefon raqamingizni kiriting:*\n\nMasalan: +998901234567", parse_mode="Markdown")
        return

    if step == "telefon":
        state["telefon"] = msg.text.strip()
        x = XONALAR[state["xona_id"]]
        narx = format_narx(x["narx"])
        matn = (
            f"📋 *Bron ma'lumotlari:*\n\n"
            f"👤 Ism: {state['ism']}\n"
            f"📞 Telefon: {state['telefon']}\n"
            f"📅 Sana: {state['sana']}\n"
            f"👥 Kishi soni: {state['kishi']}\n"
            f"🛏 Xona: {x['nomi']} ({x['sigim']} kishilik)\n"
            f"💰 Narx: {narx} so'm\n\n"
            f"✅ Tasdiqlaysizmi?"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ Ha, tasdiqlash", callback_data="tasdiq_ha"),
            types.InlineKeyboardButton("❌ Bekor", callback_data="tasdiq_yoq")
        )
        bot.send_message(cid, matn, parse_mode="Markdown", reply_markup=kb)
        state["step"] = "tasdiq"
        return

if __name__ == "__main__":
    print("✅ Tog' Tagi Resort Bot ishga tushdi!")
    bot.infinity_polling()
