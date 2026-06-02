import os
import logging
import random
import string
from datetime import datetime, timedelta
from io import BytesIO
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [8886176055, 7323184602]
TELEFON1 = "+998993342035"
TELEFON2 = "+998704902025"
INSTAGRAM = "https://instagram.com/togtagi"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(BOT_TOKEN)

bot.set_my_commands([
    types.BotCommand("start", "Bosh menyu"),
    types.BotCommand("bron", "Xona bron qilish"),
    types.BotCommand("xonalar", "Bo'sh xonalar"),
    types.BotCommand("xizmatlar", "Xizmatlar"),
    types.BotCommand("manzil", "Manzil"),
    types.BotCommand("boglanish", "Bog'lanish"),
])

# ==================== BAZA ====================
XONALAR = {
    1:  {"nomi": "1-xona",  "qavat": 1, "sigim": 3, "narx": 300000, "band": {}, "rasmlar": []},
    2:  {"nomi": "2-xona",  "qavat": 1, "sigim": 3, "narx": 300000, "band": {}, "rasmlar": []},
    3:  {"nomi": "3-xona",  "qavat": 1, "sigim": 7, "narx": 700000, "band": {}, "rasmlar": []},
    4:  {"nomi": "4-xona",  "qavat": 1, "sigim": 7, "narx": 700000, "band": {}, "rasmlar": []},
    5:  {"nomi": "5-xona",  "qavat": 2, "sigim": 3, "narx": 300000, "band": {}, "rasmlar": []},
    6:  {"nomi": "6-xona",  "qavat": 2, "sigim": 3, "narx": 300000, "band": {}, "rasmlar": []},
    7:  {"nomi": "7-xona",  "qavat": 2, "sigim": 3, "narx": 300000, "band": {}, "rasmlar": []},
    8:  {"nomi": "8-xona",  "qavat": 2, "sigim": 3, "narx": 300000, "band": {}, "rasmlar": []},
    9:  {"nomi": "9-xona",  "qavat": 2, "sigim": 3, "narx": 300000, "band": {}, "rasmlar": []},
    10: {"nomi": "10-xona", "qavat": 2, "sigim": 3, "narx": 300000, "band": {}, "rasmlar": []},
}
JAMI_JOY = 38
BRONLAR = {}
MIJOZLAR = {}
BLOKLANGAN = []
MEDIA = {"photos": [], "videos": []}
user_state = {}

# ==================== YORDAMCHI ====================

def is_admin(uid):
    return uid in ADMIN_IDS

def format_narx(n):
    return f"{n:,}".replace(",", " ")

def bron_id_gen():
    harf = random.choice(string.ascii_uppercase)
    raqam = random.randint(100, 999)
    return f"{harf}{raqam}"

def xona_band_mi(xid, sana):
    return sana in XONALAR[xid]["band"]

def xona_kunlar_band(xid, bosh_sana, kunlar):
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    for i in range(kunlar):
        sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
        if xona_band_mi(xid, sana):
            return True
    return False

def band_qil(xid, bosh_sana, kunlar, bron_id):
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    for i in range(kunlar):
        sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
        XONALAR[xid]["band"][sana] = {"bron_id": bron_id}

def bosh_qil(xid, bosh_sana, kunlar):
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    for i in range(kunlar):
        sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
        XONALAR[xid]["band"].pop(sana, None)

def mos_kombinatsiya(kishi, guruh, sana, kunlar=1):
    bosh = []
    for xid, x in XONALAR.items():
        if not xona_kunlar_band(xid, sana, kunlar):
            bosh.append((xid, x))
    if not bosh:
        return []
    # Bitta xona yetarlimi?
    for xid, x in sorted(bosh, key=lambda a: a[1]["sigim"]):
        if x["sigim"] >= kishi:
            return [(xid, x)]
    # Kombinatsiya: guruhga qarab afzal qavat
    afzal_qavat = 1 if guruh == "oila" else 2
    afzal = sorted([(xid, x) for xid, x in bosh if x["qavat"] == afzal_qavat],
                   key=lambda a: a[1]["sigim"], reverse=True)
    boshqa = sorted([(xid, x) for xid, x in bosh if x["qavat"] != afzal_qavat],
                    key=lambda a: a[1]["sigim"], reverse=True)
    tartiblangan = afzal + boshqa
    tanlangan = []
    jami = 0
    for xid, x in tartiblangan:
        if jami >= kishi:
            break
        tanlangan.append((xid, x))
        jami += x["sigim"]
    return tanlangan if jami >= kishi else []

def xato_xabar(cid):
    bot.send_message(cid,
        f"⚠️ Xatolik yuz berdi.\n\nTelefon orqali bog'laning:\n"
        f"📞 {TELEFON1}\n📞 {TELEFON2}",
        reply_markup=asosiy_menu())

def sana_tugmalari():
    kb = types.InlineKeyboardMarkup(row_width=5)
    bugun = datetime.now().date()
    tugmalar = []
    for i in range(30):
        kun = bugun + timedelta(days=i)
        sana_str = kun.strftime("%d.%m.%Y")
        kun_qisqa = kun.strftime("%d/%m")
        tugmalar.append(types.InlineKeyboardButton(kun_qisqa, callback_data=f"sana_{sana_str}"))
    kb.add(*tugmalar)
    return kb

def kunlar_tugmalari():
    kb = types.InlineKeyboardMarkup(row_width=5)
    tugmalar = []
    for i in range(1, 16):
        tugmalar.append(types.InlineKeyboardButton(f"{i} kun", callback_data=f"kun_{i}"))
    kb.add(*tugmalar)
    return kb

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
        types.KeyboardButton("🏨 Xonalar boshqaruvi"),
        types.KeyboardButton("📋 Bronlar ro'yxati"),
        types.KeyboardButton("👥 Mijozlar bazasi"),
        types.KeyboardButton("➕ Tezkor bron"),
        types.KeyboardButton("📸 Umumiy rasm yuklash"),
        types.KeyboardButton("🎥 Video yuklash"),
        types.KeyboardButton("📄 Hisobot"),
        types.KeyboardButton("🔙 Asosiy menyu")
    )
    return kb

