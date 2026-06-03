from telebot import types
from config import M, TELEFON1, TELEFON2, INSTAGRAM
from db import get_til, format_narx, tugash_sanasi, get_xonalar, xona_band_mi, xona_kunlar_band, xona_bugun_boshadimi
from datetime import datetime, timedelta


def asosiy_kb(uid):
    til = get_til(uid) or "uz"
    m = M[til]
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(m["bron"], m["bosh_x"], m["galereya"], m["xizmatlar"], m["manzil"], m["bronlarim"])
    kb.add("🌐 Ijtimoiy tarmoqlar")
    return kb


def ijtimoiy_kb():
    from db import get_ijtimoiy
    ijt = get_ijtimoiy()
    kb = types.InlineKeyboardMarkup(row_width=1)
    icons = {"telegram": "📱 Telegram", "instagram": "📸 Instagram", "youtube": "🎬 YouTube"}
    for kalit, info in ijt.items():
        if info["link"]:
            kb.add(types.InlineKeyboardButton(icons.get(kalit, kalit), url=info["link"]))
    return kb


def admin_kb(uid=None):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        "🏨 Qabulxona", "🏠 Xonaga joylash",
        "📊 Bugungi holat", "👥 Mehmonlar",
        "🏢 Xonalar", "📋 Bronlar",
        "👤 Mijoz qidirish", "➕ Tezkor bron",
        "📸 Galereya", "📄 Hisobot",
        "🤖 AI malumot", "🔗 Ijtimoiy tarmoqlar",
        "🔙 Asosiy menyu"
    )
    from db import is_director
    if uid and is_director(uid):
        kb.add("👮 Adminlar", "📊 Statistika")
    return kb


def til_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🇺🇿 O'zbek (lotin)", callback_data="til_uz"),
        types.InlineKeyboardButton("🇺🇿 Ўзбек (кирил)", callback_data="til_uz_kril"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="til_ru"),
    )
    return kb


def sana_kb():
    kb = types.InlineKeyboardMarkup(row_width=5)
    bugun = datetime.now().date()
    btns = []
    for i in range(30):
        kun = bugun + timedelta(days=i)
        btns.append(types.InlineKeyboardButton(
            kun.strftime("%d/%m"),
            callback_data=f"S_{kun.strftime('%d.%m.%Y')}"))
    kb.add(*btns)
    return kb


def kunlar_kb():
    kb = types.InlineKeyboardMarkup(row_width=5)
    btns = [types.InlineKeyboardButton(str(i), callback_data=f"K_{i}") for i in range(1, 16)]
    kb.add(*btns)
    return kb


def xonalar_kb(sana, kunlar, kishi=1):
    kb = types.InlineKeyboardMarkup(row_width=1)
    xonalar = get_xonalar()
    for x in xonalar:
        if dict(x).get("yopiq", 0):
            continue
        if x["sigim"] < kishi - 1:
            continue
        # To'liq band
        if xona_kunlar_band(x["id"], sana, kunlar):
            # Faqat birinchi kun band bo'lib, tugash sanasi = tanlangan sana bo'lsa ko'rsat
            if kunlar == 1 or xona_bugun_boshadimi(x["id"], sana):
                mos = "✅" if x["sigim"] >= kishi else "⚠️"
                qavat = "🏠" if x["qavat"] == 1 else "🏢"
                narx = format_narx(x["narx"] * kunlar)
                kb.add(types.InlineKeyboardButton(
                    f"🕐{qavat} {x['nomi']} | {x['sigim']}👤 | {narx} (13:00 dan)",
                    callback_data=f"XT_{x['id']}_{sana}_{kunlar}_kech"))
            continue
        mos = "✅" if x["sigim"] >= kishi else "⚠️"
        qavat = "🏠" if x["qavat"] == 1 else "🏢"
        narx = format_narx(x["narx"] * kunlar)
        kb.add(types.InlineKeyboardButton(
            f"{mos}{qavat} {x['nomi']} | {x['sigim']}👤 | {narx}",
            callback_data=f"XT_{x['id']}_{sana}_{kunlar}"))
    return kb


def binolar_kb():
    from db import get_binolar
    kb = types.InlineKeyboardMarkup(row_width=1)
    for b in get_binolar():
        kb.add(types.InlineKeyboardButton(f"🏢 {b['nomi']}", callback_data=f"BINO_{b['id']}"))
    return kb


def xonalar_admin_kb(bino_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    bugun = datetime.now().strftime("%d.%m.%Y")
    btns = []
    for x in get_xonalar(bino_id):
        h = "🔴" if xona_band_mi(x["id"], bugun) else "🟢"
        yopiq = "🔒" if dict(x).get("yopiq", 0) else ""
        btns.append(types.InlineKeyboardButton(
            f"{h}{yopiq} {x['nomi']}({x['sigim']}👤)",
            callback_data=f"AX_{x['id']}"))
    kb.add(*btns)
    return kb


def xona_detail_kb(xid, bino_id, yopiq=0):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📅 Bronlar", callback_data=f"AXB_{xid}"),
        types.InlineKeyboardButton("🔴 Band qilish", callback_data=f"AXBAND_{xid}"),
        types.InlineKeyboardButton("🟢 Bosh qilish", callback_data=f"AXBOSH_{xid}"),
        types.InlineKeyboardButton("📸 Rasmlar", callback_data=f"AXRASM_{xid}"),
        types.InlineKeyboardButton("🎥 Videolar", callback_data=f"AXVIDEO_{xid}"),
        types.InlineKeyboardButton("💰 Narx", callback_data=f"AXNARX_{xid}"),
    )
    if yopiq:
        kb.add(types.InlineKeyboardButton("🔓 Brondan ochish", callback_data=f"XONA_OCHIQ_{xid}"))
    else:
        kb.add(types.InlineKeyboardButton("🔒 Brondan yopish", callback_data=f"XONA_YOPIQ_{xid}"))
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"BINO_{bino_id}"))
    return kb
