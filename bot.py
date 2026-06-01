import os
import logging
from datetime import datetime
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = 8886176055

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(BOT_TOKEN)

XONALAR = {
    1: {"nomi": "1-xona", "qavat": 1, "sigim": 3, "band": []},
    2: {"nomi": "2-xona", "qavat": 1, "sigim": 3, "band": []},
    3: {"nomi": "3-xona", "qavat": 1, "sigim": 7, "band": []},
    4: {"nomi": "4-xona", "qavat": 1, "sigim": 7, "band": []},
    5: {"nomi": "5-xona", "qavat": 2, "sigim": 3, "band": []},
    6: {"nomi": "6-xona", "qavat": 2, "sigim": 3, "band": []},
    7: {"nomi": "7-xona", "qavat": 2, "sigim": 3, "band": []},
    8: {"nomi": "8-xona", "qavat": 2, "sigim": 3, "band": []},
    9: {"nomi": "9-xona", "qavat": 2, "sigim": 3, "band": []},
    10: {"nomi": "10-xona", "qavat": 2, "sigim": 3, "band": []},
}

user_state = {}

def asosiy_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("Xona bron qilish"))
    kb.add(types.KeyboardButton("Bosh xonalarni korish"))
    kb.add(types.KeyboardButton("Manzil va lokatsiya"))
    kb.add(types.KeyboardButton("Boglanish"))
    return kb

def mos_xonalar(kishi, guruh, sana):
    mos = []
    for xid, x in XONALAR.items():
        if sana in x["band"]:
            continue
        if x["sigim"] < kishi:
            continue
        p = 1 if (guruh == "oila" and x["qavat"] == 1) or (guruh == "dost" and x["qavat"] == 2) else 2
        mos.append((xid, x, p))
    mos.sort(key=lambda a: (a[2], a[0]))
    return mos

@bot.message_handler(commands=["start"])
def start(msg):
    user_state.pop(msg.chat.id, None)
    bot.send_message(msg.chat.id, "Tog Tagi Resort ga xush kelibsiz!\n\nQuyidagi bolimlardan birini tanlang:", reply_markup=asosiy_menu())

@bot.message_handler(func=lambda m: m.text == "Xona bron qilish")
def bron_start(msg):
    user_state[msg.chat.id] = {"step": "kishi"}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add("1","2","3","4","5","6","7","8","9")
    bot.send_message(msg.chat.id, "Nechta kishi kelmoqchisiz?", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "Bosh xonalarni korish")
def bosh_xonalar(msg):
    bugun = datetime.now().strftime("%d.%m.%Y")
    txt = "Tog Tagi Resort xonalari:\n\n1-qavat (oilalar uchun):\n"
    for xid in [1,2,3,4]:
        x = XONALAR[xid]
        h = "Band" if bugun in x["band"] else "Bosh"
        txt += f"  {x['nomi']} — {x['sigim']} kishi — {h}\n"
    txt += "\n2-qavat (dostlar uchun):\n"
    for xid in [5,6,7,8,9,10]:
        x = XONALAR[xid]
        h = "Band" if bugun in x["band"] else "Bosh"
        txt += f"  {x['nomi']} — {x['sigim']} kishi — {h}\n"
    bot.send_message(msg.chat.id, txt)

@bot.message_handler(func=lambda m: m.text == "Manzil va lokatsiya")
def manzil(msg):
    bot.send_message(msg.chat.id, "Tog Tagi Resort manzili:\n[Manzilni kiriting]")
    bot.send_location(msg.chat.id, latitude=41.2995, longitude=69.2401)

@bot.message_handler(func=lambda m: m.text == "Boglanish")
def boglanish(msg):
    bot.send_message(msg.chat.id, "Boglanish:\n\nTelefon: +998XXXXXXXXX\nInstagram: @togtagi_resort\n\nIsh vaqti: 24/7")