def xonalar_boshqaruv_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for xid, x in XONALAR.items():
        qavat = "🏠" if x["qavat"] == 1 else "🏢"
        rasmlar = f"📸{len(x['rasmlar'])}" if x["rasmlar"] else ""
        kb.add(types.InlineKeyboardButton(
            f"{qavat} {x['nomi']} ({x['sigim']} kishi) {rasmlar}",
            callback_data=f"admin_xona_{xid}"
        ))
    return kb

def xona_admin_kb(xid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📅 Bronlar", callback_data=f"ax_bronlar_{xid}"),
        types.InlineKeyboardButton("🔴 Band qilish", callback_data=f"ax_band_{xid}"),
        types.InlineKeyboardButton("🟢 Bo'sh qilish", callback_data=f"ax_bosh_{xid}"),
        types.InlineKeyboardButton("📸 Rasm yuklash", callback_data=f"ax_rasm_{xid}"),
        types.InlineKeyboardButton("🔙 Orqaga", callback_data="ax_back")
    )
    return kb

# ==================== START ====================

@bot.message_handler(commands=["start", "bron", "xonalar", "xizmatlar", "manzil", "boglanish"])
def start(msg):
    if msg.text and msg.text.startswith("/bron"):
        bron_start(msg); return
    if msg.text and msg.text.startswith("/xonalar"):
        bosh_xonalar(msg); return
    if msg.text and msg.text.startswith("/xizmatlar"):
        xizmatlar(msg); return
    if msg.text and msg.text.startswith("/manzil"):
        manzil(msg); return
    if msg.text and msg.text.startswith("/boglanish"):
        boglanish(msg); return
    user_state.pop(msg.chat.id, None)
    bot.send_message(msg.chat.id,
        "🏔 *Tog' Tagi Resort*\n\n"
        "Shohimardon tog'lari bag'rida,\nsof havo va go'zal tabiat qo'ynida dam oling!\n\n"
        "🌊 Soy bo'yida  |  💦 Sharshara\n"
        "🍽 Oshxona  |  🔥 Mangal & Shashlik\n"
        "🛖 Tapchanlar  |  🚗 Bepul parking\n\n"
        "📍 Ko'lqubondan 300 metr pastda\n\n"
        f"📞 {TELEFON1}  |  {TELEFON2}",
        parse_mode="Markdown", reply_markup=asosiy_menu())

@bot.message_handler(commands=["admin"])
def admin_panel(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "❌ Ruxsat yo'q")
        return
    user_state[msg.chat.id] = {"mode": "admin"}
    bot.send_message(msg.chat.id, "👨‍💼 *Admin panel*",
                     parse_mode="Markdown", reply_markup=admin_menu())

# ==================== MIJOZLAR ====================

