import os
import logging
from datetime import datetime, timedelta
from io import BytesIO
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [8886176055, 7323184602]
TELEFON1 = "+998704902025"
TELEFON2 = "+998993342035"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(BOT_TOKEN)

bot.set_my_commands([
    types.BotCommand("start", "Bosh menyu"),
    types.BotCommand("bron", "Xona bron qilish"),
    types.BotCommand("xonalar", "Bosh xonalar"),
    types.BotCommand("xizmatlar", "Xizmatlar"),
    types.BotCommand("manzil", "Manzil"),
    types.BotCommand("boglanish", "Boglanish"),
])

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
MIJOZLAR = {}
BLOKLANGAN = []
MEDIA = {"photos": [], "videos": []}
user_state = {}

# ==================== YORDAMCHI ====================

def is_admin(uid):
    return uid in ADMIN_IDS

def format_narx(n):
    return f"{n:,}".replace(",", " ")

def xona_band_mi(xid, sana):
    return sana in XONALAR[xid]["band"]

def mos_kombinatsiya(kishi, guruh, sana):
    """Eng samarali xona kombinatsiyasini topish"""
    bosh = []
    for xid, x in XONALAR.items():
        if not xona_band_mi(xid, sana):
            bosh.append((xid, x))

    if not bosh:
        return []

    # Bitta xona yetarlimi?
    for xid, x in sorted(bosh, key=lambda a: a[1]["sigim"]):
        if x["sigim"] >= kishi:
            return [(xid, x)]

    # Kombinatsiya kerak — greedy yondashuv
    # Guruhga qarab afzal qavat
    afzal_qavat = 1 if guruh == "oila" else 2

    # Avval afzal qavatdan, keyin boshqasidan
    afzal = [(xid, x) for xid, x in bosh if x["qavat"] == afzal_qavat]
    boshqa = [(xid, x) for xid, x in bosh if x["qavat"] != afzal_qavat]
    tartiblangan = sorted(afzal, key=lambda a: a[1]["sigim"], reverse=True) + \
                   sorted(boshqa, key=lambda a: a[1]["sigim"], reverse=True)

    tanlangan = []
    jami = 0
    for xid, x in tartiblangan:
        if jami >= kishi:
            break
        tanlangan.append((xid, x))
        jami += x["sigim"]

    if jami >= kishi:
        return tanlangan
    return []

def xato_xabar(cid):
    bot.send_message(
        cid,
        f"⚠️ Nimadir xato ketdi.\n\n"
        f"Telefon orqali bron qilishingiz mumkin:\n"
        f"📞 {TELEFON1}\n"
        f"📞 {TELEFON2}",
        reply_markup=asosiy_menu()
    )

def sana_tugmalari(boshlanish=None):
    """Boshlanish sanasidan 30 kun ko'rsat"""
    kb = types.InlineKeyboardMarkup(row_width=4)
    if boshlanish is None:
        boshlanish = datetime.now().date()
    tugmalar = []
    for i in range(30):
        kun = boshlanish + timedelta(days=i)
        sana_str = kun.strftime("%d.%m.%Y")
        kun_qisqa = kun.strftime("%d/%m")
        tugmalar.append(types.InlineKeyboardButton(kun_qisqa, callback_data=f"sana_{sana_str}"))
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
        types.KeyboardButton("📸 Rasm yuklash"),
        types.KeyboardButton("🎥 Video yuklash"),
        types.KeyboardButton("➕ Tezkor bron"),
        types.KeyboardButton("📄 PDF hisobot"),
        types.KeyboardButton("🔙 Asosiy menyu")
    )
    return kb

def xonalar_boshqaruv_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for xid, x in XONALAR.items():
        qavat = "🏠" if x["qavat"] == 1 else "🏢"
        kb.add(types.InlineKeyboardButton(
            f"{qavat} {x['nomi']} ({x['sigim']} kishi)",
            callback_data=f"admin_xona_{xid}"
        ))
    return kb

def xona_boshqaruv_kb(xid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📅 Bronlar ko'rish", callback_data=f"ax_bronlar_{xid}"),
        types.InlineKeyboardButton("🔴 Band qilish", callback_data=f"ax_band_{xid}"),
        types.InlineKeyboardButton("🟢 Bo'sh qilish", callback_data=f"ax_bosh_{xid}"),
        types.InlineKeyboardButton("🔙 Orqaga", callback_data="ax_back")
    )
    return kb

# ==================== XONA TANLASH INLINE ====================

