import os
import logging
import random
import string
import sqlite3
import threading
from datetime import datetime, timedelta
from io import BytesIO
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [8886176055, 7323184602]
TELEFON1 = "+998993342035"
TELEFON2 = "+998704902025"
INSTAGRAM = "https://instagram.com/togtagi"
DB_PATH = "/data/resort.db"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(BOT_TOKEN)

# ==================== DATABASE ====================

def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS xonalar (
            id INTEGER PRIMARY KEY,
            nomi TEXT,
            qavat INTEGER,
            sigim INTEGER,
            narx INTEGER
        );
        CREATE TABLE IF NOT EXISTS xona_rasmlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            xona_id INTEGER,
            file_id TEXT
        );
        CREATE TABLE IF NOT EXISTS band (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            xona_id INTEGER,
            sana TEXT,
            bron_id TEXT
        );
        CREATE TABLE IF NOT EXISTS bronlar (
            id TEXT PRIMARY KEY,
            ism TEXT,
            telefon TEXT,
            sana TEXT,
            kunlar INTEGER,
            kishi INTEGER,
            xona TEXT,
            narx INTEGER,
            tasdiqlangan INTEGER DEFAULT 0,
            user_id INTEGER,
            username TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS bron_xonalar (
            bron_id TEXT,
            xona_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS mijozlar (
            telefon TEXT PRIMARY KEY,
            ism TEXT,
            user_id INTEGER,
            username TEXT,
            bloklangan INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tur TEXT,
            file_id TEXT
        );
        CREATE TABLE IF NOT EXISTS til (
            user_id INTEGER PRIMARY KEY,
            til TEXT
        );
        """)
        # Xonalarni boshlang'ich qiymatlar bilan to'ldirish
        existing = conn.execute("SELECT COUNT(*) FROM xonalar").fetchone()[0]
        if existing == 0:
            xonalar_data = [
                (1,"1-xona",1,3,300000),(2,"2-xona",1,3,300000),
                (3,"3-xona",1,7,700000),(4,"4-xona",1,7,700000),
                (5,"5-xona",2,3,300000),(6,"6-xona",2,3,300000),
                (7,"7-xona",2,3,300000),(8,"8-xona",2,3,300000),
                (9,"9-xona",2,3,300000),(10,"10-xona",2,3,300000),
            ]
            conn.executemany("INSERT INTO xonalar VALUES (?,?,?,?,?)", xonalar_data)
        conn.commit()

init_db()

bot.set_my_commands([
    types.BotCommand("start", "Bosh menyu"),
    types.BotCommand("bron", "Xona bron qilish"),
    types.BotCommand("xonalar", "Bo'sh xonalar"),
    types.BotCommand("xizmatlar", "Xizmatlar"),
    types.BotCommand("manzil", "Manzil"),
    types.BotCommand("boglanish", "Bog'lanish"),
])

user_state = {}

# ==================== TIL ====================

MATNLAR = {
    "uz": {
        "til_tanlash": "🌐 Tilni tanlang / Выберите язык:",
        "xush_kelibsiz": "🏔 *Tog' Tagi Resort*\n\nShohimardon tog'lari bag'rida, sof havo va go'zal tabiat qo'ynida dam oling!\n\n🌊 Soy bo'yida  |  💦 Sharshara\n🍽 Oshxona  |  🔥 Mangal\n🛖 Tapchanlar  |  🚗 Bepul parking\n\n📍 Ko'lqubondan 300 metr pastda\n\n📞 {tel1}  |  {tel2}",
        "bron": "🛏 Xona bron qilish",
        "bosh_xonalar": "📅 Bo'sh xonalar",
        "galereya": "🖼 Galereya",
        "xizmatlar": "🌿 Xizmatlar",
        "manzil": "📍 Manzil",
        "boglanish": "📞 Bog'lanish",
        "bosh_menyu": "🏠 Bosh menyu",
        "necha_kishi": "👥 *Nechta kishi kelmoqchisiz?*\n\nRaqam kiriting:",
        "kimlar": "👥 *Kimlar bilan kelmoqchisiz?*",
        "oila": "👨‍👩‍👧‍👦 Oila bilan",
        "dostlar": "👬 Do'stlar / Erkaklar",
        "qaysi_sana": "📅 *Qaysi sanada kelmoqchisiz?*",
        "sana_tanlang": "👇 Sanani tanlang:",
        "necha_kun": "Necha kun turmoqchisiz?",
        "ism": "👤 *Ismingizni kiriting:*",
        "telefon": "📞 *Telefon raqamingizni yuboring:*\n\nYoki kiriting: +998901234567",
        "kontakt": "📱 Kontaktni yuborish",
        "tasdiq": "✅ Tasdiqlaysizmi?",
        "tasdiq_ha": "✅ Tasdiqlash",
        "bekor": "❌ Bekor",
        "bron_yuborildi": "⏳ *So'rovingiz qabul qilindi! #{bid}*\n\n🛏 {xona}\n📅 {sana} | {kunlar} kun\n👥 {kishi} kishi\n💰 {narx} so'm\n\nAdmin tasdiqlashini kuting.\n📞 {tel}",
        "bron_tasdiqlandi": "✅ *Broningiz tasdiqlandi! #{bid}*\n\n🛏 {xona}\n📅 {sana} | {kunlar} kun\n👥 {kishi} kishi\n💰 {narx} so'm\n\n📞 {tel}",
        "bron_rad": "❌ Bron #{bid} rad etildi.\nBog'laning: {tel}",
        "mos_xona": "✨ *Sizga mos variant:*",
        "barcha_xonalar": "📋 Barcha bo'sh xonalar",
        "xona_yoq": "❌ Bu sanada mos bo'sh xona yo'q.\n\nBog'laning:\n📞 {tel}",
        "xizmatlar_matn": "🌿 *Tog' Tagi Resort Xizmatlari:*\n\n🌊 Soy bo'yi\n💦 Sharshara\n🍽 Oshxona *(o'zingiz pishirasiz)*\n🔥 Mangal\n🥩 Shashlik\n📶 WiFi\n📺 Televizor\n🛏 Yotoq joylar\n🛖 Tapchanlar\n🚗 Bepul parking\n🌿 Yashil tabiat\n\n📞 {tel1}\n📞 {tel2}",
        "manzil_matn": "📍 *Tog' Tagi Resort manzili:*\n\nShohimardon, Farg'ona viloyati\n📌 Ko'lqubondan 300 metr pastda\n\n📞 {tel1}\n📞 {tel2}",
        "boglanish_matn": "📞 *Bog'lanish:*\n\n📱 {tel1}\n📱 {tel2}\n📸 Instagram: @togtagi\n\n⏰ 24/7",
        "galereya_yoq": "📸 Hozircha rasm/video yo'q.",
        "vaqt_tugaydi": "⏰ Hurmatli mijoz!\n\nSizning xonadagi vaqtingiz bugun 12:00 da tugaydi.\nIltimos, xonani bo'shating.\n\n🛖 Tapchanlardan foydalanishingiz mumkin!\n\n📞 {tel}",
        "xato": "⚠️ Xatolik.\n\nBog'laning:\n📞 {tel1}\n📞 {tel2}",
        "til_btn": "🇺🇿 O'zbek (lotin)",
    },
    "uz_kril": {
        "til_tanlash": "🌐 Tilni tanlang / Выберите язык:",
        "xush_kelibsiz": "🏔 *Тоғ Тagi Резорт*\n\nШоҳимардон тоғлари бағрида дам олинг!\n\n🌊 Соy бўйида  |  💦 Шаршара\n🍽 Ошхона  |  🔥 Мангал\n🛖 Тапчанлар  |  🚗 Бепул паркинг\n\n📍 Кўлқубондан 300 метр пастда\n\n📞 {tel1}  |  {tel2}",
        "bron": "🛏 Хона брон қилиш",
        "bosh_xonalar": "📅 Бўш хоналар",
        "galereya": "🖼 Галерея",
        "xizmatlar": "🌿 Хизматлар",
        "manzil": "📍 Манзил",
        "boglanish": "📞 Боғланиш",
        "bosh_menyu": "🏠 Бош меню",
        "necha_kishi": "👥 *Неча киши келмоқчисиз?*\n\nРақам киритинг:",
        "kimlar": "👥 *Кимлар билан келмоқчисиз?*",
        "oila": "👨‍👩‍👧‍👦 Оила билан",
        "dostlar": "👬 Дўстлар / Эркаклар",
        "qaysi_sana": "📅 *Қайси санада келмоқчисиз?*",
        "sana_tanlang": "👇 Санани танланг:",
        "necha_kun": "Неча кун турмоқчисиз?",
        "ism": "👤 *Исмингизни киритинг:*",
        "telefon": "📞 *Телефон рақамингизни юборинг:*\n\nЁки киритинг: +998901234567",
        "kontakt": "📱 Контактни юбориш",
        "tasdiq": "✅ Тасдиқлайсизми?",
        "tasdiq_ha": "✅ Тасдиқлаш",
        "bekor": "❌ Бекор",
        "bron_yuborildi": "⏳ *Сўровингиз қабул қилинди! #{bid}*\n\n🛏 {xona}\n📅 {sana} | {kunlar} кун\n👥 {kishi} киши\n💰 {narx} сўм\n\nАдмин тасдиқлашини кутинг.\n📞 {tel}",
        "bron_tasdiqlandi": "✅ *Бронингиз тасдиқланди! #{bid}*\n\n🛏 {xona}\n📅 {sana} | {kunlar} кун\n👥 {kishi} киши\n💰 {narx} сўм\n\n📞 {tel}",
        "bron_rad": "❌ Брон #{bid} рад этилди.\nБоғланинг: {tel}",
        "mos_xona": "✨ *Сизга мос вариант:*",
        "barcha_xonalar": "📋 Барча бўш хоналар",
        "xona_yoq": "❌ Бу санада мос бўш хона йўқ.\n\nБоғланинг:\n📞 {tel}",
        "xizmatlar_matn": "🌿 *Тоғ Тagi Резорт Хизматлари:*\n\n🌊 Соy бўйи\n💦 Шаршара\n🍽 Ошхона *(ўзингиз пишрасиз)*\n🔥 Мангал\n🥩 Шашлик\n📶 WiFi\n📺 Телевизор\n🛏 Ётоқ жойлар\n🛖 Тапчанлар\n🚗 Бепул паркинг\n🌿 Яшил табиат\n\n📞 {tel1}\n📞 {tel2}",
        "manzil_matn": "📍 *Тоғ Тagi Резорт манзили:*\n\nШоҳимардон, Фарғона вилояти\n📌 Кўлқубондан 300 метр пастда\n\n📞 {tel1}\n📞 {tel2}",
        "boglanish_matn": "📞 *Боғланиш:*\n\n📱 {tel1}\n📱 {tel2}\n📸 Instagram: @togtagi\n\n⏰ 24/7",
        "galereya_yoq": "📸 Ҳозирча расм/видео йўқ.",
        "vaqt_tugaydi": "⏰ Ҳурматли мижоз!\n\nХонадаги вақтингиз бугун 12:00 да тугайди.\nИлтимос, хонани бўшатинг.\n\n🛖 Тапчанлардан фойдаланишингиз мумкин!\n\n📞 {tel}",
        "xato": "⚠️ Хатолик.\n\nБоғланинг:\n📞 {tel1}\n📞 {tel2}",
        "til_btn": "🇺🇿 Ўзбек (кирил)",
    },
    "ru": {
        "til_tanlash": "🌐 Tilni tanlang / Выберите язык:",
        "xush_kelibsiz": "🏔 *Tog' Tagi Resort*\n\nОтдохните в горах Шахимардона!\n\n🌊 У реки  |  💦 Водопад\n🍽 Кухня  |  🔥 Мангал\n🛖 Беседки  |  🚗 Бесплатная парковка\n\n📍 В 300 метрах ниже Кулькубона\n\n📞 {tel1}  |  {tel2}",
        "bron": "🛏 Забронировать",
        "bosh_xonalar": "📅 Свободные номера",
        "galereya": "🖼 Галерея",
        "xizmatlar": "🌿 Услуги",
        "manzil": "📍 Адрес",
        "boglanish": "📞 Контакты",
        "bosh_menyu": "🏠 Главное меню",
        "necha_kishi": "👥 *Сколько человек приедет?*\n\nВведите число:",
        "kimlar": "👥 *С кем приедете?*",
        "oila": "👨‍👩‍👧‍👦 С семьёй",
        "dostlar": "👬 С друзьями",
        "qaysi_sana": "📅 *На какую дату?*",
        "sana_tanlang": "👇 Выберите дату:",
        "necha_kun": "На сколько ночей?",
        "ism": "👤 *Введите ваше имя:*",
        "telefon": "📞 *Отправьте номер телефона:*\n\nИли введите: +998901234567",
        "kontakt": "📱 Отправить контакт",
        "tasdiq": "✅ Подтверждаете?",
        "tasdiq_ha": "✅ Подтвердить",
        "bekor": "❌ Отмена",
        "bron_yuborildi": "⏳ *Заявка принята! #{bid}*\n\n🛏 {xona}\n📅 {sana} | {kunlar} ночей\n👥 {kishi} чел.\n💰 {narx} сум\n\nОжидайте подтверждения.\n📞 {tel}",
        "bron_tasdiqlandi": "✅ *Бронь подтверждена! #{bid}*\n\n🛏 {xona}\n📅 {sana} | {kunlar} ночей\n👥 {kishi} чел.\n💰 {narx} сум\n\n📞 {tel}",
        "bron_rad": "❌ Бронь #{bid} отклонена.\nСвяжитесь: {tel}",
        "mos_xona": "✨ *Подходящий вариант:*",
        "barcha_xonalar": "📋 Все свободные номера",
        "xona_yoq": "❌ На эту дату нет подходящих номеров.\n\nСвяжитесь:\n📞 {tel}",
        "xizmatlar_matn": "🌿 *Услуги Tog' Tagi Resort:*\n\n🌊 Берег реки\n💦 Водопад\n🍽 Кухня *(готовите сами)*\n🔥 Мангал\n🥩 Шашлык\n📶 WiFi\n📺 Телевизор\n🛏 Спальные места\n🛖 Беседки\n🚗 Бесплатная парковка\n🌿 Природа\n\n📞 {tel1}\n📞 {tel2}",
        "manzil_matn": "📍 *Адрес Tog' Tagi Resort:*\n\nШахимардон, Ферганская область\n📌 В 300 метрах ниже Кулькубона\n\n📞 {tel1}\n📞 {tel2}",
        "boglanish_matn": "📞 *Контакты:*\n\n📱 {tel1}\n📱 {tel2}\n📸 Instagram: @togtagi\n\n⏰ 24/7",
        "galereya_yoq": "📸 Пока нет фото/видео.",
        "vaqt_tugaydi": "⏰ Уважаемый гость!\n\nВремя вашего проживания истекает сегодня в 12:00.\nПожалуйста, освободите номер.\n\n🛖 Беседки в вашем распоряжении!\n\n📞 {tel}",
        "xato": "⚠️ Ошибка.\n\nСвяжитесь:\n📞 {tel1}\n📞 {tel2}",
        "til_btn": "🇷🇺 Русский",
    }
}

def get_til(uid):
    try:
        with db() as conn:
            row = conn.execute("SELECT til FROM til WHERE user_id=?", (uid,)).fetchone()
            return row["til"] if row else None
    except:
        return None

def set_til(uid, til):
    with db() as conn:
        conn.execute("INSERT OR REPLACE INTO til VALUES (?,?)", (uid, til))
        conn.commit()

def t(uid, kalit, **kwargs):
    til = get_til(uid) or "uz"
    matn = MATNLAR[til].get(kalit, kalit)
    try:
        return matn.format(tel1=TELEFON1, tel2=TELEFON2, tel=TELEFON1, **kwargs)
    except:
        return matn

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
    with db() as conn:
        r = conn.execute("SELECT id FROM band WHERE xona_id=? AND sana=?", (xid, sana)).fetchone()
        return r is not None

def xona_kunlar_band(xid, bosh_sana, kunlar):
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    for i in range(kunlar):
        sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
        if xona_band_mi(xid, sana):
            return True
    return False

def band_qil(xid, bosh_sana, kunlar, bron_id):
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    with db() as conn:
        for i in range(kunlar):
            sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
            conn.execute("INSERT OR IGNORE INTO band (xona_id, sana, bron_id) VALUES (?,?,?)",
                        (xid, sana, bron_id))
        conn.commit()

def bosh_qil(xid, bosh_sana, kunlar):
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    with db() as conn:
        for i in range(kunlar):
            sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
            conn.execute("DELETE FROM band WHERE xona_id=? AND sana=?", (xid, sana))
        conn.commit()

def get_xonalar():
    with db() as conn:
        return conn.execute("SELECT * FROM xonalar ORDER BY id").fetchall()

def mos_kombinatsiya(kishi, guruh, sana, kunlar=1):
    xonalar = get_xonalar()
    bosh = [x for x in xonalar if not xona_kunlar_band(x["id"], sana, kunlar)]
    if not bosh:
        return []
    for x in sorted(bosh, key=lambda a: a["sigim"]):
        if x["sigim"] >= kishi:
            return [x]
    afzal_qavat = 1 if guruh == "oila" else 2
    afzal = sorted([x for x in bosh if x["qavat"] == afzal_qavat], key=lambda a: a["sigim"], reverse=True)
    boshqa = sorted([x for x in bosh if x["qavat"] != afzal_qavat], key=lambda a: a["sigim"], reverse=True)
    tartiblangan = afzal + boshqa
    tanlangan = []
    jami = 0
    for x in tartiblangan:
        if jami >= kishi:
            break
        tanlangan.append(x)
        jami += x["sigim"]
    return tanlangan if jami >= kishi else []

def xato_xabar(cid):
    uid = cid
    bot.send_message(cid, t(uid, "xato"), reply_markup=asosiy_menu(uid))

def sana_tugmalari():
    kb = types.InlineKeyboardMarkup(row_width=5)
    bugun = datetime.now().date()
    tugmalar = []
    for i in range(30):
        kun = bugun + timedelta(days=i)
        tugmalar.append(types.InlineKeyboardButton(
            kun.strftime("%d/%m"), callback_data=f"sana_{kun.strftime('%d.%m.%Y')}"))
    kb.add(*tugmalar)
    return kb

def kunlar_tugmalari():
    kb = types.InlineKeyboardMarkup(row_width=5)
    tugmalar = [types.InlineKeyboardButton(f"{i} kun", callback_data=f"kun_{i}") for i in range(1, 16)]
    kb.add(*tugmalar)
    return kb

# ==================== MENYULAR ====================

def asosiy_menu(uid):
    til = get_til(uid) or "uz"
    m = MATNLAR[til]
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(m["bron"], m["bosh_xonalar"], m["galereya"], m["xizmatlar"], m["manzil"], m["boglanish"])
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        "🏨 Xonalar boshqaruvi", "📋 Bronlar ro'yxati",
        "📊 Bugungi holat", "👥 Mijozlar bazasi",
        "➕ Tezkor bron", "📸 Umumiy rasm",
        "🎥 Video yuklash", "📄 Hisobot",
        "🔙 Asosiy menyu"
    )
    return kb

def xonalar_boshqaruv_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for x in get_xonalar():
        qavat = "🏠" if x["qavat"] == 1 else "🏢"
        with db() as conn:
            rasmlar = conn.execute("SELECT COUNT(*) as cnt FROM xona_rasmlar WHERE xona_id=?", (x["id"],)).fetchone()["cnt"]
        rasm_txt = f" 📸{rasmlar}" if rasmlar else ""
        kb.add(types.InlineKeyboardButton(
            f"{qavat} {x['nomi']} ({x['sigim']} kishi){rasm_txt}",
            callback_data=f"admin_xona_{x['id']}"))
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

def til_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🇺🇿 O'zbek (lotin)", callback_data="til_uz"),
        types.InlineKeyboardButton("🇺🇿 Ўзбек (кирил)", callback_data="til_uz_kril"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="til_ru"),
    )
    return kb

# ==================== START ====================

@bot.message_handler(commands=["start", "bron", "xonalar", "xizmatlar", "manzil", "boglanish"])
def start(msg):
    uid = msg.from_user.id
    til = get_til(uid)
    if not til:
        bot.send_message(uid, "🌐 Tilni tanlang / Выберите язык:", reply_markup=til_menu())
        return
    if msg.text and not msg.text == "/start":
        if "/bron" in msg.text: bron_start(msg); return
        if "/xonalar" in msg.text: bosh_xonalar_cmd(msg); return
        if "/xizmatlar" in msg.text: xizmatlar_cmd(msg); return
        if "/manzil" in msg.text: manzil_cmd(msg); return
        if "/boglanish" in msg.text: boglanish_cmd(msg); return
    user_state.pop(uid, None)
    bot.send_message(uid, t(uid, "xush_kelibsiz"), parse_mode="Markdown", reply_markup=asosiy_menu(uid))

@bot.message_handler(commands=["admin"])
def admin_panel(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "❌ Ruxsat yo'q")
        return
    user_state[msg.chat.id] = {"mode": "admin"}
    bot.send_message(msg.chat.id, "👨‍💼 *Admin panel*", parse_mode="Markdown", reply_markup=admin_menu())

# ==================== TIL CALLBACK ====================

@bot.callback_query_handler(func=lambda c: c.data.startswith("til_"))
def cb_til(call):
    uid = call.from_user.id
    til = call.data.replace("til_", "")
    set_til(uid, til)
    user_state.pop(uid, None)
    bot.edit_message_text("✅", call.message.chat.id, call.message.message_id)
    bot.send_message(uid, t(uid, "xush_kelibsiz"), parse_mode="Markdown", reply_markup=asosiy_menu(uid))
    bot.answer_callback_query(call.id)

# ==================== MIJOZ HANDLERLAR ====================

def bron_start(msg):
    uid = msg.from_user.id
    with db() as conn:
        blok = conn.execute("SELECT bloklangan FROM mijozlar WHERE user_id=?", (uid,)).fetchone()
        if blok and blok["bloklangan"]:
            bot.send_message(uid, f"❌ Bog'laning: {TELEFON1}")
            return
    user_state[uid] = {"step": "kishi"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    for i in range(1, 11): kb.add(str(i))
    kb.add(t(uid, "bosh_menyu"))
    bot.send_message(uid, t(uid, "necha_kishi"), parse_mode="Markdown", reply_markup=kb)

def bosh_xonalar_cmd(msg):
    uid = msg.from_user.id
    user_state[uid] = {"step": "bosh_kishi"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    for i in range(1, 11): kb.add(str(i))
    kb.add(t(uid, "bosh_menyu"))
    bot.send_message(uid, t(uid, "necha_kishi"), parse_mode="Markdown", reply_markup=kb)

def xizmatlar_cmd(msg):
    uid = msg.from_user.id
    bot.send_message(uid, t(uid, "xizmatlar_matn"), parse_mode="Markdown")

def manzil_cmd(msg):
    uid = msg.from_user.id
    bot.send_message(uid, t(uid, "manzil_matn"), parse_mode="Markdown")
    bot.send_location(uid, latitude=39.961311, longitude=71.836921)

def boglanish_cmd(msg):
    uid = msg.from_user.id
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(f"📞 {TELEFON1}", url=f"tel:{TELEFON1}"),
        types.InlineKeyboardButton(f"📞 {TELEFON2}", url=f"tel:{TELEFON2}"),
        types.InlineKeyboardButton("📸 Instagram", url=INSTAGRAM),
        types.InlineKeyboardButton(t(uid, "bron"), callback_data="bron_start"),
    )
    bot.send_message(uid, t(uid, "boglanish_matn"), parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: any(
    m.text == MATNLAR[til]["bron"] for til in MATNLAR))
def h_bron(msg): bron_start(msg)

@bot.message_handler(func=lambda m: any(
    m.text == MATNLAR[til]["bosh_xonalar"] for til in MATNLAR))
def h_bosh(msg): bosh_xonalar_cmd(msg)

@bot.message_handler(func=lambda m: any(
    m.text == MATNLAR[til]["xizmatlar"] for til in MATNLAR))
def h_xizmat(msg): xizmatlar_cmd(msg)

@bot.message_handler(func=lambda m: any(
    m.text == MATNLAR[til]["manzil"] for til in MATNLAR))
def h_manzil(msg): manzil_cmd(msg)

@bot.message_handler(func=lambda m: any(
    m.text == MATNLAR[til]["boglanish"] for til in MATNLAR))
def h_boglanish(msg): boglanish_cmd(msg)

@bot.message_handler(func=lambda m: any(
    m.text == MATNLAR[til]["galereya"] for til in MATNLAR))
def h_galereya(msg):
    uid = msg.from_user.id
    with db() as conn:
        photos = conn.execute("SELECT file_id FROM media WHERE tur='photo'").fetchall()
        videos = conn.execute("SELECT file_id FROM media WHERE tur='video'").fetchall()
    if not photos and not videos:
        bot.send_message(uid, t(uid, "galereya_yoq"))
        return
    bot.send_message(uid, "🖼 *Tog' Tagi Resort — Galereya:*", parse_mode="Markdown")
    for p in photos[:10]:
        try: bot.send_photo(uid, p["file_id"])
        except: pass
    for v in videos[:5]:
        try: bot.send_video(uid, v["file_id"])
        except: pass

@bot.message_handler(func=lambda m: any(
    m.text == MATNLAR[til]["bosh_menyu"] for til in MATNLAR))
def h_bosh_menyu(msg):
    uid = msg.from_user.id
    user_state.pop(uid, None)
    bot.send_message(uid, "👇", reply_markup=asosiy_menu(uid))

# ==================== ADMIN HANDLERLAR ====================

@bot.message_handler(func=lambda m: m.text == "🔙 Asosiy menyu" and is_admin(m.from_user.id))
def admin_back(msg):
    user_state.pop(msg.chat.id, None)
    bot.send_message(msg.chat.id, "Asosiy menyu", reply_markup=asosiy_menu(msg.from_user.id))

@bot.message_handler(func=lambda m: m.text == "🏨 Xonalar boshqaruvi" and is_admin(m.from_user.id))
def h_xonalar_boshqaruvi(msg):
    bot.send_message(msg.chat.id, "🏨 *Xonalar:*", parse_mode="Markdown", reply_markup=xonalar_boshqaruv_menu())

@bot.message_handler(func=lambda m: m.text == "📊 Bugungi holat" and is_admin(m.from_user.id))
def bugungi_holat(msg):
    bugun = datetime.now().strftime("%d.%m.%Y")
    matn = f"📊 *Bugungi holat ({bugun}):*\n\n"
    with db() as conn:
        for x in get_xonalar():
            h = "🔴 Band" if xona_band_mi(x["id"], bugun) else "🟢 Bo'sh"
            band_info = ""
            if xona_band_mi(x["id"], bugun):
                brow = conn.execute("SELECT bron_id FROM band WHERE xona_id=? AND sana=?",
                                   (x["id"], bugun)).fetchone()
                if brow and brow["bron_id"] != "admin":
                    bron = conn.execute("SELECT * FROM bronlar WHERE id=?",
                                      (brow["bron_id"],)).fetchone()
                    if bron:
                        band_info = f"\n   👤 {bron['ism']} | 📞 {bron['telefon']}"
                        son = bron["kunlar"]
                        bosh_sana = datetime.strptime(bron["sana"], "%d.%m.%Y")
                        tugash = bosh_sana + timedelta(days=son)
                        band_info += f"\n   📅 {bron['sana']} — {tugash.strftime('%d.%m.%Y')}"
            qavat = "🏠" if x["qavat"] == 1 else "🏢"
            matn += f"{qavat} *{x['nomi']}* — {h}{band_info}\n\n"
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "📋 Bronlar ro'yxati" and is_admin(m.from_user.id))
def bronlar_royxati(msg):
    bugun = datetime.now().date()
    oxiri = bugun + timedelta(days=10)
    with db() as conn:
        bronlar = conn.execute(
            "SELECT * FROM bronlar WHERE sana >= ? AND sana <= ? ORDER BY sana",
            (bugun.strftime("%d.%m.%Y"), oxiri.strftime("%d.%m.%Y"))
        ).fetchall()
    if not bronlar:
        bot.send_message(msg.chat.id, "📋 Kelayotgan 10 kunda bron yo'q", reply_markup=admin_menu())
        return
    matn = "📋 *Kelayotgan 10 kunlik bronlar:*\n\n"
    for b in bronlar:
        tasdiq = "✅" if b["tasdiqlangan"] else "⏳"
        matn += (f"{tasdiq} *#{b['id']}* | {b['xona']}\n"
                 f"👤 {b['ism']} | 📞 {b['telefon']}\n"
                 f"📅 {b['sana']} | {b['kunlar']} kun | 👥 {b['kishi']} kishi\n"
                 f"💰 {format_narx(b['narx'])} so'm\n\n")
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "👥 Mijozlar bazasi" and is_admin(m.from_user.id))
def mijozlar_bazasi(msg):
    user_state[msg.chat.id] = {"step": "admin_mijoz_qidir", "mode": "admin"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Admin menyu")
    bot.send_message(msg.chat.id, "👥 Mijoz telefon yoki bron ID kiriting:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "➕ Tezkor bron" and is_admin(m.from_user.id))
def tezkor_bron(msg):
    user_state[msg.chat.id] = {"step": "admin_tezkor_kishi", "mode": "admin", "ab": {}}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    for i in range(1, 11): kb.add(str(i))
    kb.add("🔙 Admin menyu")
    bot.send_message(msg.chat.id, "➕ *Tezkor bron*\n\nNechta kishi?", parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📸 Umumiy rasm" and is_admin(m.from_user.id))
def umumiy_rasm(msg):
    user_state[msg.chat.id] = {"step": "admin_umumiy_rasm", "mode": "admin"}
    bot.send_message(msg.chat.id, "📸 Umumiy rasmlar yuboring.\n/done — tugallash")

@bot.message_handler(func=lambda m: m.text == "🎥 Video yuklash" and is_admin(m.from_user.id))
def admin_video(msg):
    user_state[msg.chat.id] = {"step": "admin_video", "mode": "admin"}
    bot.send_message(msg.chat.id, "🎥 Video yuboring.\n/done — tugallash")

@bot.message_handler(func=lambda m: m.text == "📄 Hisobot" and is_admin(m.from_user.id))
def hisobot(msg):
    with db() as conn:
        bronlar = conn.execute("SELECT * FROM bronlar ORDER BY created_at DESC").fetchall()
    if not bronlar:
        bot.send_message(msg.chat.id, "Hozircha bron yo'q")
        return
    matn = "BRONLAR RO'YXATI\n" + "="*40 + "\n\n"
    for b in bronlar:
        tasdiq = "TASDIQLANGAN" if b["tasdiqlangan"] else "KUTILMOQDA"
        matn += (f"#{b['id']} | {b['xona']} | {tasdiq}\n"
                 f"Ism: {b['ism']}\nTel: {b['telefon']}\n"
                 f"Sana: {b['sana']} | {b['kunlar']} kun\n"
                 f"Kishi: {b['kishi']} | Narx: {format_narx(b['narx'])} som\n"
                 + "-"*30 + "\n")
    buf = BytesIO(matn.encode("utf-8"))
    buf.name = "bronlar.txt"
    bot.send_document(msg.chat.id, buf, caption="📄 Bronlar ro'yxati")

@bot.message_handler(func=lambda m: m.text == "🔙 Admin menyu" and is_admin(m.from_user.id))
def admin_menyu_back(msg):
    user_state[msg.chat.id] = {"mode": "admin"}
    bot.send_message(msg.chat.id, "Admin panel 👇", reply_markup=admin_menu())

@bot.message_handler(commands=["done"])
def cmd_done(msg):
    if not is_admin(msg.from_user.id): return
    state = user_state.get(msg.chat.id, {})
    xid = state.get("rasm_xona_id")
    if xid:
        bot.send_message(msg.chat.id, f"✅ {dict(get_xonalar()[xid-1])['nomi']} rasmlari saqlandi!", reply_markup=admin_menu())
    else:
        bot.send_message(msg.chat.id, "✅ Saqlandi!", reply_markup=admin_menu())
    user_state[msg.chat.id] = {"mode": "admin"}

@bot.message_handler(content_types=["photo"])
def photo_handler(msg):
    state = user_state.get(msg.chat.id, {})
    if not is_admin(msg.from_user.id): return
    step = state.get("step")
    with db() as conn:
        if step == "admin_umumiy_rasm":
            conn.execute("INSERT INTO media (tur, file_id) VALUES ('photo', ?)", (msg.photo[-1].file_id,))
            conn.commit()
            cnt = conn.execute("SELECT COUNT(*) as c FROM media WHERE tur='photo'").fetchone()["c"]
            bot.send_message(msg.chat.id, f"✅ Saqlandi! Jami: {cnt} ta\n/done — tugallash")
        elif step == "admin_xona_rasm":
            xid = state.get("rasm_xona_id")
            if xid:
                conn.execute("INSERT INTO xona_rasmlar (xona_id, file_id) VALUES (?,?)", (xid, msg.photo[-1].file_id))
                conn.commit()
                cnt = conn.execute("SELECT COUNT(*) as c FROM xona_rasmlar WHERE xona_id=?", (xid,)).fetchone()["c"]
                bot.send_message(msg.chat.id, f"✅ Saqlandi! Jami: {cnt} ta\n/done — tugallash")

@bot.message_handler(content_types=["video"])
def video_handler(msg):
    state = user_state.get(msg.chat.id, {})
    if is_admin(msg.from_user.id) and state.get("step") == "admin_video":
        with db() as conn:
            conn.execute("INSERT INTO media (tur, file_id) VALUES ('video', ?)", (msg.video.file_id,))
            conn.commit()
            cnt = conn.execute("SELECT COUNT(*) as c FROM media WHERE tur='video'").fetchone()["c"]
        bot.send_message(msg.chat.id, f"✅ Video saqlandi! Jami: {cnt} ta\n/done — tugallash")

@bot.message_handler(content_types=["contact"])
def contact_handler(msg):
    state = user_state.get(msg.chat.id, {})
    if state.get("step") == "telefon":
        tel = msg.contact.phone_number
        if not tel.startswith("+"): tel = "+" + tel
        state["telefon"] = tel
        user_state[msg.chat.id] = state
        _tasdiqlash_yuborim(msg.chat.id)

# ==================== CALLBACK ====================

@bot.callback_query_handler(func=lambda c: c.data == "bron_start")
def cb_bron_start(call):
    uid = call.from_user.id
    user_state[uid] = {"step": "kishi"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    for i in range(1, 11): kb.add(str(i))
    kb.add(t(uid, "bosh_menyu"))
    bot.send_message(uid, t(uid, "necha_kishi"), parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("sana_"))
def cb_sana(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    sana = call.data.replace("sana_", "")
    state = user_state.get(cid, {})

    if is_admin(uid) and state.get("step") in ["admin_tezkor_sana", "ax_band_sana", "ax_bosh_sana"]:
        step = state.get("step")
        if step == "admin_tezkor_sana":
            state["ab"]["sana"] = sana
            state["step"] = "admin_tezkor_kunlar"
            user_state[cid] = state
            bot.send_message(cid, f"📅 {sana}\n\nNecha kun?", reply_markup=kunlar_tugmalari())
        elif step == "ax_band_sana":
            state["ax_sana"] = sana
            state["step"] = "ax_band_kunlar"
            user_state[cid] = state
            bot.send_message(cid, f"📅 {sana}\n\nNecha kun band?", reply_markup=kunlar_tugmalari())
        elif step == "ax_bosh_sana":
            state["ax_sana"] = sana
            state["step"] = "ax_bosh_kunlar"
            user_state[cid] = state
            bot.send_message(cid, f"📅 {sana}\n\nNecha kun bo'sh?", reply_markup=kunlar_tugmalari())
        bot.answer_callback_query(call.id)
        return

    state["sana"] = sana
    state["step"] = "kunlar"
    user_state[cid] = state
    bot.edit_message_text(f"📅 {sana}\n\n{t(uid, 'necha_kun')}",
                          cid, call.message.message_id,
                          reply_markup=kunlar_tugmalari())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("kun_"))
def cb_kun(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    kunlar = int(call.data.replace("kun_", ""))
    state = user_state.get(cid, {})

    if is_admin(uid) and state.get("step") in ["admin_tezkor_kunlar", "ax_band_kunlar", "ax_bosh_kunlar"]:
        step = state.get("step")
        if step == "admin_tezkor_kunlar":
            state["ab"]["kunlar"] = kunlar
            state["step"] = "admin_tezkor_xona"
            user_state[cid] = state
            sana = state["ab"]["sana"]
            kishi = state["ab"].get("kishi", 1)
            kombinatsiya = mos_kombinatsiya(kishi, "oila", sana, kunlar)
            if not kombinatsiya:
                bot.send_message(cid, f"❌ {sana} da bo'sh xona yo'q")
                bot.answer_callback_query(call.id)
                return
            kb = types.InlineKeyboardMarkup(row_width=1)
            for x in kombinatsiya:
                narx = format_narx(x["narx"] * kunlar)
                kb.add(types.InlineKeyboardButton(
                    f"🛏 {x['nomi']} | {x['sigim']} kishi | {narx} so'm",
                    callback_data=f"atx_{x['id']}"))
            kb.add(types.InlineKeyboardButton("📋 Barchasi", callback_data="atx_barchasi"))
            bot.send_message(cid, f"✅ {sana} | {kunlar} kun | {kishi} kishi\n\nXonani tanlang:", reply_markup=kb)
        elif step == "ax_band_kunlar":
            xid = state["ax_xid"]
            band_qil(xid, state["ax_sana"], kunlar, "admin")
            user_state[cid] = {"mode": "admin"}
            with db() as conn:
                x = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()
            bot.send_message(cid, f"✅ {x['nomi']} — {state['ax_sana']} dan {kunlar} kun BAND", reply_markup=admin_menu())
        elif step == "ax_bosh_kunlar":
            xid = state["ax_xid"]
            bosh_qil(xid, state["ax_sana"], kunlar)
            user_state[cid] = {"mode": "admin"}
            with db() as conn:
                x = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()
            bot.send_message(cid, f"✅ {x['nomi']} — {state['ax_sana']} dan {kunlar} kun BO'SH", reply_markup=admin_menu())
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
            t(uid, "xona_yoq").format(tel=TELEFON1),
            cid, call.message.message_id, reply_markup=sana_tugmalari())
        bot.answer_callback_query(call.id)
        return

    jami_narx = sum(x["narx"] for x in kombinatsiya) * kunlar
    xona_nomlari = " + ".join(x["nomi"] for x in kombinatsiya)

    matn = f"📅 *{sana}* | {kunlar} kun | 👥 *{kishi} kishi*\n\n{t(uid, 'mos_xona')}\n\n"
    for x in kombinatsiya:
        qavat = "🏠" if x["qavat"] == 1 else "🏢"
        matn += f"{qavat} *{x['nomi']}* | 👥 {x['sigim']} kishi | 💰 {format_narx(x['narx']*kunlar)} so'm\n\n"
    if len(kombinatsiya) > 1:
        matn += f"💰 *Jami: {format_narx(jami_narx)} so'm*\n\n"
    matn += "👇"

    kb = types.InlineKeyboardMarkup(row_width=1)
    ids = "_".join(str(x["id"]) for x in kombinatsiya)
    kb.add(types.InlineKeyboardButton(
        f"✅ {xona_nomlari} — {format_narx(jami_narx)} so'm",
        callback_data=f"kombina_{ids}_{sana}_{kunlar}"))
    kb.add(types.InlineKeyboardButton(t(uid, "barcha_xonalar"),
                                       callback_data=f"barcha_{sana}_{kunlar}"))
    bot.edit_message_text(matn, cid, call.message.message_id,
                          parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("barcha_"))
def cb_barcha(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    parts = call.data.split("_")
    sana, kunlar = parts[1], int(parts[2])
    kb = types.InlineKeyboardMarkup(row_width=1)
    for x in get_xonalar():
        if not xona_kunlar_band(x["id"], sana, kunlar):
            qavat = "🏠" if x["qavat"] == 1 else "🏢"
            kb.add(types.InlineKeyboardButton(
                f"{qavat} {x['nomi']} | {x['sigim']} 👤 | {format_narx(x['narx']*kunlar)} so'm",
                callback_data=f"kombina_{x['id']}_{sana}_{kunlar}"))
    bot.edit_message_text(f"📅 {sana} | {kunlar} kun\n\n📋 *Bo'sh xonalar:*",
                          cid, call.message.message_id,
                          parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("kombina_"))
def cb_kombina(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    parts = call.data.split("_")
    kunlar = int(parts[-1])
    sana = parts[-2]
    xid_list = [int(x) for x in parts[1:-2]]

    state = user_state.get(cid, {})
    with db() as conn:
        xonalar_info = [dict(conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()) for xid in xid_list]
    jami_narx = sum(x["narx"] for x in xonalar_info) * kunlar
    xona_nomi = " + ".join(x["nomi"] for x in xonalar_info)

    state.update({"xona_ids": xid_list, "sana": sana, "kunlar": kunlar,
                  "xona_nomi": xona_nomi, "jami_narx": jami_narx, "step": "ism"})
    user_state[cid] = state

    # Xona rasmlarini yuborish
    for xid in xid_list:
        with db() as conn:
            rasmlar = conn.execute("SELECT file_id FROM xona_rasmlar WHERE xona_id=?", (xid,)).fetchall()
        if rasmlar:
            with db() as conn:
                xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
            bot.send_message(cid, f"📸 *{xnomi}:*", parse_mode="Markdown")
            for r in rasmlar[:5]:
                try: bot.send_photo(cid, r["file_id"])
                except: pass

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(t(uid, "bosh_menyu"))
    bot.edit_message_text(
        f"✅ *{xona_nomi}* tanlandi\n📅 {sana} | {kunlar} kun\n💰 {format_narx(jami_narx)} so'm\n\n{t(uid, 'ism')}",
        cid, call.message.message_id, parse_mode="Markdown")
    bot.send_message(cid, "👇", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_tasdiq_"))
def cb_admin_tasdiq(call):
    if not is_admin(call.from_user.id): return
    parts = call.data.split("_")
    action = parts[2]
    bron_id = parts[3]

    with db() as conn:
        b = conn.execute("SELECT * FROM bronlar WHERE id=?", (bron_id,)).fetchone()
    if not b:
        bot.answer_callback_query(call.id, "Bron topilmadi")
        return

    if action == "ha":
        xid_list = []
        with db() as conn:
            rows = conn.execute("SELECT xona_id FROM bron_xonalar WHERE bron_id=?", (bron_id,)).fetchall()
            xid_list = [r["xona_id"] for r in rows]
            conn.execute("UPDATE bronlar SET tasdiqlangan=1 WHERE id=?", (bron_id,))
            conn.commit()
        for xid in xid_list:
            band_qil(xid, b["sana"], b["kunlar"], bron_id)
        try:
            uid = b["user_id"]
            til = get_til(uid) or "uz"
            bot.send_message(uid, t(uid, "bron_tasdiqlandi").format(
                bid=bron_id, xona=b["xona"], sana=b["sana"],
                kunlar=b["kunlar"], kishi=b["kishi"],
                narx=format_narx(b["narx"]), tel=TELEFON1),
                parse_mode="Markdown")
        except: pass
        bot.edit_message_text(f"✅ #{bron_id} TASDIQLANDI | {b['ism']}",
                              call.message.chat.id, call.message.message_id)
    else:
        with db() as conn:
            conn.execute("DELETE FROM bronlar WHERE id=?", (bron_id,))
            conn.execute("DELETE FROM bron_xonalar WHERE bron_id=?", (bron_id,))
            conn.commit()
        try:
            uid = b["user_id"]
            bot.send_message(uid, t(uid, "bron_rad").format(bid=bron_id, tel=TELEFON1))
        except: pass
        bot.edit_message_text(f"❌ #{bron_id} RAD ETILDI",
                              call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

# ==================== ADMIN XONA ====================

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_xona_"))
def cb_admin_xona(call):
    if not is_admin(call.from_user.id): return
    xid = int(call.data.replace("admin_xona_", ""))
    with db() as conn:
        x = conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()
        rasmlar = conn.execute("SELECT COUNT(*) as c FROM xona_rasmlar WHERE xona_id=?", (xid,)).fetchone()["c"]
    bugun = datetime.now().strftime("%d.%m.%Y")
    h = "🔴 Band" if xona_band_mi(xid, bugun) else "🟢 Bo'sh"
    matn = (f"🛏 *{x['nomi']}*\n"
            f"{'🏠 1-qavat' if x['qavat']==1 else '🏢 2-qavat'} | 👥 {x['sigim']} kishi\n"
            f"💰 {format_narx(x['narx'])} so'm | Bugun: {h}\n"
            f"📸 Rasmlar: {rasmlar} ta")
    bot.edit_message_text(matn, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=xona_admin_kb(xid))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ax_bronlar_"))
def cb_ax_bronlar(call):
    if not is_admin(call.from_user.id): return
    xid = int(call.data.replace("ax_bronlar_", ""))
    with db() as conn:
        x = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()
        bron_ids = conn.execute("SELECT bron_id FROM bron_xonalar WHERE xona_id=?", (xid,)).fetchall()
        bronlar = []
        for r in bron_ids:
            b = conn.execute("SELECT * FROM bronlar WHERE id=?", (r["bron_id"],)).fetchone()
            if b: bronlar.append(b)
    matn = f"🛏 *{x['nomi']}* bronlari:\n\n"
    if bronlar:
        for b in bronlar[-8:]:
            tasdiq = "✅" if b["tasdiqlangan"] else "⏳"
            matn += f"{tasdiq} *#{b['id']}* | {b['sana']} | {b['kunlar']} kun\n👤 {b['ism']} | 📞 {b['telefon']}\n\n"
    else:
        matn += "Bron yo'q\n\n"
    matn += "📅 *15 kunlik holat:*\n"
    bugun = datetime.now().date()
    for i in range(15):
        kun = bugun + timedelta(days=i)
        sana_str = kun.strftime("%d.%m.%Y")
        h = "🔴" if xona_band_mi(xid, sana_str) else "🟢"
        matn += f"{h}{kun.strftime('%d/%m')} "
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
    with db() as conn:
        x = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()
    bot.send_message(call.message.chat.id,
        f"🔴 *{x['nomi']}* band qilish\n\n📅 Boshlanish sanasini tanlang:",
        parse_mode="Markdown", reply_markup=sana_tugmalari())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ax_bosh_"))
def cb_ax_bosh(call):
    if not is_admin(call.from_user.id): return
    xid = int(call.data.replace("ax_bosh_", ""))
    user_state[call.message.chat.id] = {"step": "ax_bosh_sana", "mode": "admin", "ax_xid": xid}
    with db() as conn:
        x = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()
    bot.send_message(call.message.chat.id,
        f"🟢 *{x['nomi']}* bo'sh qilish\n\n📅 Sanani tanlang:",
        parse_mode="Markdown", reply_markup=sana_tugmalari())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ax_rasm_"))
def cb_ax_rasm(call):
    if not is_admin(call.from_user.id): return
    xid = int(call.data.replace("ax_rasm_", ""))
    user_state[call.message.chat.id] = {"step": "admin_xona_rasm", "mode": "admin", "rasm_xona_id": xid}
    with db() as conn:
        x = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()
    bot.send_message(call.message.chat.id,
        f"📸 *{x['nomi']}* uchun rasmlar yuboring.\n/done — tugallash",
        parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "ax_back")
def cb_ax_back(call):
    if not is_admin(call.from_user.id): return
    bot.edit_message_text("🏨 *Xonalar:*", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=xonalar_boshqaruv_menu())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("atx_"))
def cb_atx(call):
    if not is_admin(call.from_user.id): return
    cid = call.message.chat.id
    state = user_state.get(cid, {})
    ab = state.get("ab", {})
    if call.data == "atx_barchasi":
        sana = ab.get("sana", "")
        kunlar = ab.get("kunlar", 1)
        kb = types.InlineKeyboardMarkup(row_width=1)
        for x in get_xonalar():
            if not xona_kunlar_band(x["id"], sana, kunlar):
                kb.add(types.InlineKeyboardButton(
                    f"{'🏠' if x['qavat']==1 else '🏢'} {x['nomi']} | {x['sigim']} kishi",
                    callback_data=f"atx_{x['id']}"))
        bot.send_message(cid, "📋 Barcha bo'sh xonalar:", reply_markup=kb)
    else:
        xid = int(call.data.replace("atx_", ""))
        with db() as conn:
            x = conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()
        ab["xona_ids"] = [xid]
        ab["xona_nomi"] = x["nomi"]
        ab["narx"] = x["narx"] * ab.get("kunlar", 1)
        state["ab"] = ab
        state["step"] = "admin_tezkor_ism"
        user_state[cid] = state
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(cid, f"✅ {x['nomi']} tanlandi\n\nMijoz ismi:", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("block_"))
def cb_block(call):
    if not is_admin(call.from_user.id): return
    uid = int(call.data.replace("block_", ""))
    with db() as conn:
        conn.execute("UPDATE mijozlar SET bloklangan=1 WHERE user_id=?", (uid,))
        conn.commit()
    bot.edit_message_text(f"🚫 {uid} bloklandi", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "Bloklandi!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("unblock_"))
def cb_unblock(call):
    if not is_admin(call.from_user.id): return
    uid = int(call.data.replace("unblock_", ""))
    with db() as conn:
        conn.execute("UPDATE mijozlar SET bloklangan=0 WHERE user_id=?", (uid,))
        conn.commit()
    bot.edit_message_text(f"✅ {uid} blokdan chiqarildi", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "Blok ochildi!")

# ==================== TASDIQLASH ====================

def _tasdiqlash_yuborim(cid):
    uid = cid
    state = user_state.get(cid, {})
    try:
        xona_nomi = state["xona_nomi"]
        jami_narx = state["jami_narx"]
        matn = (f"📋 *{t(uid, 'tasdiq')}*\n\n"
                f"👤 {state['ism']}\n📞 {state['telefon']}\n"
                f"📅 {state['sana']} | {state['kunlar']} kun\n"
                f"👥 {state['kishi']} kishi\n"
                f"🛏 {xona_nomi}\n💰 {format_narx(jami_narx)} so'm")
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton(t(uid, "tasdiq_ha"), callback_data="mijoz_tasdiq_ha"),
            types.InlineKeyboardButton(t(uid, "bekor"), callback_data="mijoz_tasdiq_yoq"))
        bot.send_message(cid, matn, parse_mode="Markdown", reply_markup=kb)
        state["step"] = "tasdiq"
        user_state[cid] = state
    except Exception as e:
        logging.error(e)
        xato_xabar(cid)

@bot.callback_query_handler(func=lambda c: c.data.startswith("mijoz_tasdiq_"))
def cb_mijoz_tasdiq(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    if call.data == "mijoz_tasdiq_ha":
        state = user_state.get(cid, {})
        try:
            bron_id = bron_id_gen()
            with db() as conn:
                while conn.execute("SELECT id FROM bronlar WHERE id=?", (bron_id,)).fetchone():
                    bron_id = bron_id_gen()
                conn.execute("""INSERT INTO bronlar
                    (id,ism,telefon,sana,kunlar,kishi,xona,narx,tasdiqlangan,user_id,username,created_at)
                    VALUES (?,?,?,?,?,?,?,?,0,?,?,?)""",
                    (bron_id, state["ism"], state["telefon"], state["sana"],
                     state["kunlar"], state["kishi"], state["xona_nomi"],
                     state["jami_narx"], uid, call.from_user.username or "yoq",
                     datetime.now().strftime("%d.%m.%Y %H:%M")))
                for xid in state["xona_ids"]:
                    conn.execute("INSERT INTO bron_xonalar VALUES (?,?)", (bron_id, xid))
                conn.execute("""INSERT OR REPLACE INTO mijozlar (telefon,ism,user_id,username,bloklangan)
                    VALUES (?,?,?,?,0)""",
                    (state["telefon"], state["ism"], uid, call.from_user.username or "yoq"))
                conn.commit()

            bot.edit_message_text(
                t(uid, "bron_yuborildi").format(
                    bid=bron_id, xona=state["xona_nomi"], sana=state["sana"],
                    kunlar=state["kunlar"], kishi=state["kishi"],
                    narx=format_narx(state["jami_narx"]), tel=TELEFON1),
                cid, call.message.message_id, parse_mode="Markdown")
            bot.send_message(cid, "👇", reply_markup=asosiy_menu(uid))

            admin_kb = types.InlineKeyboardMarkup()
            admin_kb.add(
                types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_tasdiq_ha_{bron_id}"),
                types.InlineKeyboardButton("❌ Rad etish", callback_data=f"admin_tasdiq_yoq_{bron_id}"))
            admin_txt = (f"🔔 *YANGI BRON #{bron_id}*\n\n"
                        f"👤 {state['ism']}\n📞 {state['telefon']}\n"
                        f"📅 {state['sana']} | {state['kunlar']} kun\n"
                        f"👥 {state['kishi']} kishi\n🛏 {state['xona_nomi']}\n"
                        f"💰 {format_narx(state['jami_narx'])} so'm\n"
                        f"💬 @{call.from_user.username or 'yoq'}")
            for admin_id in ADMIN_IDS:
                try: bot.send_message(admin_id, admin_txt, parse_mode="Markdown", reply_markup=admin_kb)
                except: pass
            user_state.pop(cid, None)
        except Exception as e:
            logging.error(e)
            xato_xabar(cid)
    else:
        user_state.pop(cid, None)
        bot.edit_message_text(t(uid, "bekor"), cid, call.message.message_id)
        bot.send_message(cid, "👇", reply_markup=asosiy_menu(uid))
    bot.answer_callback_query(call.id)

# ==================== UMUMIY XABARLAR ====================

@bot.message_handler(func=lambda m: True)
def barcha(msg):
    cid = msg.chat.id
    uid = msg.from_user.id
    state = user_state.get(cid, {})
    step = state.get("step")

    # Admin mijoz qidirish
    if step == "admin_mijoz_qidir" and is_admin(uid):
        qidiruv = msg.text.strip()
        with db() as conn:
            # Bron ID bo'yicha qidirish
            bron = conn.execute("SELECT * FROM bronlar WHERE id=?", (qidiruv.upper(),)).fetchone()
            if bron:
                mijoz = conn.execute("SELECT * FROM mijozlar WHERE telefon=?", (bron["telefon"],)).fetchone()
                blok = "🚫 Bloklangan" if mijoz and mijoz["bloklangan"] else "✅ Faol"
                matn = (f"🎫 Bron *#{bron['id']}*\n\n"
                       f"👤 {bron['ism']} | {blok}\n📞 {bron['telefon']}\n"
                       f"📅 {bron['sana']} | {bron['kunlar']} kun\n"
                       f"🛏 {bron['xona']}\n💰 {format_narx(bron['narx'])} so'm")
                kb = types.InlineKeyboardMarkup()
                if mijoz:
                    if mijoz["bloklangan"]:
                        kb.add(types.InlineKeyboardButton("✅ Blokdan chiqarish", callback_data=f"unblock_{mijoz['user_id']}"))
                    else:
                        kb.add(types.InlineKeyboardButton("🚫 Bloklash", callback_data=f"block_{mijoz['user_id']}"))
                bot.send_message(cid, matn, parse_mode="Markdown", reply_markup=kb)
                return

            # Telefon bo'yicha qidirish (+ kodi bilan ham, siz ham)
            tel_variants = [qidiruv, "+998"+qidiruv, "998"+qidiruv]
            mijoz = None
            for tel in tel_variants:
                mijoz = conn.execute("SELECT * FROM mijozlar WHERE telefon=?", (tel,)).fetchone()
                if mijoz: break
            # Raqamning oxirgi 9 ta belgisi bilan qidirish
            if not mijoz and len(qidiruv) >= 9:
                oxiri = qidiruv[-9:]
                all_m = conn.execute("SELECT * FROM mijozlar").fetchall()
                for m in all_m:
                    if m["telefon"] and m["telefon"][-9:] == oxiri:
                        mijoz = m
                        break

            if mijoz:
                blok = "🚫 Bloklangan" if mijoz["bloklangan"] else "✅ Faol"
                bronlar = conn.execute(
                    "SELECT id FROM bron_xonalar bx JOIN bronlar b ON bx.bron_id=b.id WHERE b.telefon=?",
                    (mijoz["telefon"],)).fetchall()
                matn = (f"👤 *{mijoz['ism']}*\n📞 {mijoz['telefon']}\n"
                       f"💬 @{mijoz['username']}\n{blok}\n"
                       f"Bronlar: {len(bronlar)} ta")
                kb = types.InlineKeyboardMarkup()
                if mijoz["bloklangan"]:
                    kb.add(types.InlineKeyboardButton("✅ Blokdan chiqarish", callback_data=f"unblock_{mijoz['user_id']}"))
                else:
                    kb.add(types.InlineKeyboardButton("🚫 Bloklash", callback_data=f"block_{mijoz['user_id']}"))
                bot.send_message(cid, matn, parse_mode="Markdown", reply_markup=kb)
            else:
                bot.send_message(cid, f"❌ '{qidiruv}' topilmadi")
        return

    # Admin tezkor bron
    if step == "admin_tezkor_kishi" and is_admin(uid):
        try:
            n = int(msg.text)
            state["ab"]["kishi"] = n
            state["ab"]["guruh"] = "oila"
            state["step"] = "admin_tezkor_sana"
            user_state[cid] = state
            bot.send_message(cid, f"👥 {n} kishi\n\n📅 Sana tanlang:", reply_markup=sana_tugmalari())
        except: bot.send_message(cid, "Raqam kiriting")
        return

    if step == "admin_tezkor_ism" and is_admin(uid):
        state["ab"]["ism"] = msg.text
        state["step"] = "admin_tezkor_telefon"
        user_state[cid] = state
        bot.send_message(cid, "Telefon raqami:")
        return

    if step == "admin_tezkor_telefon" and is_admin(uid):
        ab = state["ab"]
        bron_id = bron_id_gen()
        with db() as conn:
            while conn.execute("SELECT id FROM bronlar WHERE id=?", (bron_id,)).fetchone():
                bron_id = bron_id_gen()
            conn.execute("""INSERT INTO bronlar
                (id,ism,telefon,sana,kunlar,kishi,xona,narx,tasdiqlangan,user_id,username,created_at)
                VALUES (?,?,?,?,?,?,?,?,1,?,?,?)""",
                (bron_id, ab["ism"], msg.text, ab["sana"], ab["kunlar"],
                 ab["kishi"], ab["xona_nomi"], ab["narx"],
                 ADMIN_IDS[0], "admin", datetime.now().strftime("%d.%m.%Y %H:%M")))
            for xid in ab["xona_ids"]:
                conn.execute("INSERT INTO bron_xonalar VALUES (?,?)", (bron_id, xid))
            conn.commit()
        for xid in ab["xona_ids"]:
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
            bot.send_message(cid, t(uid, "qaysi_sana"),
                             parse_mode="Markdown",
                             reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(t(uid, "bosh_menyu")))
            bot.send_message(cid, t(uid, "sana_tanlang"), reply_markup=sana_tugmalari())
        except: bot.send_message(cid, "Raqam kiriting")
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
            kb.add(t(uid, "oila"), t(uid, "dostlar"), t(uid, "bosh_menyu"))
            bot.send_message(cid, t(uid, "kimlar"), parse_mode="Markdown", reply_markup=kb)
        except: bot.send_message(cid, "Raqam kiriting")
        return

    if step == "guruh":
        til = get_til(uid) or "uz"
        g = "oila" if msg.text == MATNLAR[til]["oila"] else "dost"
        state["guruh"] = g
        state["step"] = "sana"
        user_state[cid] = state
        bot.send_message(cid, t(uid, "qaysi_sana"), parse_mode="Markdown",
                         reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(t(uid, "bosh_menyu")))
        bot.send_message(cid, t(uid, "sana_tanlang"), reply_markup=sana_tugmalari())
        return

    if step == "ism":
        state["ism"] = msg.text.strip()
        state["step"] = "telefon"
        user_state[cid] = state
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(types.KeyboardButton(t(uid, "kontakt"), request_contact=True))
        kb.add(t(uid, "bosh_menyu"))
        bot.send_message(cid, t(uid, "telefon"), parse_mode="Markdown", reply_markup=kb)
        return

    if step == "telefon":
        state["telefon"] = msg.text.strip()
        user_state[cid] = state
        _tasdiqlash_yuborim(cid)
        return

# ==================== ESLATMA ====================

def eslatma_yuborish():
    while True:
        try:
            hozir = datetime.now()
            if hozir.hour == 11 and hozir.minute == 0:
                ertaga = (hozir + timedelta(days=1)).strftime("%d.%m.%Y")
                with db() as conn:
                    bronlar = conn.execute(
                        "SELECT * FROM bronlar WHERE tasdiqlangan=1").fetchall()
                for b in bronlar:
                    bosh = datetime.strptime(b["sana"], "%d.%m.%Y")
                    tugash = bosh + timedelta(days=b["kunlar"])
                    if tugash.strftime("%d.%m.%Y") == hozir.strftime("%d.%m.%Y"):
                        try:
                            uid = b["user_id"]
                            bot.send_message(uid, t(uid, "vaqt_tugaydi"))
                        except: pass
            import time
            time.sleep(60)
        except Exception as e:
            logging.error(f"Eslatma xato: {e}")
            import time
            time.sleep(60)

# Eslatmani alohida thread da ishga tushirish
eslatma_thread = threading.Thread(target=eslatma_yuborish, daemon=True)
eslatma_thread.start()

if __name__ == "__main__":
    print("✅ Tog' Tagi Resort Bot ishga tushdi!")
    bot.infinity_polling()