@bot.message_handler(func=lambda m: m.text == "🛏 Xona bron qilish")
def bron_start(msg):
    if msg.from_user.id in BLOKLANGAN:
        bot.send_message(msg.chat.id, f"❌ Bog'laning: {TELEFON1}")
        return
    user_state[msg.chat.id] = {"step": "kishi"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    for i in range(1, 11):
        kb.add(types.KeyboardButton(str(i)))
    kb.add(types.KeyboardButton("🏠 Bosh menyu"))
    bot.send_message(msg.chat.id,
        "👥 *Nechta kishi kelmoqchisiz?*\n\nRaqamni tanlang yoki yozing:",
        parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📅 Bo'sh xonalar")
def bosh_xonalar(msg):
    user_state[msg.chat.id] = {"step": "bosh_kishi"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    for i in range(1, 11):
        kb.add(types.KeyboardButton(str(i)))
    kb.add(types.KeyboardButton("🏠 Bosh menyu"))
    bot.send_message(msg.chat.id,
        "📅 *Bo'sh xonalarni ko'rish*\n\nNechta kishi kelmoqchisiz?",
        parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "🖼 Galereya")
def galereya(msg):
    if not MEDIA["photos"] and not MEDIA["videos"]:
        bot.send_message(msg.chat.id, "📸 Hozircha rasm/video yo'q.\nTez orada qo'shamiz!")
        return
    bot.send_message(msg.chat.id, "🖼 *Tog' Tagi Resort — Galereya:*", parse_mode="Markdown")
    for photo_id in MEDIA["photos"][:10]:
        try: bot.send_photo(msg.chat.id, photo_id)
        except: pass
    for video_id in MEDIA["videos"][:5]:
        try: bot.send_video(msg.chat.id, video_id)
        except: pass

@bot.message_handler(func=lambda m: m.text == "🌿 Xizmatlar")
def xizmatlar(msg):
    bot.send_message(msg.chat.id,
        "🌿 *Tog' Tagi Resort Xizmatlari:*\n\n"
        "🌊 Soy bo'yi\n"
        "💦 Sharshara\n"
        "🍽 Oshxona *(mijozlar o'zlari pishiradi)*\n"
        "🔥 Mangal\n"
        "🥩 Shashlik\n"
        "📶 WiFi\n"
        "📺 Televizor\n"
        "🛏 Qulay yotoq joylar\n"
        "🛖 Tapchanlar\n"
        "🚗 Bepul parking\n"
        "🌿 Yashil tabiat\n\n"
        f"📞 {TELEFON1}\n📞 {TELEFON2}",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📍 Manzil")
def manzil(msg):
    bot.send_message(msg.chat.id,
        "📍 *Tog' Tagi Resort manzili:*\n\n"
        "🏘 Shohimardon, Farg'ona viloyati\n"
        "📌 Ko'lqubondan 300 metr pastda\n\n"
        f"📞 {TELEFON1}\n📞 {TELEFON2}",
        parse_mode="Markdown")
    bot.send_location(msg.chat.id, latitude=39.961311, longitude=71.836921)

@bot.message_handler(func=lambda m: m.text == "📞 Bog'lanish")
def boglanish(msg):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(f"📞 {TELEFON1}", url=f"tel:{TELEFON1}"),
        types.InlineKeyboardButton(f"📞 {TELEFON2}", url=f"tel:{TELEFON2}"),
        types.InlineKeyboardButton("📸 Instagram", url=INSTAGRAM),
        types.InlineKeyboardButton("🛏 Xona bron qilish", callback_data="bron_start")
    )
    bot.send_message(msg.chat.id,
        "📞 *Bog'lanish:*\n\n"
        f"📱 {TELEFON1}\n"
        f"📱 {TELEFON2}\n"
        f"📸 Instagram: @togtagi\n\n"
        "⏰ Ish vaqti: 24/7",
        parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "🏠 Bosh menyu")
def bosh_menyu(msg):
    user_state.pop(msg.chat.id, None)
    bot.send_message(msg.chat.id, "Bosh menyu 👇", reply_markup=asosiy_menu())

# ==================== ADMIN ====================

@bot.message_handler(func=lambda m: m.text == "🔙 Asosiy menyu" and is_admin(m.from_user.id))
def admin_back(msg):
    user_state.pop(msg.chat.id, None)
    bot.send_message(msg.chat.id, "Asosiy menyu", reply_markup=asosiy_menu())

@bot.message_handler(func=lambda m: m.text == "🏨 Xonalar boshqaruvi" and is_admin(m.from_user.id))
def xonalar_boshqaruvi(msg):
    bot.send_message(msg.chat.id, "🏨 *Xonalarni tanlang:*",
                     parse_mode="Markdown", reply_markup=xonalar_boshqaruv_menu())

@bot.message_handler(func=lambda m: m.text == "📋 Bronlar ro'yxati" and is_admin(m.from_user.id))
def bronlar_royxati(msg):
    if not BRONLAR:
        bot.send_message(msg.chat.id, "Hozircha bron yo'q", reply_markup=admin_menu())
        return
    matn = "📋 *So'nggi bronlar:*\n\n"
    for bid, b in list(BRONLAR.items())[-15:]:
        matn += (f"🎫 *#{bid}* | {b['xona']}\n"
                 f"👤 {b['ism']} | 📞 {b['telefon']}\n"
                 f"📅 {b['sana']} | {b['kunlar']} kun | 👥 {b['kishi']} kishi\n"
                 f"💰 {format_narx(b['narx'])} so'm\n\n")
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "📄 Hisobot" and is_admin(m.from_user.id))
def hisobot(msg):
    if not BRONLAR:
        bot.send_message(msg.chat.id, "Hozircha bron yo'q")
        return
    matn = "BRONLAR RO'YXATI\n" + "="*40 + "\n\n"
    for bid, b in BRONLAR.items():
        matn += (f"#{bid} | {b['xona']}\n"
                 f"Ism: {b['ism']}\nTel: {b['telefon']}\n"
                 f"Sana: {b['sana']} | {b['kunlar']} kun\n"
                 f"Kishi: {b['kishi']} | Narx: {format_narx(b['narx'])} som\n"
                 + "-"*30 + "\n")
    buf = BytesIO(matn.encode("utf-8"))
    buf.name = "bronlar.txt"
    bot.send_document(msg.chat.id, buf, caption="📄 Bronlar ro'yxati")

@bot.message_handler(func=lambda m: m.text == "👥 Mijozlar bazasi" and is_admin(m.from_user.id))
def mijozlar_bazasi(msg):
    user_state[msg.chat.id] = {"step": "admin_mijoz_qidir", "mode": "admin"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Admin menyu")
    bot.send_message(msg.chat.id, "👥 Mijoz telefon raqamini kiriting:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "➕ Tezkor bron" and is_admin(m.from_user.id))
def tezkor_bron(msg):
    user_state[msg.chat.id] = {"step": "admin_tezkor_kishi", "mode": "admin", "ab": {}}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    for i in range(1, 11):
        kb.add(types.KeyboardButton(str(i)))
    kb.add("🔙 Admin menyu")
    bot.send_message(msg.chat.id, "➕ *Tezkor bron*\n\nNechta kishi?",
                     parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📸 Umumiy rasm yuklash" and is_admin(m.from_user.id))
def umumiy_rasm(msg):
    user_state[msg.chat.id] = {"step": "admin_umumiy_rasm", "mode": "admin"}
    bot.send_message(msg.chat.id, "📸 Umumiy rasmlarni yuboring.\n/done — tugallash")

@bot.message_handler(func=lambda m: m.text == "🎥 Video yuklash" and is_admin(m.from_user.id))
def admin_video(msg):
    user_state[msg.chat.id] = {"step": "admin_video", "mode": "admin"}
    bot.send_message(msg.chat.id, "🎥 Video yuboring.\n/done — tugallash")

@bot.message_handler(func=lambda m: m.text == "🔙 Admin menyu" and is_admin(m.from_user.id))
def admin_menyu_back(msg):
    user_state[msg.chat.id] = {"mode": "admin"}
    bot.send_message(msg.chat.id, "Admin panel 👇", reply_markup=admin_menu())

@bot.message_handler(commands=["done"])
def cmd_done(msg):
    if not is_admin(msg.from_user.id):
        return
    state = user_state.get(msg.chat.id, {})
    xid = state.get("rasm_xona_id")
    if xid:
        bot.send_message(msg.chat.id, f"✅ {XONALAR[xid]['nomi']} rasmlari saqlandi!", reply_markup=admin_menu())
    else:
        bot.send_message(msg.chat.id, "✅ Saqlandi!", reply_markup=admin_menu())
    user_state[msg.chat.id] = {"mode": "admin"}

@bot.message_handler(content_types=["photo"])
def photo_handler(msg):
    state = user_state.get(msg.chat.id, {})
    if not is_admin(msg.from_user.id):
        return
    step = state.get("step")
    if step == "admin_umumiy_rasm":
        MEDIA["photos"].append(msg.photo[-1].file_id)
        bot.send_message(msg.chat.id, f"✅ Saqlandi! Jami: {len(MEDIA['photos'])} ta\n/done — tugallash")
    elif step == "admin_xona_rasm":
        xid = state.get("rasm_xona_id")
        if xid:
            XONALAR[xid]["rasmlar"].append(msg.photo[-1].file_id)
            bot.send_message(msg.chat.id,
                f"✅ {XONALAR[xid]['nomi']} rasmi saqlandi! Jami: {len(XONALAR[xid]['rasmlar'])} ta\n/done — tugallash")

@bot.message_handler(content_types=["video"])
def video_handler(msg):
    state = user_state.get(msg.chat.id, {})
    if is_admin(msg.from_user.id) and state.get("step") == "admin_video":
        MEDIA["videos"].append(msg.video.file_id)
        bot.send_message(msg.chat.id, f"✅ Video saqlandi! Jami: {len(MEDIA['videos'])} ta\n/done — tugallash")

@bot.message_handler(content_types=["contact"])
def contact_handler(msg):
    state = user_state.get(msg.chat.id, {})
    if state.get("step") == "telefon":
        telefon = msg.contact.phone_number
        if not telefon.startswith("+"): telefon = "+" + telefon
        state["telefon"] = telefon
        user_state[msg.chat.id] = state
        _tasdiqlash_yuborim(msg.chat.id)

# ==================== CALLBACK ====================

@bot.callback_query_handler(func=lambda c: c.data == "bron_start")
def cb_bron_start(call):
    user_state[call.message.chat.id] = {"step": "kishi"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    for i in range(1, 11):
        kb.add(types.KeyboardButton(str(i)))
    kb.add(types.KeyboardButton("🏠 Bosh menyu"))
    bot.send_message(call.message.chat.id, "👥 *Nechta kishi kelmoqchisiz?*",
                     parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("sana_"))
def cb_sana(call):
    cid = call.message.chat.id
    sana = call.data.replace("sana_", "")
    state = user_state.get(cid, {})

    # Admin tezkor bron uchun
    if is_admin(call.from_user.id) and state.get("step") in ["admin_tezkor_sana", "ax_band_sana", "ax_bosh_sana"]:
        step = state.get("step")
        if step == "admin_tezkor_sana":
            state["ab"]["sana"] = sana
            state["step"] = "admin_tezkor_kunlar"
            user_state[cid] = state
            bot.send_message(cid, f"📅 Sana: {sana}\n\nNecha kun turadi?", reply_markup=kunlar_tugmalari())
        elif step == "ax_band_sana":
            state["ax_sana"] = sana
            state["step"] = "ax_band_kunlar"
            user_state[cid] = state
            bot.send_message(cid, f"📅 {sana}\n\nNecha kun band qilinsin?", reply_markup=kunlar_tugmalari())
        elif step == "ax_bosh_sana":
            state["ax_sana"] = sana
            state["step"] = "ax_bosh_kunlar"
            user_state[cid] = state
            bot.send_message(cid, f"📅 {sana}\n\nNecha kun bo'sh qilinsin?", reply_markup=kunlar_tugmalari())
        bot.answer_callback_query(call.id)
        return

    # Mijoz uchun
    state["sana"] = sana
    state["step"] = "kunlar"
    user_state[cid] = state
    bot.edit_message_text(
        f"📅 Sana: *{sana}*\n\nNecha kun turmoqchisiz?",
        cid, call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kunlar_tugmalari()
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("kun_"))
def cb_kun(call):
    cid = call.message.chat.id
    kunlar = int(call.data.replace("kun_", ""))
    state = user_state.get(cid, {})

    # Admin tezkor bron
    if is_admin(call.from_user.id) and state.get("step") in ["admin_tezkor_kunlar", "ax_band_kunlar", "ax_bosh_kunlar"]:
        step = state.get("step")
        if step == "admin_tezkor_kunlar":
            state["ab"]["kunlar"] = kunlar
            state["step"] = "admin_tezkor_xona"
            user_state[cid] = state
            sana = state["ab"]["sana"]
            kishi = state["ab"].get("kishi", 1)
            guruh = state["ab"].get("guruh", "oila")
            kombinatsiya = mos_kombinatsiya(kishi, guruh, sana, kunlar)
            if not kombinatsiya:
                bot.send_message(cid, f"❌ {sana} sanasida bo'sh xona yo'q")
                bot.answer_callback_query(call.id)
                return
            matn = f"📅 {sana} | {kunlar} kun | 👥 {kishi} kishi\n\n✅ *Mos xonalar:*\n"
            kb = types.InlineKeyboardMarkup(row_width=1)
            for xid, x in kombinatsiya:
                narx = format_narx(x["narx"] * kunlar)
                kb.add(types.InlineKeyboardButton(
                    f"🛏 {x['nomi']} | {x['sigim']} kishi | {narx} so'm",
                    callback_data=f"admin_tezkor_xona_{xid}"
                ))
            kb.add(types.InlineKeyboardButton("📋 Barcha bo'sh xonalar", callback_data="admin_tezkor_barchasi"))
            bot.send_message(cid, matn, parse_mode="Markdown", reply_markup=kb)
        elif step == "ax_band_kunlar":
            xid = state["ax_xid"]
            sana = state["ax_sana"]
            band_qil(xid, sana, kunlar, "admin")
            user_state[cid] = {"mode": "admin"}
            bot.send_message(cid, f"✅ {XONALAR[xid]['nomi']} — {sana} dan {kunlar} kun BAND qilindi",
                             reply_markup=admin_menu())
        elif step == "ax_bosh_kunlar":
            xid = state["ax_xid"]
            sana = state["ax_sana"]
            bosh_qil(xid, sana, kunlar)
            user_state[cid] = {"mode": "admin"}
            bot.send_message(cid, f"✅ {XONALAR[xid]['nomi']} — {sana} dan {kunlar} kun BO'SH qilindi",
                             reply_markup=admin_menu())
        bot.answer_callback_query(call.id)
        return

    # Mijoz uchun
    state["kunlar"] = kunlar
    state["step"] = "xona_tanlash"
    user_state[cid] = state

    sana = state.get("sana", "")
    kishi = state.get("kishi", 1)
    guruh = state.get("guruh", "oila")

    kombinatsiya = mos_kombinatsiya(kishi, guruh, sana, kunlar)

    if not kombinatsiya:
        bot.edit_message_text(
            f"❌ *{sana}* sanasida {kishi} kishiga mos bo'sh xona yo'q.\n\n"
            f"Boshqa sana tanlang yoki bog'laning:\n📞 {TELEFON1}",
            cid, call.message.message_id,
            parse_mode="Markdown",
            reply_markup=sana_tugmalari()
        )
        bot.answer_callback_query(call.id)
        return

    jami_narx = sum(x["narx"] for _, x in kombinatsiya) * kunlar
    xona_nomlari = " + ".join(x["nomi"] for _, x in kombinatsiya)

    matn = f"📅 *{sana}* | {kunlar} kun | 👥 *{kishi} kishi*\n\n"
    matn += "✨ *Sizga mos variant:*\n\n"
    for xid, x in kombinatsiya:
        qavat = "🏠" if x["qavat"] == 1 else "🏢"
        narx = format_narx(x["narx"] * kunlar)
        matn += f"{qavat} *{x['nomi']}* | 👥 {x['sigim']} kishi\n💰 {narx} so'm ({kunlar} kun)\n\n"
    if len(kombinatsiya) > 1:
        matn += f"💰 *Jami: {format_narx(jami_narx)} so'm*\n\n"
    matn += "👇 Tanlang:"

    kb = types.InlineKeyboardMarkup(row_width=1)
    if len(kombinatsiya) == 1:
        xid = kombinatsiya[0][0]
        kb.add(types.InlineKeyboardButton(
            f"✅ {xona_nomlari} — {format_narx(jami_narx)} so'm",
            callback_data=f"kombina_{'_'.join(str(x[0]) for x in kombinatsiya)}_{sana}_{kunlar}"
        ))
    else:
        kb.add(types.InlineKeyboardButton(
            f"✅ Barcha ({xona_nomlari}) — {format_narx(jami_narx)} so'm",
            callback_data=f"kombina_{'_'.join(str(x[0]) for x in kombinatsiya)}_{sana}_{kunlar}"
        ))
    kb.add(types.InlineKeyboardButton("📋 Barcha bo'sh xonalar", callback_data=f"barcha_{sana}_{kunlar}"))

    bot.edit_message_text(matn, cid, call.message.message_id,
                          parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("barcha_"))
def cb_barcha(call):
    cid = call.message.chat.id
    parts = call.data.split("_")
    sana = parts[1]
    kunlar = int(parts[2])
    kb = types.InlineKeyboardMarkup(row_width=1)
    for xid, x in XONALAR.items():
        if xona_kunlar_band(xid, sana, kunlar):
            continue
        qavat = "🏠" if x["qavat"] == 1 else "🏢"
        narx = format_narx(x["narx"] * kunlar)
        kb.add(types.InlineKeyboardButton(
            f"{qavat} {x['nomi']} | {x['sigim']} 👤 | {narx} so'm",
            callback_data=f"kombina_{xid}_{sana}_{kunlar}"
        ))
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"kun_{kunlar}"))
    bot.edit_message_text(f"📅 {sana} | {kunlar} kun\n\n📋 *Barcha bo'sh xonalar:*",
                          cid, call.message.message_id,
                          parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("kombina_"))
def cb_kombina(call):
    cid = call.message.chat.id
    parts = call.data.split("_")
    kunlar = int(parts[-1])
    sana = parts[-2]
    xid_list = [int(x) for x in parts[1:-2]]

    state = user_state.get(cid, {})
    state["xona_ids"] = xid_list
    state["sana"] = sana
    state["kunlar"] = kunlar
    state["step"] = "ism"

    xonalar_info = [XONALAR[xid] for xid in xid_list]
    jami_narx = sum(x["narx"] for x in xonalar_info) * kunlar
    xona_nomi = " + ".join(x["nomi"] for x in xonalar_info)
    state["xona_nomi"] = xona_nomi
    state["jami_narx"] = jami_narx
    user_state[cid] = state

    # Xona rasmlarini yuborish
    for xid in xid_list:
        rasmlar = XONALAR[xid]["rasmlar"]
        if rasmlar:
            bot.send_message(cid, f"📸 *{XONALAR[xid]['nomi']}* rasmlari:", parse_mode="Markdown")
            for r in rasmlar[:5]:
                try: bot.send_photo(cid, r)
                except: pass

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("🏠 Bosh menyu"))
    bot.edit_message_text(
        f"✅ *{xona_nomi}* tanlandi\n"
        f"📅 {sana} | {kunlar} kun\n"
        f"💰 {format_narx(jami_narx)} so'm\n\n"
        f"👤 *Ismingizni kiriting:*",
        cid, call.message.message_id, parse_mode="Markdown"
    )
    bot.send_message(cid, "👇 Ismingizni yozing:", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_tasdiq_"))
def cb_admin_tasdiq(call):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    action = parts[2]
    bron_id = parts[3]

    if bron_id not in BRONLAR:
        bot.answer_callback_query(call.id, "Bron topilmadi")
        return

    b = BRONLAR[bron_id]

    if action == "ha":
        for xid in b["xona_ids"]:
            band_qil(xid, b["sana"], b["kunlar"], bron_id)
        BRONLAR[bron_id]["tasdiqlangan"] = True

        try:
            bot.send_message(b["user_id"],
                f"✅ *Broningiz tasdiqlandi! #{bron_id}*\n\n"
                f"🛏 {b['xona']}\n"
                f"📅 {b['sana']} | {b['kunlar']} kun\n"
                f"👥 {b['kishi']} kishi\n"
                f"💰 {format_narx(b['narx'])} so'm\n\n"
                f"📞 {TELEFON1}",
                parse_mode="Markdown")
        except: pass

        bot.edit_message_text(
            f"✅ Bron #{bron_id} TASDIQLANDI!\n{b['ism']} — {b['xona']} — {b['sana']}",
            call.message.chat.id, call.message.message_id
        )
    else:
        BRONLAR.pop(bron_id, None)
        try:
            bot.send_message(b["user_id"],
                f"❌ Bron #{bron_id} rad etildi.\n\nBog'laning: {TELEFON1}")
        except: pass
        bot.edit_message_text(
            f"❌ Bron #{bron_id} RAD ETILDI",
            call.message.chat.id, call.message.message_id
        )
    bot.answer_callback_query(call.id)

# ==================== ADMIN XONA BOSHQARUVI ====================

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_xona_"))
def cb_admin_xona(call):
    if not is_admin(call.from_user.id): return
    xid = int(call.data.replace("admin_xona_", ""))
    x = XONALAR[xid]
    bugun = datetime.now().strftime("%d.%m.%Y")
    h = "🔴 Band" if xona_band_mi(xid, bugun) else "🟢 Bo'sh"
    matn = (f"🛏 *{x['nomi']}*\n"
            f"{'🏠 1-qavat' if x['qavat']==1 else '🏢 2-qavat'} | 👥 {x['sigim']} kishi\n"
            f"💰 {format_narx(x['narx'])} so'm | Bugun: {h}\n"
            f"📸 Rasmlar: {len(x['rasmlar'])} ta")
    bot.edit_message_text(matn, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=xona_admin_kb(xid))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ax_bronlar_"))
def cb_ax_bronlar(call):
    if not is_admin(call.from_user.id): return
    xid = int(call.data.replace("ax_bronlar_", ""))
    xona_bronlar = {bid: b for bid, b in BRONLAR.items() if xid in b.get("xona_ids", [])}
    matn = f"🛏 *{XONALAR[xid]['nomi']}* bronlari:\n\n"
    if xona_bronlar:
        for bid, b in list(xona_bronlar.items())[-8:]:
            matn += f"#{bid} | {b['sana']} | {b['kunlar']} kun\n👤 {b['ism']} | 📞 {b['telefon']}\n\n"
    else:
        matn += "Hozircha bron yo'q\n\n"
    matn += "📅 *15 kunlik holat:*\n"
    bugun = datetime.now().date()
    for i in range(15):
        kun = bugun + timedelta(days=i)
        sana_str = kun.strftime("%d.%m.%Y")
        kun_q = kun.strftime("%d/%m")
        h = "🔴" if xona_band_mi(xid, sana_str) else "🟢"
        matn += f"{h}{kun_q} "
        if (i+1) % 5 == 0: matn += "\n"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"admin_xona_{xid}"))
    bot.edit_message_text(matn, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ax_band_"))
def cb_ax_band(call):
    if not is_admin(call.from_user.id): return
    xid = int(call.data.replace("ax_band_", ""))
    user_state[call.message.chat.id] = {"step": "ax_band_sana", "mode": "admin", "ax_xid": xid}
    bot.send_message(call.message.chat.id,
        f"🔴 *{XONALAR[xid]['nomi']}* band qilish\n\n📅 Boshlanish sanasini tanlang:",
        parse_mode="Markdown", reply_markup=sana_tugmalari())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ax_bosh_"))
def cb_ax_bosh(call):
    if not is_admin(call.from_user.id): return
    xid = int(call.data.replace("ax_bosh_", ""))
    user_state[call.message.chat.id] = {"step": "ax_bosh_sana", "mode": "admin", "ax_xid": xid}
    bot.send_message(call.message.chat.id,
        f"🟢 *{XONALAR[xid]['nomi']}* bo'sh qilish\n\n📅 Boshlanish sanasini tanlang:",
        parse_mode="Markdown", reply_markup=sana_tugmalari())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ax_rasm_"))
def cb_ax_rasm(call):
    if not is_admin(call.from_user.id): return
    xid = int(call.data.replace("ax_rasm_", ""))
    user_state[call.message.chat.id] = {"step": "admin_xona_rasm", "mode": "admin", "rasm_xona_id": xid}
    bot.send_message(call.message.chat.id,
        f"📸 *{XONALAR[xid]['nomi']}* uchun rasmlar yuboring.\n/done — tugallash",
        parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "ax_back")
def cb_ax_back(call):
    if not is_admin(call.from_user.id): return
    bot.edit_message_text("🏨 *Xonalarni tanlang:*", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=xonalar_boshqaruv_menu())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_tezkor_xona_"))
def cb_tezkor_xona(call):
    if not is_admin(call.from_user.id): return
    cid = call.message.chat.id
    xid = int(call.data.replace("admin_tezkor_xona_", ""))
    state = user_state.get(cid, {})
    ab = state.get("ab", {})
    state["step"] = "admin_tezkor_ism"
    state["ab"]["xona_ids"] = [xid]
    state["ab"]["xona_nomi"] = XONALAR[xid]["nomi"]
    state["ab"]["narx"] = XONALAR[xid]["narx"] * ab.get("kunlar", 1)
    user_state[cid] = state
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Admin menyu")
    bot.send_message(cid, f"✅ {XONALAR[xid]['nomi']} tanlandi\n\nMijoz ismi:", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "admin_tezkor_barchasi")
def cb_tezkor_barchasi(call):
    if not is_admin(call.from_user.id): return
    cid = call.message.chat.id
    state = user_state.get(cid, {})
    ab = state.get("ab", {})
    sana = ab.get("sana", "")
    kunlar = ab.get("kunlar", 1)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for xid, x in XONALAR.items():
        if not xona_kunlar_band(xid, sana, kunlar):
            narx = format_narx(x["narx"] * kunlar)
            kb.add(types.InlineKeyboardButton(
                f"{'🏠' if x['qavat']==1 else '🏢'} {x['nomi']} | {x['sigim']} kishi | {narx} so'm",
                callback_data=f"admin_tezkor_xona_{xid}"
            ))
    bot.edit_message_text(f"📋 *Barcha bo'sh xonalar:*\n{sana} | {kunlar} kun",
                          cid, call.message.message_id,
                          parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("block_"))
def cb_block(call):
    if not is_admin(call.from_user.id): return
    uid = int(call.data.replace("block_", ""))
    if uid not in BLOKLANGAN: BLOKLANGAN.append(uid)
    bot.edit_message_text(f"🚫 {uid} bloklandi", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "Bloklandi!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("unblock_"))
def cb_unblock(call):
    if not is_admin(call.from_user.id): return
    uid = int(call.data.replace("unblock_", ""))
    if uid in BLOKLANGAN: BLOKLANGAN.remove(uid)
    bot.edit_message_text(f"✅ {uid} blokdan chiqarildi", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "Blok ochildi!")

# ==================== TASDIQLASH ====================

def _tasdiqlash_yuborim(cid):
    state = user_state.get(cid, {})
    try:
        xid_list = state["xona_ids"]
        xona_nomi = state["xona_nomi"]
        jami_narx = state["jami_narx"]
        narx = format_narx(jami_narx)
        matn = (
            f"📋 *Bron ma'lumotlari:*\n\n"
            f"👤 {state['ism']}\n"
            f"📞 {state['telefon']}\n"
            f"📅 {state['sana']} | {state['kunlar']} kun\n"
            f"👥 {state['kishi']} kishi\n"
            f"🛏 {xona_nomi}\n"
            f"💰 {narx} so'm\n\n"
            f"✅ Tasdiqlaysizmi?"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="mijoz_tasdiq_ha"),
            types.InlineKeyboardButton("❌ Bekor", callback_data="mijoz_tasdiq_yoq")
        )
        bot.send_message(cid, matn, parse_mode="Markdown", reply_markup=kb)
        state["step"] = "tasdiq"
        user_state[cid] = state
    except Exception as e:
        logging.error(e)
        xato_xabar(cid)

@bot.callback_query_handler(func=lambda c: c.data.startswith("mijoz_tasdiq_"))
def cb_mijoz_tasdiq(call):
    cid = call.message.chat.id
    if call.data == "mijoz_tasdiq_ha":
        state = user_state.get(cid, {})
        try:
            bron_id = bron_id_gen()
            while bron_id in BRONLAR:
                bron_id = bron_id_gen()

            b = {
                "ism": state["ism"],
                "telefon": state["telefon"],
                "sana": state["sana"],
                "kunlar": state["kunlar"],
                "kishi": state["kishi"],
                "xona": state["xona_nomi"],
                "xona_ids": state["xona_ids"],
                "narx": state["jami_narx"],
                "tasdiqlangan": False,
                "user_id": call.from_user.id,
                "username": call.from_user.username or "yoq"
            }
            BRONLAR[bron_id] = b

            # Mijozlar bazasi
            MIJOZLAR[state["telefon"]] = {
                "ism": state["ism"],
                "telefon": state["telefon"],
                "user_id": call.from_user.id,
                "username": call.from_user.username or "yoq",
                "bronlar": MIJOZLAR.get(state["telefon"], {}).get("bronlar", []) + [bron_id]
            }

            bot.edit_message_text(
                f"⏳ *So'rovingiz qabul qilindi! #{bron_id}*\n\n"
                f"🛏 {state['xona_nomi']}\n"
                f"📅 {state['sana']} | {state['kunlar']} kun\n"
                f"👥 {state['kishi']} kishi\n"
                f"💰 {format_narx(state['jami_narx'])} so'm\n\n"
                f"Admin tasdiqlashidan keyin sizga xabar yuboramiz.\n"
                f"📞 {TELEFON1}",
                cid, call.message.message_id, parse_mode="Markdown"
            )
            bot.send_message(cid, "Bosh menyu 👇", reply_markup=asosiy_menu())

            # Adminlarga yuborish
            admin_kb = types.InlineKeyboardMarkup()
            admin_kb.add(
                types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_tasdiq_ha_{bron_id}"),
                types.InlineKeyboardButton("❌ Rad etish", callback_data=f"admin_tasdiq_yoq_{bron_id}")
            )
            admin_txt = (
                f"🔔 *YANGI BRON SO'ROVI #{bron_id}*\n\n"
                f"👤 {state['ism']}\n"
                f"📞 {state['telefon']}\n"
                f"📅 {state['sana']} | {state['kunlar']} kun\n"
                f"👥 {state['kishi']} kishi\n"
                f"🛏 {state['xona_nomi']}\n"
                f"💰 {format_narx(state['jami_narx'])} so'm\n"
                f"💬 @{call.from_user.username or 'yoq'}"
            )
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(admin_id, admin_txt, parse_mode="Markdown", reply_markup=admin_kb)
                except: pass

            user_state.pop(cid, None)
        except Exception as e:
            logging.error(e)
            xato_xabar(cid)
    else:
        user_state.pop(cid, None)
        bot.edit_message_text("❌ Bekor qilindi.", cid, call.message.message_id)
        bot.send_message(cid, "Bosh menyu 👇", reply_markup=asosiy_menu())
    bot.answer_callback_query(call.id)

# ==================== UMUMIY XABARLAR ====================

@bot.message_handler(func=lambda m: True)
def barcha(msg):
    cid = msg.chat.id
    state = user_state.get(cid, {})
    step = state.get("step")

    # Admin mijoz qidirish
    if step == "admin_mijoz_qidir" and is_admin(msg.from_user.id):
        tel = msg.text.strip()
        if tel in MIJOZLAR:
            m2 = MIJOZLAR[tel]
            bloq = "🚫 Bloklangan" if m2.get("user_id") in BLOKLANGAN else "✅ Faol"
            matn = (f"👤 *{m2['ism']}*\n📞 {m2['telefon']}\n"
                    f"💬 @{m2['username']}\n{bloq}\n"
                    f"Bronlar: {len(m2.get('bronlar', []))} ta")
            kb = types.InlineKeyboardMarkup()
            uid = m2.get("user_id")
            if uid in BLOKLANGAN:
                kb.add(types.InlineKeyboardButton("✅ Blokdan chiqarish", callback_data=f"unblock_{uid}"))
            else:
                kb.add(types.InlineKeyboardButton("🚫 Bloklash", callback_data=f"block_{uid}"))
            bot.send_message(cid, matn, parse_mode="Markdown", reply_markup=kb)
        else:
            bot.send_message(cid, f"❌ {tel} topilmadi")
        return

    # Admin tezkor bron
    if step == "admin_tezkor_kishi" and is_admin(msg.from_user.id):
        try:
            n = int(msg.text)
            state["ab"]["kishi"] = n
            state["ab"]["guruh"] = "oila"
            state["step"] = "admin_tezkor_sana"
            user_state[cid] = state
            bot.send_message(cid, f"👥 {n} kishi\n\n📅 Sana tanlang:", reply_markup=sana_tugmalari())
        except:
            bot.send_message(cid, "Raqam kiriting")
        return

    if step == "admin_tezkor_ism" and is_admin(msg.from_user.id):
        state["ab"]["ism"] = msg.text
        state["step"] = "admin_tezkor_telefon"
        user_state[cid] = state
        bot.send_message(cid, "Telefon raqami:")
        return

    if step == "admin_tezkor_telefon" and is_admin(msg.from_user.id):
        ab = state["ab"]
        bron_id = bron_id_gen()
        while bron_id in BRONLAR:
            bron_id = bron_id_gen()
        xid_list = ab["xona_ids"]
        BRONLAR[bron_id] = {
            "ism": ab["ism"], "telefon": msg.text,
            "sana": ab["sana"], "kunlar": ab["kunlar"],
            "kishi": ab["kishi"], "xona": ab["xona_nomi"],
            "xona_ids": xid_list, "narx": ab["narx"],
            "tasdiqlangan": True,
            "user_id": ADMIN_IDS[0], "username": "admin"
        }
        for xid in xid_list:
            band_qil(xid, ab["sana"], ab["kunlar"], bron_id)
        bot.send_message(cid,
            f"✅ *Bron #{bron_id} qo'shildi!*\n"
            f"{ab['xona_nomi']} | {ab['sana']} | {ab['kunlar']} kun\n"
            f"{format_narx(ab['narx'])} so'm",
            parse_mode="Markdown", reply_markup=admin_menu())
        user_state[cid] = {"mode": "admin"}
        return

    # Bo'sh xonalar - kishi soni
    if step == "bosh_kishi":
        try:
            n = int(msg.text)
            state["kishi"] = n
            state["guruh"] = "oila"
            state["step"] = "bosh_sana"
            user_state[cid] = state
            bot.send_message(cid, f"👥 {n} kishi\n\n📅 Qaysi sanada?",
                             reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🏠 Bosh menyu"))
            bot.send_message(cid, "Sanani tanlang:", reply_markup=sana_tugmalari())
        except:
            bot.send_message(cid, "Raqam kiriting")
        return

    # Mijoz bron
    if step == "kishi":
        try:
            n = int(msg.text)
            if n < 1: raise ValueError
            state["kishi"] = n
            state["step"] = "guruh"
            user_state[cid] = state
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            kb.add("👨‍👩‍👧‍👦 Oila bilan", "👬 Do'stlar / Erkaklar guruh")
            kb.add(types.KeyboardButton("🏠 Bosh menyu"))
            bot.send_message(cid, f"✅ {n} kishi\n\n👥 *Kimlar bilan kelmoqchisiz?*",
                             parse_mode="Markdown", reply_markup=kb)
        except:
            bot.send_message(cid, "Iltimos raqam kiriting")
        return

    if step == "guruh":
        g = "oila" if "Oila" in msg.text else "dost"
        state["guruh"] = g
        state["step"] = "sana"
        user_state[cid] = state
        bot.send_message(cid, "📅 *Qaysi sanada kelmoqchisiz?*",
                         parse_mode="Markdown",
                         reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🏠 Bosh menyu"))
        bot.send_message(cid, "👇 Sanani tanlang:", reply_markup=sana_tugmalari())
        return

    if step == "ism":
        state["ism"] = msg.text.strip()
        state["step"] = "telefon"
        user_state[cid] = state
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(types.KeyboardButton("📱 Kontaktni yuborish", request_contact=True))
        kb.add(types.KeyboardButton("🏠 Bosh menyu"))
        bot.send_message(cid, "📞 *Telefon raqamingizni yuboring:*\n\nYoki qo'lda kiriting: +998901234567",
                         parse_mode="Markdown", reply_markup=kb)
        return

    if step == "telefon":
        state["telefon"] = msg.text.strip()
        user_state[cid] = state
        _tasdiqlash_yuborim(cid)
        return

if __name__ == "__main__":
    print("Tog' Tagi Resort Bot ishga tushdi!")
    bot.infinity_polling()