def xonalar_kombinatsiya_inline(kombinatsiya, sana):
    kb = types.InlineKeyboardMarkup(row_width=1)
    jami_narx = sum(x["narx"] for _, x in kombinatsiya)
    jami_sigim = sum(x["sigim"] for _, x in kombinatsiya)
    xona_nomlari = " + ".join(x["nomi"] for _, x in kombinatsiya)

    if len(kombinatsiya) == 1:
        xid, x = kombinatsiya[0]
        qavat = "🏠 1-qavat" if x["qavat"] == 1 else "🏢 2-qavat"
        matn = f"{qavat}\n🛏 {x['nomi']} | 👥 {x['sigim']} kishi\n💰 {format_narx(x['narx'])} so'm/kecha"
        kb.add(types.InlineKeyboardButton(matn, callback_data=f"kombina_{xid}_{sana}"))
    else:
        ids = "_".join(str(xid) for xid, _ in kombinatsiya)
        matn = f"✨ Tavsiya: {xona_nomlari}\n👥 Jami: {jami_sigim} kishi\n💰 {format_narx(jami_narx)} so'm/kecha"
        kb.add(types.InlineKeyboardButton(matn, callback_data=f"kombina_{ids}_{sana}"))

    # Boshqa variantlar ham ko'rsat
    kb.add(types.InlineKeyboardButton("📋 Barcha bo'sh xonalar", callback_data=f"barcha_xonalar_{sana}"))
    return kb

def barcha_bosh_xonalar_inline(sana):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for xid, x in XONALAR.items():
        if xona_band_mi(xid, sana):
            continue
        qavat = "🏠" if x["qavat"] == 1 else "🏢"
        narx = format_narx(x["narx"])
        kb.add(types.InlineKeyboardButton(
            f"{qavat} {x['nomi']} | 👥 {x['sigim']} kishi | 💰 {narx} so'm",
            callback_data=f"kombina_{xid}_{sana}"
        ))
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="bron_qayta"))
    return kb

# ==================== START ====================

@bot.message_handler(commands=["start", "bron", "xonalar", "xizmatlar", "manzil", "boglanish"])
def start(msg):
    if msg.text and msg.text.startswith("/bron"):
        bron_start(msg)
        return
    if msg.text and msg.text.startswith("/xonalar"):
        bosh_xonalar(msg)
        return
    if msg.text and msg.text.startswith("/xizmatlar"):
        xizmatlar(msg)
        return
    if msg.text and msg.text.startswith("/manzil"):
        manzil(msg)
        return
    if msg.text and msg.text.startswith("/boglanish"):
        boglanish(msg)
        return
    user_state.pop(msg.chat.id, None)
    bot.send_message(
        msg.chat.id,
        "🏔 *Tog' Tagi Resort*\n\n"
        "Shohimardon tog'lari bag'rida, sof havo va go'zal tabiat qo'ynida dam oling!\n\n"
        "🌊 Soy bo'yida\n"
        "💦 Sharshara yaqinida\n"
        "🍽 Oshxona mavjud\n"
        "🛖 Qulay tapchanlar\n"
        "📍 Ko'lqubondan 300 metr pastda\n\n"
        "📞 Bog'lanish:\n"
        f"{TELEFON1}\n"
        f"{TELEFON2}\n\n"
        "👇 Xizmatlarimiz bilan tanishing:",
        parse_mode="Markdown",
        reply_markup=asosiy_menu()
    )

@bot.message_handler(commands=["admin"])
def admin_panel(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "❌ Ruxsat yo'q")
        return
    user_state[msg.chat.id] = {"mode": "admin"}
    bot.send_message(msg.chat.id, "👨‍💼 *Admin panel*\n\nNimani qilmoqchisiz?",
                     parse_mode="Markdown", reply_markup=admin_menu())

# ==================== MIJOZLAR ====================

