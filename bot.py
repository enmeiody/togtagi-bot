import logging
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)

# ==================== SOZLAMALAR ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = 8886176055
ADMIN_CHAT_ID = 8886176055

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

# ==================== XONALAR BAZASI ====================
XONALAR = {
    1: {"nomi": "1-xona", "qavat": 1, "sigim": 3, "tur": "oila", "band_kunlar": []},
    2: {"nomi": "2-xona", "qavat": 1, "sigim": 3, "tur": "oila", "band_kunlar": []},
    3: {"nomi": "3-xona", "qavat": 1, "sigim": 7, "tur": "oila", "band_kunlar": []},
    4: {"nomi": "4-xona", "qavat": 1, "sigim": 7, "tur": "oila", "band_kunlar": []},
    5: {"nomi": "5-xona", "qavat": 2, "sigim": 3, "tur": "dostlar", "band_kunlar": []},
    6: {"nomi": "6-xona", "qavat": 2, "sigim": 3, "tur": "dostlar", "band_kunlar": []},
    7: {"nomi": "7-xona", "qavat": 2, "sigim": 3, "tur": "dostlar", "band_kunlar": []},
    8: {"nomi": "8-xona", "qavat": 2, "sigim": 3, "tur": "dostlar", "band_kunlar": []},
    9: {"nomi": "9-xona", "qavat": 2, "sigim": 3, "tur": "dostlar", "band_kunlar": []},
    10: {"nomi": "10-xona", "qavat": 2, "sigim": 3, "tur": "dostlar", "band_kunlar": []},
}

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

NECHA_KISHI, GURUH_TURI, SANA, ISM, TELEFON, TASDIQLASH = range(6)
user_data_store = {}

# ==================== YORDAMCHI ====================

def xona_band_mi(xona_id, sana):
    return sana in XONALAR[xona_id]["band_kunlar"]

def mos_xonalar(kishi_soni, guruh_turi, sana):
    mos = []
    for xona_id, xona in XONALAR.items():
        if xona_band_mi(xona_id, sana):
            continue
        if xona["sigim"] < kishi_soni:
            continue
        if guruh_turi == "oila":
            priority = 1 if xona["qavat"] == 1 else 2
        else:
            priority = 1 if xona["qavat"] == 2 else 2
        mos.append((xona_id, xona, priority))
    mos.sort(key=lambda x: (x[2], x[0]))
    return mos

def xonalar_matni(mos_list):
    if not mos_list:
        return "Afsuski, bu sana va kishi soni uchun bosh xona yoq."
    matn = "Sizga mos bosh xonalar:\n\n"
    for xona_id, xona, _ in mos_list[:5]:
        qavat_izoh = "1-qavat (oilalar uchun qulay)" if xona["qavat"] == 1 else "2-qavat (dostlar uchun qulay)"
        sigim = xona["sigim"]
        nomi = xona["nomi"]
        matn += f"Xona: {nomi}\n"
        matn += f"Sigimi: {sigim} kishi\n"
        matn += f"{qavat_izoh}\n\n"
    return matn