@bot.message_handler(commands=["band"])
def admin_band(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        _, xid, sana = msg.text.split()
        xid = int(xid)
        if sana not in XONALAR[xid]["band"]:
            XONALAR[xid]["band"].append(sana)
        bot.send_message(msg.chat.id, f"{XONALAR[xid]['nomi']} — {sana} BAND qilindi")
    except:
        bot.send_message(msg.chat.id, "Format: /band 1 15.06.2025")

@bot.message_handler(commands=["bosh"])
def admin_bosh(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        _, xid, sana = msg.text.split()
        xid = int(xid)
        if sana in XONALAR[xid]["band"]:
            XONALAR[xid]["band"].remove(sana)
        bot.send_message(msg.chat.id, f"{XONALAR[xid]['nomi']} — {sana} BOSH qilindi")
    except:
        bot.send_message(msg.chat.id, "Format: /bosh 1 15.06.2025")

@bot.message_handler(commands=["holat"])
def admin_holat(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    txt = "Xonalar holati:\n\n"
    for xid, x in XONALAR.items():
        if x["band"]:
            txt += f"Band: {x['nomi']} — {', '.join(x['band'][-3:])}\n"
        else:
            txt += f"Bosh: {x['nomi']}\n"
    txt += "\n/band 1 15.06.2025 — band qilish\n/bosh 1 15.06.2025 — bosh qilish"
    bot.send_message(msg.chat.id, txt)

@bot.message_handler(func=lambda m: True)
def barcha_xabarlar(msg):
    cid = msg.chat.id
    state = user_state.get(cid, {})
    step = state.get("step")

    if step == "kishi":
        try:
            n = int(msg.text)
            if n < 1 or n > 14:
                raise ValueError
            user_state[cid]["kishi"] = n
            user_state[cid]["step"] = "guruh"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("Oila bilan", "Dostlar yoki erkaklar")
            bot.send_message(cid, f"{n} kishi.\n\nKimlar bilan kelmoqchisiz?", reply_markup=kb)
        except ValueError:
            bot.send_message(cid, "Iltimos 1-14 orasida raqam kiriting.")

    elif step == "guruh":
        g = "oila" if "Oila" in msg.text else "dost"
        user_state[cid]["guruh"] = g
        user_state[cid]["step"] = "sana"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("/bekor")
        bot.send_message(cid, "Qaysi sanada kelmoqchisiz?\n\nMasalan: 15.06.2025", reply_markup=kb)

    elif step == "sana":
        if msg.text == "/bekor":
            user_state.pop(cid, None)
            bot.send_message(cid, "Bekor qilindi.", reply_markup=asosiy_menu())
            return
        try:
            d = datetime.strptime(msg.text.strip(), "%d.%m.%Y")
            if d.date() < datetime.now().date():
                bot.send_message(cid, "Otgan sana. Kelajakdagi sana kiriting.")
                return
            sana = msg.text.strip()
            mos = mos_xonalar(user_state[cid]["kishi"], user_state[cid]["guruh"], sana)
            if not mos:
                bot.send_message(cid, "Bu sanada mos bosh xona yoq. Boshqa sana kiriting.")
                return
            user_state[cid]["sana"] = sana
            user_state[cid]["xonalar"] = [(a[0], a[1]["nomi"]) for a in mos[:3]]
            user_state[cid]["step"] = "ism"
            txt = "Sizga mos xonalar:\n\n"
            for xid, x, _ in mos[:5]:
                q = "1-qavat (oila)" if x["qavat"] == 1 else "2-qavat (dostlar)"
                txt += f"{x['nomi']} — {x['sigim']} kishi — {q}\n"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("/bekor")
            bot.send_message(cid, f"Sana: {sana}\n\n{txt}\nIsmingizni kiriting:", reply_markup=kb)
        except ValueError:
            bot.send_message(cid, "Format: 15.06.2025")

    elif step == "ism":
        user_state[cid]["ism"] = msg.text.strip()
        user_state[cid]["step"] = "telefon"
        bot.send_message(cid, "Telefon raqamingizni kiriting:\nMasalan: +998901234567")

    elif step == "telefon":
        user_state[cid]["telefon"] = msg.text.strip()
        user_state[cid]["step"] = "tasdiq"
        d = user_state[cid]
        xona_txt = ", ".join([x[1] for x in d["xonalar"]])
        matn = (
            "Bron malumotlari:\n\n"
            f"Ism: {d['ism']}\n"
            f"Telefon: {d['telefon']}\n"
            f"Sana: {d['sana']}\n"
            f"Kishi soni: {d['kishi']}\n"
            f"Mos xonalar: {xona_txt}\n\n"
            "Togrimikin? (Ha / Yoq)"
        )
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("Ha, tasdiqlash", "Yoq, bekor qilish")
        bot.send_message(cid, matn, reply_markup=kb)

    elif step == "tasdiq":
        if "Ha" in msg.text:
            d = user_state[cid]
            xona_txt = ", ".join([x[1] for x in d["xonalar"]])
            admin_txt = (
                "YANGI BRON SOROVI!\n\n"
                f"Ism: {d['ism']}\n"
                f"Telefon: {d['telefon']}\n"
                f"Sana: {d['sana']}\n"
                f"Kishi: {d['kishi']}\n"
                f"Guruh: {d['guruh']}\n"
                f"Xonalar: {xona_txt}\n"
                f"Telegram: @{msg.from_user.username or 'yoq'}\n"
                f"ID: {msg.from_user.id}"
            )
            try:
                bot.send_message(ADMIN_ID, admin_txt)
            except Exception as e:
                logging.error(e)
            user_state.pop(cid, None)
            bot.send_message(cid, "Bron sorovingiz qabul qilindi!\nTez orada boglanamiz.", reply_markup=asosiy_menu())
        else:
            user_state.pop(cid, None)
            bot.send_message(cid, "Bekor qilindi.", reply_markup=asosiy_menu())

if __name__ == "__main__":
    print("Bot ishga tushdi!")
    bot.infinity_polling()