@bot.message_handler(func=lambda m: m.text == "🛏 Xona bron qilish")
def bron_start(msg):
    if msg.from_user.id in BLOKLANGAN:
        bot.send_message(msg.chat.id, "❌ Siz bloklandingiz. Bog'lanish: " + TELEFON1)
        return
    user_state[msg.chat.id] = {"step": "kishi"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    kb.add("1","2","3","4","5","6","7","8","9","10","11","12","13","14")
    kb.add(types.KeyboardButton("🏠 Bosh menyu"))
    bot.send_message(msg.chat.id, "👥 *Nechta kishi kelmoqchisiz?*\n\n_(1 dan 14 gacha)_",
                     parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📅 Bo'sh xonalar")
def bosh_xonalar(msg):
    bugun = datetime.now().strftime("%d.%m.%Y")
    matn = "🏨 *Tog' Tagi Resort — Bugungi holat:*\n\n"
    matn += "🏠 *1-qavat (Oilalar uchun qulay):*\n"
    for xid in [1,2,3,4]:
        x = XONALAR[xid]
        h = "🔴 Band" if xona_band_mi(xid, bugun) else "🟢 Bo'sh"
        narx = format_narx(x["narx"])
        matn += f"  {x['nomi']} | {x['sigim']} 👤 | {narx} so'm | {h}\n"
    matn += "\n🏢 *2-qavat (Do'stlar uchun qulay):*\n"
    for xid in [5,6,7,8,9,10]:
        x = XONALAR[xid]
        h = "🔴 Band" if xona_band_mi(xid, bugun) else "🟢 Bo'sh"
        narx = format_narx(x["narx"])
        matn += f"  {x['nomi']} | {x['sigim']} 👤 | {narx} so'm | {h}\n"
    matn += f"\n📞 Bron: {TELEFON1}"
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🖼 Galereya")
def galereya(msg):
    if not MEDIA["photos"] and not MEDIA["videos"]:
        bot.send_message(msg.chat.id, "📸 Hozircha rasm/video yuklanmagan.\nTez orada qo'shamiz!")
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
    bot.send_message(msg.chat.id,
        "🌿 *Tog' Tagi Resort Xizmatlari:*\n\n"
        "🌊 Soy bo'yi\n"
        "💦 Sharshara\n"
        "🍽 Oshxona — milliy taomlar\n"
        "🔥 Mangal va Shashlik\n"
        "🛖 Tapchanlar\n"
        "🚗 Bepul parking\n\n"
        "📍 Ko'lqubondan 300m pastda\n"
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
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🛏 Xona bron qilish", callback_data="bron_start"))
    bot.send_message(msg.chat.id,
        "📞 *Bog'lanish:*\n\n"
        f"📱 {TELEFON1}\n📱 {TELEFON2}\n"
        "📸 Instagram: @togtagi_resort\n⏰ 24/7",
        parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "🏠 Bosh menyu")
def bosh_menyu(msg):
    user_state.pop(msg.chat.id, None)
    bot.send_message(msg.chat.id, "Bosh menyu 👇", reply_markup=asosiy_menu())

# ==================== ADMIN PANEL ====================

@bot.message_handler(func=lambda m: m.text == "🔙 Asosiy menyu" and is_admin(m.from_user.id))
def admin_back(msg):
    user_state.pop(msg.chat.id, None)
    bot.send_message(msg.chat.id, "Asosiy menyu", reply_markup=asosiy_menu())

@bot.message_handler(func=lambda m: m.text == "🏨 Xonalar boshqaruvi" and is_admin(m.from_user.id))
def xonalar_boshqaruvi(msg):
    bot.send_message(msg.chat.id, "🏨 *Xonalarni tanlang:*\n\nHar bir xona uchun bronlar, band/bosh qilish imkoniyati:",
                     parse_mode="Markdown", reply_markup=xonalar_boshqaruv_menu())

@bot.message_handler(func=lambda m: m.text == "📋 Bronlar ro'yxati" and is_admin(m.from_user.id))
def bronlar_royxati(msg):
    if not BRONLAR:
        bot.send_message(msg.chat.id, "📋 Hozircha bron yo'q", reply_markup=admin_menu())
        return
    matn = "📋 *So'nggi bronlar:*\n\n"
    for bron_id, b in list(BRONLAR.items())[-15:]:
        matn += (
            f"*#{bron_id}* | {b['xona']}\n"
            f"👤 {b['ism']} | 📞 {b['telefon']}\n"
            f"📅 {b['sana']} | 👥 {b['kishi']} kishi\n"
            f"💰 {format_narx(b['narx'])} so'm\n\n"
        )
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "📄 PDF hisobot" and is_admin(m.from_user.id))
def pdf_hisobot(msg):
    if not BRONLAR:
        bot.send_message(msg.chat.id, "Hozircha bron yo'q", reply_markup=admin_menu())
        return
    try:
        matn = "BRONLAR RO'YXATI\n"
        matn += "=" * 40 + "\n\n"
        for bron_id, b in BRONLAR.items():
            matn += f"#{bron_id} | {b['xona']}\n"
            matn += f"Ism: {b['ism']}\n"
            matn += f"Telefon: {b['telefon']}\n"
            matn += f"Sana: {b['sana']}\n"
            matn += f"Kishi: {b['kishi']}\n"
            matn += f"Narx: {format_narx(b['narx'])} som\n"
            matn += "-" * 30 + "\n"
        buf = BytesIO(matn.encode("utf-8"))
        buf.name = "bronlar.txt"
        bot.send_document(msg.chat.id, buf, caption="📄 Bronlar ro'yxati")
    except Exception as e:
        logging.error(e)
        bot.send_message(msg.chat.id, "Xato yuz berdi")

@bot.message_handler(func=lambda m: m.text == "👥 Mijozlar bazasi" and is_admin(m.from_user.id))
def mijozlar_bazasi(msg):
    user_state[msg.chat.id] = {"step": "admin_mijoz_qidir", "mode": "admin"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Admin menyu")
    bot.send_message(msg.chat.id,
        "👥 *Mijozlar bazasi*\n\nMijoz telefon raqamini yozing:",
        parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📸 Rasm yuklash" and is_admin(m.from_user.id))
def admin_rasm_start(msg):
    user_state[msg.chat.id] = {"step": "admin_rasm", "mode": "admin"}
    bot.send_message(msg.chat.id, "📸 Rasmlarni yuboring.\n/done — tugallash")

@bot.message_handler(func=lambda m: m.text == "🎥 Video yuklash" and is_admin(m.from_user.id))
def admin_video_start(msg):
    user_state[msg.chat.id] = {"step": "admin_video", "mode": "admin"}
    bot.send_message(msg.chat.id, "🎥 Videolarni yuboring.\n/done — tugallash")

@bot.message_handler(func=lambda m: m.text == "➕ Tezkor bron" and is_admin(m.from_user.id))
def admin_tezkor_bron(msg):
    user_state[msg.chat.id] = {"step": "admin_bron_ism", "mode": "admin", "admin_bron": {}}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Admin menyu")
    bot.send_message(msg.chat.id, "➕ *Tezkor bron*\n\nMijoz ismi:", parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "🔙 Admin menyu" and is_admin(m.from_user.id))
def admin_menyu_back(msg):
    user_state[msg.chat.id] = {"mode": "admin"}
    bot.send_message(msg.chat.id, "Admin panel 👇", reply_markup=admin_menu())

@bot.message_handler(commands=["done"])
def cmd_done(msg):
    if not is_admin(msg.from_user.id):
        return
    user_state[msg.chat.id] = {"mode": "admin"}
    bot.send_message(msg.chat.id, "✅ Saqlandi!", reply_markup=admin_menu())

@bot.message_handler(content_types=["photo"])
def photo_handler(msg):
    state = user_state.get(msg.chat.id, {})
    if is_admin(msg.from_user.id) and state.get("step") == "admin_rasm":
        MEDIA["photos"].append(msg.photo[-1].file_id)
        bot.send_message(msg.chat.id, f"✅ Rasm saqlandi! Jami: {len(MEDIA['photos'])} ta\n/done — tugallash")

@bot.message_handler(content_types=["video"])
def video_handler(msg):
    state = user_state.get(msg.chat.id, {})
    if is_admin(msg.from_user.id) and state.get("step") == "admin_video":
        MEDIA["videos"].append(msg.video.file_id)
        bot.send_message(msg.chat.id, f"✅ Video saqlandi! Jami: {len(MEDIA['videos'])} ta\n/done — tugallash")

@bot.message_handler(content_types=["contact"])
def contact_handler(msg):
    cid = msg.chat.id
    state = user_state.get(cid, {})
    if state.get("step") == "telefon":
        telefon = msg.contact.phone_number
        if not telefon.startswith("+"):
            telefon = "+" + telefon
        state["telefon"] = telefon
        user_state[cid] = state
        _telefon_olindi(msg, telefon)

# ==================== CALLBACK ====================

@bot.callback_query_handler(func=lambda c: c.data == "bron_start")
def cb_bron_start(call):
    user_state[call.message.chat.id] = {"step": "kishi"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    kb.add("1","2","3","4","5","6","7","8","9","10","11","12","13","14")
    kb.add(types.KeyboardButton("🏠 Bosh menyu"))
    bot.send_message(call.message.chat.id, "👥 *Nechta kishi kelmoqchisiz?*",
                     parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "bron_qayta")
def cb_bron_qayta(call):
    cid = call.message.chat.id
    state = user_state.get(cid, {})
    sana = state.get("sana", "")
    bot.edit_message_text(
        f"📅 Sana: *{sana}*\n\n📋 *Barcha bo'sh xonalar:*",
        cid, call.message.message_id,
        parse_mode="Markdown",
        reply_markup=barcha_bosh_xonalar_inline(sana)
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("sana_"))
def cb_sana(call):
    cid = call.message.chat.id
    sana = call.data.replace("sana_", "")
    state = user_state.get(cid, {})
    state["sana"] = sana
    user_state[cid] = state

    kishi = state.get("kishi", 1)
    guruh = state.get("guruh", "oila")

    kombinatsiya = mos_kombinatsiya(kishi, guruh, sana)

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

    jami_sigim = sum(x["sigim"] for _, x in kombinatsiya)
    jami_narx = sum(x["narx"] for _, x in kombinatsiya)
    xona_nomlari = " + ".join(x["nomi"] for _, x in kombinatsiya)

    matn = f"📅 Sana: *{sana}* | 👥 {kishi} kishi\n\n"
    matn += "✨ *Sizga eng mos variant:*\n\n"

    for xid, x in kombinatsiya:
        qavat = "🏠 1-qavat" if x["qavat"] == 1 else "🏢 2-qavat"
        narx = format_narx(x["narx"])
        matn += f"🛏 *{x['nomi']}* | {qavat}\n"
        matn += f"   👥 {x['sigim']} kishilik | 💰 {narx} so'm\n\n"

    if len(kombinatsiya) > 1:
        matn += f"💰 *Jami: {format_narx(jami_narx)} so'm*\n\n"

    matn += "👇 Tanlang:"

    kb = types.InlineKeyboardMarkup(row_width=1)
    if len(kombinatsiya) == 1:
        xid = kombinatsiya[0][0]
        kb.add(types.InlineKeyboardButton(
            f"✅ {xona_nomlari} — {format_narx(jami_narx)} so'm",
            callback_data=f"kombina_{xid}_{sana}"
        ))
    else:
        ids = "_".join(str(xid) for xid, _ in kombinatsiya)
        kb.add(types.InlineKeyboardButton(
            f"✅ Hammasi ({xona_nomlari}) — {format_narx(jami_narx)} so'm",
            callback_data=f"kombina_{ids}_{sana}"
        ))
    kb.add(types.InlineKeyboardButton("📋 Barcha bo'sh xonalar", callback_data=f"barcha_xonalar_{sana}"))

    bot.edit_message_text(matn, cid, call.message.message_id,
                          parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("barcha_xonalar_"))
def cb_barcha_xonalar(call):
    cid = call.message.chat.id
    sana = call.data.replace("barcha_xonalar_", "")
    bot.edit_message_text(
        f"📅 Sana: *{sana}*\n\n📋 *Barcha bo'sh xonalar:*",
        cid, call.message.message_id,
        parse_mode="Markdown",
        reply_markup=barcha_bosh_xonalar_inline(sana)
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("kombina_"))
def cb_kombina(call):
    cid = call.message.chat.id
    parts = call.data.split("_")
    # kombina_XID_SANA yoki kombina_XID1_XID2_SANA
    sana = parts[-1]
    xid_parts = parts[1:-1]
    xid_list = [int(x) for x in xid_parts]

    state = user_state.get(cid, {})
    state["xona_ids"] = xid_list
    state["step"] = "ism"

    xonalar_info = [XONALAR[xid] for xid in xid_list]
    jami_narx = sum(x["narx"] for x in xonalar_info)
    xona_nomlari = " + ".join(x["nomi"] for x in xonalar_info)
    jami_sigim = sum(x["sigim"] for x in xonalar_info)

    state["xona_nomi"] = xona_nomlari
    state["jami_narx"] = jami_narx
    user_state[cid] = state

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🏠 Bosh menyu")
    bot.edit_message_text(
        f"✅ *{xona_nomlari}* tanlandi\n"
        f"👥 Jami: {jami_sigim} kishilik | 💰 {format_narx(jami_narx)} so'm/kecha\n\n"
        f"👤 *Ismingizni kiriting:*",
        cid, call.message.message_id, parse_mode="Markdown"
    )
    bot.send_message(cid, "👇 Ismingizni yozing:", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("tasdiq_"))
def cb_tasdiq(call):
    cid = call.message.chat.id
    if call.data == "tasdiq_ha":
        state = user_state.get(cid, {})
        try:
            xid_list = state["xona_ids"]
            bron_id = len(BRONLAR) + 1
            xonalar_info = [XONALAR[xid] for xid in xid_list]
            jami_narx = state["jami_narx"]
            xona_nomi = state["xona_nomi"]

            BRONLAR[bron_id] = {
                "ism": state["ism"],
                "telefon": state["telefon"],
                "sana": state["sana"],
                "kishi": state["kishi"],
                "xona": xona_nomi,
                "xona_ids": xid_list,
                "narx": jami_narx,
                "aktiv": True,
                "user_id": call.from_user.id,
                "username": call.from_user.username or "yoq"
            }

            for xid in xid_list:
                XONALAR[xid]["band"][state["sana"]] = {"bron_id": bron_id}

            # Mijozlar bazasiga qo'shish
            MIJOZLAR[state["telefon"]] = {
                "ism": state["ism"],
                "telefon": state["telefon"],
                "user_id": call.from_user.id,
                "username": call.from_user.username or "yoq",
                "bronlar": MIJOZLAR.get(state["telefon"], {}).get("bronlar", []) + [bron_id]
            }

            narx = format_narx(jami_narx)
            admin_txt = (
                f"🔔 *YANGI BRON #{bron_id}*\n\n"
                f"👤 {state['ism']}\n"
                f"📞 {state['telefon']}\n"
                f"📅 {state['sana']}\n"
                f"👥 {state['kishi']} kishi\n"
                f"🛏 {xona_nomi}\n"
                f"💰 {narx} so'm\n"
                f"💬 @{call.from_user.username or 'yoq'}"
            )
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(admin_id, admin_txt, parse_mode="Markdown")
                except:
                    pass

            bot.edit_message_text(
                f"✅ *Bron tasdiqlandi! #{bron_id}*\n\n"
                f"🛏 {xona_nomi}\n"
                f"📅 {state['sana']}\n"
                f"👥 {state['kishi']} kishi\n"
                f"💰 {narx} so'm\n\n"
                f"Tez orada siz bilan bog'lanamiz!\n"
                f"📞 {TELEFON1}",
                cid, call.message.message_id, parse_mode="Markdown"
            )
            user_state.pop(cid, None)
            bot.send_message(cid, "Bosh menyu 👇", reply_markup=asosiy_menu())
        except Exception as e:
            logging.error(e)
            xato_xabar(cid)
    else:
        user_state.pop(cid, None)
        bot.edit_message_text("❌ Bron bekor qilindi.", cid, call.message.message_id)
        bot.send_message(cid, "Bosh menyu 👇", reply_markup=asosiy_menu())
    bot.answer_callback_query(call.id)

# ==================== ADMIN XONA BOSHQARUVI ====================

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_xona_"))
def cb_admin_xona(call):
    if not is_admin(call.from_user.id):
        return
    xid = int(call.data.replace("admin_xona_", ""))
    x = XONALAR[xid]
    bugun = datetime.now().strftime("%d.%m.%Y")
    holat = "🔴 Band" if xona_band_mi(xid, bugun) else "🟢 Bo'sh"
    narx = format_narx(x["narx"])
    matn = (
        f"🛏 *{x['nomi']}*\n\n"
        f"🏠 Qavat: {'1-qavat' if x['qavat']==1 else '2-qavat'}\n"
        f"👥 Sigim: {x['sigim']} kishi\n"
        f"💰 Narx: {narx} so'm\n"
        f"📅 Bugun: {holat}\n\n"
        f"Nima qilmoqchisiz?"
    )
    bot.edit_message_text(matn, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=xona_boshqaruv_kb(xid))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ax_bronlar_"))
def cb_ax_bronlar(call):
    if not is_admin(call.from_user.id):
        return
    xid = int(call.data.replace("ax_bronlar_", ""))
    x = XONALAR[xid]
    xona_bronlar = {bid: b for bid, b in BRONLAR.items() if xid in b.get("xona_ids", [])}

    if not xona_bronlar:
        matn = f"🛏 *{x['nomi']}* — hozircha bron yo'q"
    else:
        matn = f"🛏 *{x['nomi']}* bronlari:\n\n"
        for bid, b in list(xona_bronlar.items())[-10:]:
            matn += f"#{bid} | {b['sana']}\n"
            matn += f"👤 {b['ism']} | 📞 {b['telefon']}\n\n"

    # 15 kunlik holat ham ko'rsat
    matn += "\n📅 *15 kunlik holat:*\n"
    bugun = datetime.now().date()
    for i in range(15):
        kun = bugun + timedelta(days=i)
        sana_str = kun.strftime("%d.%m.%Y")
        kun_qisqa = kun.strftime("%d/%m")
        h = "🔴" if xona_band_mi(xid, sana_str) else "🟢"
        matn += f"{h} {kun_qisqa}  "
        if (i+1) % 5 == 0:
            matn += "\n"

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"admin_xona_{xid}"))
    bot.edit_message_text(matn, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ax_band_"))
def cb_ax_band(call):
    if not is_admin(call.from_user.id):
        return
    xid = int(call.data.replace("ax_band_", ""))
    user_state[call.message.chat.id] = {
        "step": "ax_band_sana", "mode": "admin", "ax_xid": xid
    }
    bot.send_message(call.message.chat.id,
        f"🔴 *{XONALAR[xid]['nomi']}* ni band qilish\n\n📅 Sanani tanlang:",
        parse_mode="Markdown",
        reply_markup=sana_tugmalari()
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ax_bosh_"))
def cb_ax_bosh(call):
    if not is_admin(call.from_user.id):
        return
    xid = int(call.data.replace("ax_bosh_", ""))
    user_state[call.message.chat.id] = {
        "step": "ax_bosh_sana", "mode": "admin", "ax_xid": xid
    }
    bot.send_message(call.message.chat.id,
        f"🟢 *{XONALAR[xid]['nomi']}* ni bo'sh qilish\n\n📅 Sanani tanlang:",
        parse_mode="Markdown",
        reply_markup=sana_tugmalari()
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "ax_back")
def cb_ax_back(call):
    if not is_admin(call.from_user.id):
        return
    bot.edit_message_text("🏨 *Xonalarni tanlang:*",
                          call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=xonalar_boshqaruv_menu())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("axband_sana_"))
def cb_axband_sana(call):
    if not is_admin(call.from_user.id):
        return
    cid = call.message.chat.id
    state = user_state.get(cid, {})
    xid = state.get("ax_xid")
    sana = call.data.replace("axband_sana_", "")
    XONALAR[xid]["band"][sana] = {"admin": True}
    user_state[cid] = {"mode": "admin"}
    bot.send_message(cid, f"✅ *{XONALAR[xid]['nomi']}* — {sana} BAND qilindi",
                     parse_mode="Markdown", reply_markup=admin_menu())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("axbosh_sana_"))
def cb_axbosh_sana(call):
    if not is_admin(call.from_user.id):
        return
    cid = call.message.chat.id
    state = user_state.get(cid, {})
    xid = state.get("ax_xid")
    sana = call.data.replace("axbosh_sana_", "")
    XONALAR[xid]["band"].pop(sana, None)
    user_state[cid] = {"mode": "admin"}
    bot.send_message(cid, f"✅ *{XONALAR[xid]['nomi']}* — {sana} BO'SH qilindi",
                     parse_mode="Markdown", reply_markup=admin_menu())
    bot.answer_callback_query(call.id)

# ==================== UMUMIY XABARLAR ====================

def _telefon_olindi(msg, telefon):
    cid = msg.chat.id
    state = user_state.get(cid, {})
    state["telefon"] = telefon
    try:
        xid_list = state["xona_ids"]
        xonalar_info = [XONALAR[xid] for xid in xid_list]
        jami_narx = state["jami_narx"]
        xona_nomi = state["xona_nomi"]
        narx = format_narx(jami_narx)
        matn = (
            f"📋 *Bron ma'lumotlari:*\n\n"
            f"👤 Ism: {state['ism']}\n"
            f"📞 Telefon: {telefon}\n"
            f"📅 Sana: {state['sana']}\n"
            f"👥 Kishi soni: {state['kishi']}\n"
            f"🛏 Xona: {xona_nomi}\n"
            f"💰 Narx: {narx} so'm\n\n"
            f"✅ Tasdiqlaysizmi?"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="tasdiq_ha"),
            types.InlineKeyboardButton("❌ Bekor", callback_data="tasdiq_yoq")
        )
        bot.send_message(cid, matn, parse_mode="Markdown", reply_markup=kb)
        state["step"] = "tasdiq"
        user_state[cid] = state
    except Exception as e:
        logging.error(e)
        xato_xabar(cid)

@bot.message_handler(func=lambda m: True)
def barcha(msg):
    cid = msg.chat.id
    state = user_state.get(cid, {})
    step = state.get("step")

    # ADMIN XONA BAND/BOSH SANA
    if step == "ax_band_sana" and is_admin(msg.from_user.id):
        try:
            sana = msg.text.strip()
            datetime.strptime(sana, "%d.%m.%Y")
            xid = state["ax_xid"]
            XONALAR[xid]["band"][sana] = {"admin": True}
            user_state[cid] = {"mode": "admin"}
            bot.send_message(cid, f"✅ {XONALAR[xid]['nomi']} — {sana} BAND", reply_markup=admin_menu())
        except:
            bot.send_message(cid, "Format: 15.06.2026")
        return

    if step == "ax_bosh_sana" and is_admin(msg.from_user.id):
        try:
            sana = msg.text.strip()
            xid = state["ax_xid"]
            XONALAR[xid]["band"].pop(sana, None)
            user_state[cid] = {"mode": "admin"}
            bot.send_message(cid, f"✅ {XONALAR[xid]['nomi']} — {sana} BO'SH", reply_markup=admin_menu())
        except:
            bot.send_message(cid, "Xato")
        return

    # ADMIN MIJOZ QIDIRISH
    if step == "admin_mijoz_qidir" and is_admin(msg.from_user.id):
        telefon = msg.text.strip()
        if telefon in MIJOZLAR:
            m = MIJOZLAR[telefon]
            bloklangan = "🚫 Bloklangan" if m.get("user_id") in BLOKLANGAN else "✅ Faol"
            matn = (
                f"👤 *Mijoz ma'lumoti:*\n\n"
                f"Ism: {m['ism']}\n"
                f"Telefon: {m['telefon']}\n"
                f"Telegram: @{m['username']}\n"
                f"Holat: {bloklangan}\n"
                f"Bronlar: {len(m.get('bronlar', []))} ta\n"
            )
            kb = types.InlineKeyboardMarkup()
            uid = m.get("user_id")
            if uid in BLOKLANGAN:
                kb.add(types.InlineKeyboardButton("✅ Blokdan chiqarish", callback_data=f"unblock_{uid}"))
            else:
                kb.add(types.InlineKeyboardButton("🚫 Bloklash", callback_data=f"block_{uid}"))
            bot.send_message(cid, matn, parse_mode="Markdown", reply_markup=kb)
        else:
            bot.send_message(cid, f"❌ {telefon} raqamli mijoz topilmadi")
        return

    # ADMIN TEZKOR BRON
    if step == "admin_bron_ism" and is_admin(msg.from_user.id):
        state["admin_bron"]["ism"] = msg.text
        state["step"] = "admin_bron_telefon"
        bot.send_message(cid, "Telefon raqami:")
        return

    if step == "admin_bron_telefon" and is_admin(msg.from_user.id):
        state["admin_bron"]["telefon"] = msg.text
        state["step"] = "admin_bron_sana"
        bot.send_message(cid, "📅 Sana tanlang:", reply_markup=sana_tugmalari())
        return

    if step == "admin_bron_xona" and is_admin(msg.from_user.id):
        try:
            xid = int(msg.text)
            ab = state["admin_bron"]
            x = XONALAR[xid]
            bron_id = len(BRONLAR) + 1
            BRONLAR[bron_id] = {
                "ism": ab["ism"], "telefon": ab["telefon"],
                "sana": ab["sana"], "kishi": x["sigim"],
                "xona": x["nomi"], "xona_ids": [xid],
                "narx": x["narx"], "aktiv": True,
                "user_id": ADMIN_IDS[0], "username": "admin"
            }
            XONALAR[xid]["band"][ab["sana"]] = {"bron_id": bron_id}
            narx = format_narx(x["narx"])
            bot.send_message(cid, f"✅ Bron #{bron_id} qo'shildi!\n{x['nomi']} — {ab['sana']} — {narx} so'm",
                             reply_markup=admin_menu())
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
            kb.add("👨‍👩‍👧‍👦 Oila / Ayollar bilan", "👬 Erkaklar / Do'stlar guruh")
            kb.add(types.KeyboardButton("🏠 Bosh menyu"))
            bot.send_message(cid, f"✅ {n} kishi\n\n👥 *Kimlar bilan kelmoqchisiz?*\n\n"
                                  "_(Oilalar va ayollar 1-qavatga, erkaklar 2-qavatga joylashtiriladi)_",
                             parse_mode="Markdown", reply_markup=kb)
        except ValueError:
            bot.send_message(cid, "Iltimos 1-14 orasida raqam tanlang")
        return

    if step == "guruh":
        g = "oila" if "Oila" in msg.text or "Ayol" in msg.text else "dost"
        state["guruh"] = g
        state["step"] = "sana"
        bot.send_message(cid,
            "📅 *Qaysi sanada kelmoqchisiz?*\n\n"
            "_(Siz kelgan kundan ertasi 13:00 gacha xona sizniki)_",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🏠 Bosh menyu")
        )
        bot.send_message(cid, "👇 30 kunlik sanani tanlang:", reply_markup=sana_tugmalari())
        return

    if step == "ism":
        state["ism"] = msg.text.strip()
        state["step"] = "telefon"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(types.KeyboardButton("📱 Kontaktni yuborish", request_contact=True))
        kb.add(types.KeyboardButton("🏠 Bosh menyu"))
        bot.send_message(cid,
            "📞 *Telefon raqamingizni yuboring:*\n\n"
            "Tugmani bosing yoki qo'lda kiriting: +998901234567",
            parse_mode="Markdown", reply_markup=kb)
        return

    if step == "telefon":
        telefon = msg.text.strip()
        _telefon_olindi(msg, telefon)
        return

# ==================== MIJOZ BLOKLASH ====================

@bot.callback_query_handler(func=lambda c: c.data.startswith("block_"))
def cb_block(call):
    if not is_admin(call.from_user.id):
        return
    uid = int(call.data.replace("block_", ""))
    if uid not in BLOKLANGAN:
        BLOKLANGAN.append(uid)
    bot.edit_message_text(f"🚫 Foydalanuvchi {uid} bloklandi",
                          call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "Bloklandi!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("unblock_"))
def cb_unblock(call):
    if not is_admin(call.from_user.id):
        return
    uid = int(call.data.replace("unblock_", ""))
    if uid in BLOKLANGAN:
        BLOKLANGAN.remove(uid)
    bot.edit_message_text(f"✅ Foydalanuvchi {uid} blokdan chiqarildi",
                          call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "Blok ochildi!")

# Admin sana tanlash (tezkor bron uchun)
@bot.callback_query_handler(func=lambda c: c.data.startswith("sana_") and is_admin(c.from_user.id))
def cb_sana_admin(call):
    cid = call.message.chat.id
    state = user_state.get(cid, {})
    sana = call.data.replace("sana_", "")

    if state.get("step") == "admin_bron_telefon":
        state["admin_bron"]["sana"] = sana
        state["step"] = "admin_bron_xona"
        user_state[cid] = state
        bot.send_message(cid, f"📅 Sana: {sana}\n\nXona raqami (1-10):")
        bot.answer_callback_query(call.id)
        return

    if state.get("step") == "ax_band_sana":
        xid = state["ax_xid"]
        XONALAR[xid]["band"][sana] = {"admin": True}
        user_state[cid] = {"mode": "admin"}
        bot.send_message(cid, f"✅ {XONALAR[xid]['nomi']} — {sana} BAND qilindi", reply_markup=admin_menu())
        bot.answer_callback_query(call.id)
        return

    if state.get("step") == "ax_bosh_sana":
        xid = state["ax_xid"]
        XONALAR[xid]["band"].pop(sana, None)
        user_state[cid] = {"mode": "admin"}
        bot.send_message(cid, f"✅ {XONALAR[xid]['nomi']} — {sana} BO'SH qilindi", reply_markup=admin_menu())
        bot.answer_callback_query(call.id)
        return

    # Aks holda mijoz uchun
    cb_sana(call)

if __name__ == "__main__":
    print("Tog' Tagi Resort Bot ishga tushdi!")
    bot.infinity_polling()