# ==================== HANDLERLAR ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Xona bron qilish")],
        [KeyboardButton("Bosh xonalarni korish")],
        [KeyboardButton("Manzil va lokatsiya")],
        [KeyboardButton("Boglanish")],
    ]
    await update.message.reply_text(
        "Tog Tagi Resort ga xush kelibsiz!\n\nTog bagride dam olish uchun eng yaxshi joy.\nQuyidagi bolimlardan birini tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def bron_boshlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id] = {}
    await update.message.reply_text(
        "Nechta kishi kelmoqchisiz?\n\nRaqam kiriting (masalan: 3)",
        reply_markup=ReplyKeyboardMarkup([["1","2","3"],["4","5","6"],["7","8","9"]], resize_keyboard=True)
    )
    return NECHA_KISHI

async def necha_kishi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        son = int(update.message.text.strip())
        if son < 1 or son > 14:
            raise ValueError
        user_data_store[update.effective_user.id]["kishi_soni"] = son
        keyboard = [["Oila bilan"], ["Dostlar yoki erkaklar guruh"]]
        await update.message.reply_text(
            f"{son} kishi.\n\nKimlar bilan kelmoqchisiz?",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return GURUH_TURI
    except ValueError:
        await update.message.reply_text("Iltimos, togri raqam kiriting (1-14)")
        return NECHA_KISHI

async def guruh_turi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matn = update.message.text
    if "Oila" in matn:
        user_data_store[update.effective_user.id]["guruh_turi"] = "oila"
    else:
        user_data_store[update.effective_user.id]["guruh_turi"] = "dostlar"
    await update.message.reply_text(
        "Qaysi sanada kelmoqchisiz?\n\nSanani kiriting (masalan: 15.06.2025)",
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return SANA

async def sana_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matn = update.message.text.strip()
    try:
        sana = datetime.strptime(matn, "%d.%m.%Y")
        if sana.date() < datetime.now().date():
            await update.message.reply_text("Otgan sana kiritdingiz. Kelajakdagi sana kiriting.")
            return SANA
        user_data_store[update.effective_user.id]["sana"] = matn
        data = user_data_store[update.effective_user.id]
        mos = mos_xonalar(data["kishi_soni"], data["guruh_turi"], matn)
        if not mos:
            await update.message.reply_text("Bu sanada sizga mos bosh xona yoq. Boshqa sana sinab koring.")
            return SANA
        user_data_store[update.effective_user.id]["mos_xonalar"] = [(x[0], x[1]) for x in mos]
        xona_txt = xonalar_matni(mos)
        await update.message.reply_text(
            f"Sana: {matn}\n\n{xona_txt}\nIsmingizni kiriting:",
            reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
        )
        return ISM
    except ValueError:
        await update.message.reply_text("Nototri format. Iltimos: 15.06.2025")
        return SANA

async def ism_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["ism"] = update.message.text.strip()
    await update.message.reply_text("Telefon raqamingizni kiriting:\n\nMasalan: +998901234567")
    return TELEFON

async def telefon_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["telefon"] = update.message.text.strip()
    data = user_data_store[update.effective_user.id]
    xona_nomlari = ", ".join([x[1]["nomi"] for x in data["mos_xonalar"][:3]])
    matn = (
        "Bron malumotlari:\n\n"
        f"Ism: {data['ism']}\n"
        f"Telefon: {data['telefon']}\n"
        f"Sana: {data['sana']}\n"
        f"Kishi soni: {data['kishi_soni']}\n"
        f"Mos xonalar: {xona_nomlari}\n\n"
        "Malumotlar togrimikin?"
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Ha, tasdiqlash", callback_data="tasdiqlash"),
            InlineKeyboardButton("Bekor qilish", callback_data="bekor")
        ]
    ])
    await update.message.reply_text(matn, reply_markup=keyboard)
    return TASDIQLASH

async def tasdiqlash_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "bekor":
        await query.edit_message_text("Bron bekor qilindi. /start bosing.")
        return ConversationHandler.END
    data = user_data_store.get(update.effective_user.id, {})
    user = update.effective_user
    xona_nomlari = ", ".join([x[1]["nomi"] for x in data.get("mos_xonalar", [])[:3]])
    admin_xabar = (
        "YANGI BRON SOROVI!\n\n"
        f"Ism: {data.get('ism', '-')}\n"
        f"Telefon: {data.get('telefon', '-')}\n"
        f"Sana: {data.get('sana', '-')}\n"
        f"Kishi soni: {data.get('kishi_soni', '-')}\n"
        f"Guruh turi: {data.get('guruh_turi', '-')}\n"
        f"Mos xonalar: {xona_nomlari}\n"
        f"Telegram: @{user.username or 'yoq'}\n"
        f"ID: {user.id}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_xabar)
    except Exception as e:
        logger.error(f"Admin ga xabar yuborishda xato: {e}")
    await query.edit_message_text(
        "Bron sorovingiz qabul qilindi!\n\nTez orada siz bilan boglanamiz.\nSavollar uchun: +998XXXXXXXXX"
    )
    return ConversationHandler.END

async def bekor_qilish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in user_data_store:
        del user_data_store[update.effective_user.id]
    await update.message.reply_text("Bekor qilindi. /start bosib qaytadan boshlang.")
    return ConversationHandler.END

async def bosh_xonalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bugun = datetime.now().strftime("%d.%m.%Y")
    matn = "Tog Tagi Resort — Xonalar:\n\n"
    matn += "1-qavat (Oilalar uchun qulay):\n"
    for xona_id in [1, 2, 3, 4]:
        xona = XONALAR[xona_id]
        holat = "Band" if xona_band_mi(xona_id, bugun) else "Bosh"
        sigim = xona["sigim"]
        nomi = xona["nomi"]
        matn += f"  {nomi} — {sigim} kishi — {holat}\n"
    matn += "\n2-qavat (Dostlar uchun qulay):\n"
    for xona_id in [5, 6, 7, 8, 9, 10]:
        xona = XONALAR[xona_id]
        holat = "Band" if xona_band_mi(xona_id, bugun) else "Bosh"
        sigim = xona["sigim"]
        nomi = xona["nomi"]
        matn += f"  {nomi} — {sigim} kishi — {holat}\n"
    matn += "\nBron qilish uchun 'Xona bron qilish' tugmasini bosing"
    await update.message.reply_text(matn)

async def manzil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tog Tagi Resort manzili:\n\nManzilni shu yerga kiriting")
    await update.message.reply_location(latitude=41.2995, longitude=69.2401)

async def boglanish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Boglanish:\n\n"
        "Telefon: +998XXXXXXXXX\n"
        "Instagram: @togtagi_resort\n\n"
        "Ish vaqti: 24/7"
    )

async def admin_band(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        xona_id = int(context.args[0])
        sana = context.args[1]
        if xona_id not in XONALAR:
            await update.message.reply_text("Xona topilmadi")
            return
        if sana not in XONALAR[xona_id]["band_kunlar"]:
            XONALAR[xona_id]["band_kunlar"].append(sana)
        await update.message.reply_text(f"{XONALAR[xona_id]['nomi']} — {sana} sanasida BAND qilindi")
    except (IndexError, ValueError):
        await update.message.reply_text("Format: /band 1 15.06.2025")

async def admin_bosh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        xona_id = int(context.args[0])
        sana = context.args[1]
        if xona_id not in XONALAR:
            await update.message.reply_text("Xona topilmadi")
            return
        if sana in XONALAR[xona_id]["band_kunlar"]:
            XONALAR[xona_id]["band_kunlar"].remove(sana)
        await update.message.reply_text(f"{XONALAR[xona_id]['nomi']} — {sana} sanasida BOSH qilindi")
    except (IndexError, ValueError):
        await update.message.reply_text("Format: /bosh 1 15.06.2025")

async def admin_holat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    matn = "Barcha xonalar holati:\n\n"
    for xona_id, xona in XONALAR.items():
        band = xona["band_kunlar"]
        sigim = xona["sigim"]
        nomi = xona["nomi"]
        if band:
            band_matn = ", ".join(band[-3:])
            matn += f"Band: {nomi} ({sigim} kishi) — {band_matn}\n"
        else:
            matn += f"Bosh: {nomi} ({sigim} kishi)\n"
    matn += "\nBuyruqlar:\n/band [xona] [sana]\n/bosh [xona] [sana]\nMisol: /band 1 15.06.2025"
    await update.message.reply_text(matn)

# ==================== ASOSIY ====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    bron_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Xona bron qilish$"), bron_boshlash)],
        states={
            NECHA_KISHI: [MessageHandler(filters.TEXT & ~filters.COMMAND, necha_kishi)],
            GURUH_TURI: [MessageHandler(filters.TEXT & ~filters.COMMAND, guruh_turi)],
            SANA: [MessageHandler(filters.TEXT & ~filters.COMMAND, sana_olish)],
            ISM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ism_olish)],
            TELEFON: [MessageHandler(filters.TEXT & ~filters.COMMAND, telefon_olish)],
            TASDIQLASH: [CallbackQueryHandler(tasdiqlash_handler)],
        },
        fallbacks=[CommandHandler("bekor", bekor_qilish)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(bron_handler)
    app.add_handler(MessageHandler(filters.Regex("^Bosh xonalarni korish$"), bosh_xonalar))
    app.add_handler(MessageHandler(filters.Regex("^Manzil va lokatsiya$"), manzil))
    app.add_handler(MessageHandler(filters.Regex("^Boglanish$"), boglanish))
    app.add_handler(CommandHandler("band", admin_band))
    app.add_handler(CommandHandler("bosh", admin_bosh))
    app.add_handler(CommandHandler("holat", admin_holat))
    print("Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
