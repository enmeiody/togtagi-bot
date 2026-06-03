import random
import string
from datetime import datetime, timedelta
from database import db, format_narx, xona_kunlar_band, get_xonalar


def bron_id_gen():
    while True:
        harf = random.choice(string.ascii_uppercase)
        raqam = random.randint(100, 999)
        bid = f"{harf}{raqam}"
        with db() as conn:
            if not conn.execute("SELECT id FROM bronlar WHERE id=?", (bid,)).fetchone():
                return bid


def tugash_sanasi(bosh_sana, kunlar):
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y")
    return (bosh + timedelta(days=kunlar)).strftime("%d.%m.%Y")


def sana_tugmalari(boshlanish=None):
    from telebot import types
    kb = types.InlineKeyboardMarkup(row_width=5)
    if boshlanish is None:
        boshlanish = datetime.now().date()
    tugmalar = []
    for i in range(30):
        kun = boshlanish + timedelta(days=i)
        tugmalar.append(types.InlineKeyboardButton(
            kun.strftime("%d/%m"),
            callback_data=f"sana_{kun.strftime('%d.%m.%Y')}"))
    kb.add(*tugmalar)
    return kb


def kunlar_tugmalari():
    from telebot import types
    kb = types.InlineKeyboardMarkup(row_width=5)
    tugmalar = [types.InlineKeyboardButton(f"{i}", callback_data=f"kun_{i}") for i in range(1, 16)]
    kb.add(*tugmalar)
    return kb


def mos_kombinatsiya(kishi, guruh, sana, kunlar=1):
    xonalar = get_xonalar()
    bosh = [x for x in xonalar if not xona_kunlar_band(x["id"], sana, kunlar)]
    if not bosh:
        return []

    # Bitta xona yetarlimi yoki ortiqcha 1 kishi bo'lsa ham ko'rsat
    for x in sorted(bosh, key=lambda a: a["sigim"]):
        if x["sigim"] >= kishi:
            return [{"xonalar": [x], "tur": "bitta", "ortiqcha": 0}]
        elif x["sigim"] == kishi - 1:
            return [{"xonalar": [x], "tur": "bitta_ortiqcha", "ortiqcha": 1}]

    # Kombinatsiya kerak
    afzal_qavat = 1 if guruh == "oila" else 2
    afzal = sorted([x for x in bosh if x["qavat"] == afzal_qavat], key=lambda a: a["sigim"], reverse=True)
    boshqa = sorted([x for x in bosh if x["qavat"] != afzal_qavat], key=lambda a: a["sigim"], reverse=True)
    tartiblangan = afzal + boshqa

    # Eng optimal kombinatsiyani topish
    tanlangan = []
    jami = 0
    for x in tartiblangan:
        if jami >= kishi:
            break
        tanlangan.append(x)
        jami += x["sigim"]

    if jami >= kishi:
        return [{"xonalar": tanlangan, "tur": "kombinatsiya", "ortiqcha": jami - kishi}]

    return []


def barcha_bosh_xonalar(sana, kunlar, kishi=1):
    """Kishi soniga mos yoki yaqin barcha bo'sh xonalar"""
    from telebot import types
    xonalar = get_xonalar()
    bosh = [x for x in xonalar if not xona_kunlar_band(x["id"], sana, kunlar)]

    kb = types.InlineKeyboardMarkup(row_width=1)
    for x in bosh:
        qavat = "🏠" if x["qavat"] == 1 else "🏢"
        narx = format_narx(x["narx"] * kunlar)
        if x["sigim"] >= kishi:
            mos = "✅"
        elif x["sigim"] >= kishi - 1:
            mos = "⚠️"
        else:
            continue  # Juda kichik xonalarni ko'rsatma

        kb.add(types.InlineKeyboardButton(
            f"{mos} {qavat} {x['nomi']} | {x['sigim']} kishi | {narx} so'm",
            callback_data=f"xona_tanla_{x['id']}_{sana}_{kunlar}"))

    return kb


def o_n_kunlik_holat():
    """10 kunlik xonalar holati"""
    from telebot import types
    bugun = datetime.now().date()
    xonalar = get_xonalar()

    matn = "📊 10 kunlik xonalar holati:\n\n"
    sanalar = [(bugun + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(10)]
    kun_nomlar = ["Du","Se","Ch","Pa","Ju","Sh","Ya"]

    for x in xonalar:
        matn += f"🛏 {x['nomi']} ({x['sigim']} kishi) | {x['bino_nomi']}\n"
        kun_satri = ""
        for sana in sanalar:
            kun_dt = datetime.strptime(sana, "%d.%m.%Y")
            kun_nom = kun_nomlar[kun_dt.weekday()]
            from database import xona_band_mi
            if xona_band_mi(x["id"], sana):
                kun_satri += f"🔴"
            else:
                kun_satri += f"🟢"
        matn += kun_satri + "\n\n"

    matn += "🟢 Bo'sh  🔴 Band\n"
    matn += " ".join([f"{(bugun+timedelta(days=i)).strftime('%d/%m')}" for i in range(10)])

    return matn


def tozala_markdown(matn):
    import re
    matn = re.sub(r'\*\*(.+?)\*\*', r'\1', matn)
    matn = re.sub(r'\*(.+?)\*', r'\1', matn)
    matn = re.sub(r'#{1,6}\s', '', matn)
    matn = re.sub(r'`(.+?)`', r'\1', matn)
    return matn.strip()
