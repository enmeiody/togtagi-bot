import os
import logging
import threading
import time
from datetime import datetime, timedelta
import pytz
import telebot
from config import TZ

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from db import init_db
init_db()
logging.info("Database initialized")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=4)
bot.set_my_commands([
    telebot.types.BotCommand("start", "Bosh menyu"),
    telebot.types.BotCommand("admin", "Admin panel"),
])

from handlers import admin_h, mijoz, extra_callbacks
admin_h.register(bot)
extra_callbacks.register(bot)
mijoz.register(bot)

# Joylash jarayoni uchun sana/kun callbacklarini admin_h da qayta ishlatish
from telebot import types
from db import is_admin, tugash_sanasi, format_narx
from keyboards import kunlar_kb, sana_kb, admin_kb

DIRECTOR_IDS = [8886176055, 7323184602]


def eslatmalar():
    yuborilgan = {}  # (sana, soat): True - ikki marta yuborilmasin

    while True:
        try:
            hozir = datetime.now(TZ)
            soat_min = (hozir.hour, hozir.minute)
            bugun = hozir.strftime("%d.%m.%Y")
            ertaga = (hozir + timedelta(days=1)).strftime("%d.%m.%Y")

            from db import get_db, get_xonalar, xona_band_mi, bosh_qil_sana, get_bron_xonalar
            from db import hozirgi_mehmonlar, bugungi_keluvchilar

            # 08:00 - bugungi hisobot adminlarga
            if soat_min == (8, 0) and yuborilgan.get(f"08_{bugun}") != True:
                yuborilgan[f"08_{bugun}"] = True
                mehmonlar = hozirgi_mehmonlar()
                keluvchilar = bugungi_keluvchilar()
                bosh_list = [x for x in get_xonalar() if not xona_band_mi(x["id"], bugun)]

                matn = f"☀️ BUGUNGI HOLAT — {bugun}\n{'='*30}\n\n"
                matn += f"🏨 Hozir {len(mehmonlar)} ta xonada mehmon\n"
                if mehmonlar:
                    for m in mehmonlar:
                        matn += f"  🛏 {m['xona_nomi']} — {m['ism']} ({m['kishi']}👤) ketish: {m['tugash']}\n"

                matn += f"\n📋 Bugun keluvchi: {len(keluvchilar)} ta bron\n"
                if keluvchilar:
                    for b in keluvchilar:
                        tugash = tugash_sanasi(b["sana"], b["kunlar"])
                        matn += f"  #{b['id']} — {b['xona']} — {b['ism']} ({b['kishi']}👤)\n"

                matn += f"\n🟢 Bo'sh xonalar: {len(bosh_list)} ta\n"
                if bosh_list:
                    for x in bosh_list:
                        matn += f"  {x['nomi']} ({x['sigim']}👤)\n"

                conn = get_db()
                ertaga_bronlar = conn.execute(
                    "SELECT * FROM bronlar WHERE sana=? AND holat='tasdiqlangan'",
                    (ertaga,)).fetchall()
                conn.close()
                if ertaga_bronlar:
                    matn += f"\n📅 Ertaga keluvchilar ({len(ertaga_bronlar)} ta):\n"
                    for b in ertaga_bronlar:
                        tugash = tugash_sanasi(b["sana"], b["kunlar"])
                        matn += f"  #{b['id']} — {b['xona']} — {b['ism']} ({b['kishi']}👤)\n"

                for aid in DIRECTOR_IDS:
                    try:
                        bot.send_message(aid, matn)
                    except: pass

            # 11:00 - vaqt tugaydi eslatmasi + 1 kun oldin
            if soat_min == (11, 0) and yuborilgan.get(f"11_{bugun}") != True:
                yuborilgan[f"11_{bugun}"] = True
                conn = get_db()
                bronlar = conn.execute("SELECT * FROM bronlar WHERE holat IN ('tasdiqlangan','joylashgan')").fetchall()
                conn.close()
                for b in bronlar:
                    bosh = datetime.strptime(b["sana"], "%d.%m.%Y")
                    tugash = bosh + timedelta(days=b["kunlar"])
                    # Bugun tugaydi
                    if tugash.strftime("%d.%m.%Y") == bugun and b["user_id"]:
                        try:
                            bot.send_message(b["user_id"],
                                f"⏰ Bugun soat 12:00 da xonangiz vaqti tugaydi.\n\n"
                                f"Xonani bo'shating, lekin:\n"
                                f"🛖 Tapchanlardan foydalanishingiz mumkin\n"
                                f"🍽 Oshxonadan foydalanishingiz mumkin\n\n"
                                f"Savollar: {os.environ.get('TELEFON1', '+998993342035')}")
                        except: pass
                    # Ertaga keladi
                    if b["sana"] == ertaga:
                        tugash_str = tugash_sanasi(b["sana"], b["kunlar"])
                        if b["user_id"]:
                            try:
                                bot.send_message(b["user_id"],
                                    f"📅 Eslatma! Ertaga resortga kelasiz:\n\n"
                                    f"🛏 {b['xona']}\n📅 {b['sana']} - {tugash_str}\n"
                                    f"👥 {b['kishi']} kishi\n\n"
                                    f"Savollar: {os.environ.get('TELEFON1', '+998993342035')}")
                            except: pass
                        for aid in DIRECTOR_IDS:
                            try:
                                bot.send_message(aid,
                                    f"📋 Ertaga keluvchi:\n#{b['id']} | {b['xona']}\n"
                                    f"{b['ism']} | {b['telefon']}\n{b['kishi']} kishi")
                            except: pass

            # 12:15 - avtomatik chiqish
            if soat_min == (12, 15) and yuborilgan.get(f"1215_{bugun}") != True:
                yuborilgan[f"1215_{bugun}"] = True
                conn = get_db()
                bronlar = conn.execute("SELECT * FROM bronlar WHERE holat IN ('tasdiqlangan','joylashgan')").fetchall()
                conn.close()
                for b in bronlar:
                    bosh = datetime.strptime(b["sana"], "%d.%m.%Y")
                    tugash = bosh + timedelta(days=b["kunlar"])
                    if tugash.strftime("%d.%m.%Y") == bugun:
                        xid_list = get_bron_xonalar(b["id"])
                        for xid in xid_list:
                            bosh_qil_sana(xid, bugun, 1)
                        # joylashgan dan chiqarish
                        conn = get_db()
                        conn.execute("UPDATE joylashgan SET holat='chiqdi' WHERE bron_id=?", (b["id"],))
                        conn.commit()
                        conn.close()
                        for aid in DIRECTOR_IDS:
                            try:
                                bot.send_message(aid,
                                    f"🏠 Avtomatik bo'shatildi:\n#{b['id']} | {b['xona']}\n{b['ism']}")
                            except: pass

            # 20:00 - kechki hisobot
            if soat_min == (20, 0) and yuborilgan.get(f"20_{bugun}") != True:
                yuborilgan[f"20_{bugun}"] = True
                from db import bugungi_stat
                stat = bugungi_stat()

                mehmonlar = hozirgi_mehmonlar()
                bosh_list = [x for x in get_xonalar() if not xona_band_mi(x["id"], bugun)]

                matn = f"🌙 KECHKI HISOBOT — {bugun}\n{'='*30}\n\n"
                matn += f"👥 Bot foydalanuvchilar: {stat['foydalanuvchilar']}\n"
                matn += f"🎫 Yangi bronlar: {stat['bronlar']}\n\n"
                matn += f"🏨 Hozir {len(mehmonlar)} ta xonada mehmon\n"
                matn += f"🟢 Bo'sh xonalar: {len(bosh_list)} ta\n\n"

                # Ertaga keluvchilar
                conn = get_db()
                ertaga_b = conn.execute(
                    "SELECT * FROM bronlar WHERE sana=? AND holat='tasdiqlangan'",
                    (ertaga,)).fetchall()
                conn.close()
                if ertaga_b:
                    matn += f"📅 Ertaga keluvchilar ({len(ertaga_b)} ta):\n"
                    for b in ertaga_b:
                        matn += f"  #{b['id']} — {b['xona']} — {b['ism']}\n"

                if stat["harakatlar"]:
                    matn += "\n📈 Harakatlar:\n"
                    for h in stat["harakatlar"][:5]:
                        matn += f"  {h['harakat']}: {h['c']}\n"

                for aid in DIRECTOR_IDS:
                    try:
                        bot.send_message(aid, matn)
                    except: pass

            # Eski yuborilgan kalitlarni tozalash (xotira uchun)
            if len(yuborilgan) > 100:
                yuborilgan.clear()

            time.sleep(60)
        except Exception as e:
            logging.error(f"Eslatma xato: {e}")
            time.sleep(60)


eslatma_thread = threading.Thread(target=eslatmalar, daemon=True)
eslatma_thread.start()

if __name__ == "__main__":
    logging.info("Tog' Tagi Resort Bot ishga tushdi!")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
