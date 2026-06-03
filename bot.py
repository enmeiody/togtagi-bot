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

from db_module import init_db
init_db()

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

bot.set_my_commands([
    telebot.types.BotCommand("start", "Bosh menyu"),
    telebot.types.BotCommand("admin", "Admin panel"),
])

# Handlerlarni ro'yxatdan o'tkazish
from handlers import mijoz, admin, admin_text
mijoz.register(bot)
admin.register(bot)
admin_text.register(bot)

DIRECTOR_IDS = [8886176055, 7323184602]


# ==================== ESLATMALAR ====================

def eslatmalar():
    while True:
        try:
            hozir = datetime.now()

            # 11:00 - vaqt tugayapti eslatmasi
            if hozir.hour == 11 and hozir.minute == 0:
                bugun = hozir.strftime("%d.%m.%Y")
                from db_module import db, format_narx
                with db() as conn:
                    bronlar = conn.execute(
                        "SELECT * FROM bronlar WHERE holat='tasdiqlangan'").fetchall()
                for b in bronlar:
                    bosh = datetime.strptime(b["sana"], "%d.%m.%Y")
                    tugash = bosh + timedelta(days=b["kunlar"])
                    if tugash.strftime("%d.%m.%Y") == bugun and b["user_id"]:
                        try:
                            from texts import TELEFON1
                            bot.send_message(b["user_id"],
                                f"Bugun 12:00 da xonadagi vaqtingiz tugaydi.\n"
                                f"Iltimos, xonani boshatiqng.\n\n"
                                f"Tapchanlardan kechgacha foydalanishingiz mumkin!\n"
                                f"{TELEFON1}")
                        except: pass

            # 11:00 - 1 kun qolgan eslatma (adminlarga ham)
            if hozir.hour == 11 and hozir.minute == 0:
                ertaga = (hozir + timedelta(days=1)).strftime("%d.%m.%Y")
                from db_module import db
                with db() as conn:
                    bronlar = conn.execute(
                        "SELECT * FROM bronlar WHERE sana=? AND holat='tasdiqlangan'",
                        (ertaga,)).fetchall()
                for b in bronlar:
                    # Mijozga eslatma
                    if b["user_id"]:
                        try:
                            from texts import TELEFON1
                            bot.send_message(b["user_id"],
                                f"Eslatma! Ertaga resortga kelasiz:\n"
                                f"Bron #{b['id']}\n"
                                f"Xona: {b['xona']}\n"
                                f"Sana: {b['sana']}\n\n"
                                f"Savollar: {TELEFON1}")
                        except: pass
                    # Adminlarga eslatma
                    from db_module import format_narx
                    tugash = (datetime.strptime(b["sana"], "%d.%m.%Y") + timedelta(days=b["kunlar"])).strftime("%d.%m.%Y")
                    for aid in DIRECTOR_IDS:
                        try:
                            bot.send_message(aid,
                                f"Ertaga keluvchi mehmon:\n"
                                f"#{b['id']} | {b['xona']}\n"
                                f"{b['ism']} | {b['telefon']}\n"
                                f"{b['sana']}-{tugash} | {b['kishi']} kishi\n"
                                f"{format_narx(b['narx'])} som")
                        except: pass

            # 20:00 - kunlik hisobot
            if hozir.hour == 20 and hozir.minute == 0:
                from db_module import bugungi_statistika
                stat = bugungi_statistika()
                bugun = hozir.strftime("%d.%m.%Y")
                matn = (f"Kunlik hisobot ({bugun}):\n\n"
                        f"Foydalanuvchilar: {stat['jami_foydalanuvchi']}\n"
                        f"Yangi bronlar: {stat['yangi_bronlar']}\n\n"
                        "Harakatlar:\n")
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


# Eslatmani alohida thread da ishga tushirish
eslatma_thread = threading.Thread(target=eslatmalar, daemon=True)
eslatma_thread.start()

if __name__ == "__main__":
    logging.info("Tog' Tagi Resort Bot ishga tushdi!")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
