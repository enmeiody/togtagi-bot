import os
import logging
import threading
import time
from datetime import datetime, timedelta
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from db import init_db
init_db()
logging.info("Database initialized")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=4)

bot.set_my_commands([
    telebot.types.BotCommand("start", "Bosh menyu"),
    telebot.types.BotCommand("admin", "Admin panel"),
])

# Handlerlarni ro'yxatdan o'tkazish - tartib muhim!
from handlers import admin_h, mijoz, extra_callbacks

admin_h.register(bot)       # Admin buyruqlar va tugmalar birinchi
extra_callbacks.register(bot)  # Qoshimcha callbacklar
mijoz.register(bot)         # Mijoz handlerlar (shu jumladan umumiy matn handler)

DIRECTOR_IDS = [8886176055, 7323184602]


def eslatmalar():
    while True:
        try:
            hozir = datetime.now()
            from db import get_db, format_narx

            # 11:00 - vaqt tugaydi + 1 kun oldin eslatma
            if hozir.hour == 11 and hozir.minute == 0:
                bugun = hozir.strftime("%d.%m.%Y")
                ertaga = (hozir + timedelta(days=1)).strftime("%d.%m.%Y")
                from config import TELEFON1

                conn = get_db()
                bronlar = conn.execute(
                    "SELECT * FROM bronlar WHERE holat='tasdiqlangan'").fetchall()
                conn.close()

                for b in bronlar:
                    bosh = datetime.strptime(b["sana"], "%d.%m.%Y")
                    tugash = bosh + timedelta(days=b["kunlar"])

                    # Bugun tugaydi
                    if tugash.strftime("%d.%m.%Y") == bugun and b["user_id"]:
                        try:
                            bot.send_message(b["user_id"],
                                f"Bugun 12:00 da xonadagi vaqtingiz tugaydi.\n"
                                f"Xonani boshatishingizni so'raymiz.\n\n"
                                f"Tapchanlardan kechgacha foydalanishingiz mumkin!\n{TELEFON1}")
                        except: pass

                    # Ertaga keladi
                    if b["sana"] == ertaga:
                        tugash_str = tugash.strftime("%d.%m.%Y")
                        if b["user_id"]:
                            try:
                                bot.send_message(b["user_id"],
                                    f"Eslatma! Ertaga resortga kelasiz:\n"
                                    f"#{b['id']} | {b['xona']} | {b['sana']}\n{TELEFON1}")
                            except: pass
                        for aid in DIRECTOR_IDS:
                            try:
                                bot.send_message(aid,
                                    f"Ertaga keluvchi mehmon:\n"
                                    f"#{b['id']} | {b['xona']}\n"
                                    f"{b['ism']} | {b['telefon']}\n"
                                    f"{b['sana']}-{tugash_str} | {b['kishi']} kishi")
                            except: pass

            # 20:00 - kunlik hisobot
            if hozir.hour == 20 and hozir.minute == 0:
                from db import bugungi_stat
                stat = bugungi_stat()
                bugun = hozir.strftime("%d.%m.%Y")
                matn = (f"Kunlik hisobot ({bugun}):\n\n"
                        f"Foydalanuvchilar: {stat['foydalanuvchilar']}\n"
                        f"Yangi bronlar: {stat['bronlar']}\n\nHarakatlar:\n")
                for h in stat["harakatlar"]:
                    matn += f"  {h['harakat']}: {h['c']} marta\n"
                for aid in DIRECTOR_IDS:
                    try:
                        bot.send_message(aid, matn)
                    except: pass

            time.sleep(60)
        except Exception as e:
            logging.error(f"Eslatma xato: {e}")
            time.sleep(60)


eslatma_thread = threading.Thread(target=eslatmalar, daemon=True)
eslatma_thread.start()

if __name__ == "__main__":
    logging.info("Tog' Tagi Resort Bot ishga tushdi!")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
