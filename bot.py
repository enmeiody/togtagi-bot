import logging
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)

# ==================== SOZLAMALAR ====================
BOT_TOKEN = "YOUR_TOKEN_HERE"  # Bu yerga yangi tokeningizni kiriting
ADMIN_ID = 8886176055  # Sizning Telegram ID ingiz
ADMIN_CHAT_ID = 8886176055  # Bron xabarlari keladigan chat (guruh ID si bo'lsa shu yerga)

# ==================== XONALAR BAZASI ====================
XONALAR = {
    1: {"nomi": "1-xona", "qavat": 1, "sig'im": 3, "tur": "oila", "band_kunlar": []},
    2: {"nomi": "2-xona", "qavat": 1, "sig'im": 3, "tur": "oila", "band_kunlar": []},
    3: {"nomi": "3-xona", "qavat": 1, "sig'im": 7, "tur": "oila", "band_kunlar": []},
    4: {"nomi": "4-xona", "qavat": 1, "sig'im": 7, "tur": "oila", "band_kunlar": []},
    5: {"nomi": "5-xona", "qavat": 2, "sig'im": 3, "tur": "do'stlar", "band_kunlar": []},
    6: {"nomi": "6-xona", "qavat": 2, "sig'im": 3, "tur": "do'stlar", "band_kunlar": []},
    7: {"nomi": "7-xona", "qavat": 2, "sig'im": 3, "tur": "do'stlar", "band_kunlar": []},
    8: {"nomi": "8-xona", "qavat": 2, "sig'im": 3, "tur": "do'stlar", "band_kunlar": []},
    9: {"nomi": "9-xona", "qavat": 2, "sig'im": 3, "tur": "do'stlar", "band_kunlar": []},
    10: {"nomi": "10-xona", "qavat": 2, "sig'im": 3, "tur": "do'stlar", "band_kunlar": []},
}

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== SUHBAT HOLATLARI ====================
NECHA_KISHI, GURUH_TURI, SANA, ISM, TELEFON, TASDIQLASH = range(6)

# Foydalanuvchi ma'lumotlarini saqlash
user_data_store = {}

# ==================== YORDAMCHI FUNKSIYALAR ====================

def xona_band_mi(xona_id: int, sana: str) -> bool:
    """Xona berilgan sanada bandmi yoki yo'q"""
    return sana in XONALAR[xona_id]["band_kunlar"]

def mos_xonalar(kishi_soni: int, guruh_turi: str, sana: str) -> list:
    """Mijozga mos bo'sh xonalarni topish"""
    mos = []
    
    for xona_id, xona in XONALAR.items():
        # Sana band emasmi tekshir
        if xona_band_mi(xona_id, sana):
            continue
        
        # Sig'im yetarlimi
        if xona["sig'im"] < kishi_soni:
            continue
        
        # Guruh turi bo'yicha filtrlash
        if guruh_turi == "oila":
            # Oilalar uchun 1-qavat afzal, lekin 2-qavat ham bo'ladi
            mos.append((xona_id, xona, 1 if xona["qavat"] == 1 else 2))
        elif guruh_turi == "do'stlar":
            # Do'stlar/erkaklar uchun 2-qavat afzal
            mos.append((xona_id, xona, 1 if xona["qavat"] == 2 else 2))
        else:
            mos.append((xona_id, xona, 1))
    
    # Afzallik bo'yicha saralash
    mos.sort(key=lambda x: (x[2], x[0]))
    return mos

def xonalar_haqida_matn(mos_xonalar_list: list) -> str:
    """Bo'sh xonalar haqida matn"""
    if not mos_xonalar_list:
        return "❌ Afsuski, so'ralgan sana va kishi soni uchun bo'sh xona yo'q."
    
    matn = "✅ *Sizga mos bo'sh xonalar:*\n\n"
    for xona_id, xona, _ in mos_xonalar_list[:5]:  # Max 5 ta ko'rsat
        qavat_izoh = "🏠 1-qavat (oilalar uchun qulay)" if xona["qavat"] == 1 else "🏢 2-qavat (do'stlar uchun qulay)"
        matn += f"🛏 *{xona['nomi']}*\n"
        matn += f"   👥 Sig'imi: {xona[\"sig'im\"]} kishi\n"
        matn += f"   {qavat_izoh}\n\n"
    
    return matn

# ==================== BOT HANDLERLARI ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botni ishga tushirish"""
    keyboard = [
        [KeyboardButton("🏨 Xona bron qilish")],
        [KeyboardButton("📋 Bo'sh xonalarni ko'rish")],
        [KeyboardButton("📍 Manzil va lokatsiya")],
        [KeyboardButton("📞 Bog'lanish")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🏔 *Tog' Tagi Resort ga xush kelibsiz!*\n\n"
        "Tog' bag'rida dam olish uchun eng yaxshi joy.\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def bron_boshlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bron qilish jarayonini boshlash"""
    user_data_store[update.effective_user.id] = {}
    
    await update.message.reply_text(
        "👥 *Nechta kishi kelmoqchisiz?*\n\n"
        "Raqam kiriting (masalan: 3)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9+"]],
            resize_keyboard=True
        )
    )
    return NECHA_KISHI

async def necha_kishi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kishi sonini olish"""
    matn = update.message.text.strip()
    
    try:
        if matn == "9+":
            son = 9
        else:
            son = int(matn)
        
        if son < 1 or son > 20:
            raise ValueError
        
        user_data_store[update.effective_user.id]["kishi_soni"] = son
        
        keyboard = [
            [KeyboardButton("👨‍👩‍👧‍👦 Oila bilan")],
            [KeyboardButton("👫 Do'stlar / Erkaklar guruh")],
        ]
        
        await update.message.reply_text(
            f"✅ {son} kishi\n\n"
            "👥 *Kimlar bilan kelmoqchisiz?*\n\n"
            "_(Bu bizga mos xonani tanlashda yordam beradi)_",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )
        return GURUH_TURI
    
    except ValueError:
        await update.message.reply_text("❌ Iltimos, to'g'ri raqam kiriting (1-20)")
        return NECHA_KISHI

async def guruh_turi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruh turini olish"""
    matn = update.message.text
    
    if "Oila" in matn:
        user_data_store[update.effective_user.id]["guruh_turi"] = "oila"
        izoh = "1-qavatdagi xonalarimiz oilalar uchun qulay"
    else:
        user_data_store[update.effective_user.id]["guruh_turi"] = "do'stlar"
        izoh = "2-qavatdagi xonalarimiz do'stlar uchun qulay"
    
    await update.message.reply_text(
        f"✅ {izoh}\n\n"
        "📅 *Qaysi sanada kelmoqchisiz?*\n\n"
        "Sanani kiriting (masalan: 15.06.2025)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
    )
    return SANA

async def sana_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sanani olish"""
    matn = update.message.text.strip()
    
    try:
        # Sana formatini tekshirish
        sana = datetime.strptime(matn, "%d.%m.%Y")
        
        if sana.date() < datetime.now().date():
            await update.message.reply_text("❌ O'tgan sana kiritdingiz. Kelajakdagi sana kiriting.")
            return SANA
        
        user_data_store[update.effective_user.id]["sana"] = matn
        
        # Mos xonalarni topish
        data = user_data_store[update.effective_user.id]
        mos = mos_xonalar(data["kishi_soni"], data["guruh_turi"], matn)
        
        if not mos:
            await update.message.reply_text(
                f"❌ *{matn} sanasida sizga mos bo'sh xona yo'q.*\n\n"
                "Boshqa sana sinab ko'ring yoki biz bilan bog'laning:\n"
                "📞 [Telefon raqam]",
                parse_mode="Markdown"
            )
            return ConversationHandler.END
        
        # Mos xonalarni ko'rsat
        xona_matni = xonalar_haqida_matn(mos)
        user_data_store[update.effective_user.id]["mos_xonalar"] = [(x[0], x[1]) for x in mos]
        
        await update.message.reply_text(
            f"📅 Sana: *{matn}*\n\n{xona_matni}\n"
            "✍️ *Ismingizni kiriting:*",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([["/bekor"]], resize_keyboard=True)
        )
        return ISM
    
    except ValueError:
        await update.message.reply_text(
            "❌ Noto'g'ri format. Iltimos, shunday kiriting: *15.06.2025*",
            parse_mode="Markdown"
        )
        return SANA

async def ism_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ism olish"""
    user_data_store[update.effective_user.id]["ism"] = update.message.text.strip()
    
    await update.message.reply_text(
        "📞 *Telefon raqamingizni kiriting:*\n\n"
        "Masalan: +998901234567",
        parse_mode="Markdown"
    )
    return TELEFON

async def telefon_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telefon raqam olish"""
    user_data_store[update.effective_user.id]["telefon"] = update.message.text.strip()
    
    data = user_data_store[update.effective_user.id]
    
    # Tasdiqlash xabari
    xona_nomlari = ", ".join([x[1]["nomi"] for x in data["mos_xonalar"][:3]])
    
    matn = (
        "📋 *Bron ma'lumotlari:*\n\n"
        f"👤 Ism: {data['ism']}\n"
        f"📞 Telefon: {data['telefon']}\n"
        f"📅 Sana: {data['sana']}\n"
        f"👥 Kishi soni: {data['kishi_soni']}\n"
        f"🏨 Mos xonalar: {xona_nomlari}\n\n"
        "✅ Ma'lumotlar to'g'rimi?"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Ha, tasdiqlash", callback_data="tasdiqlash"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="bekor")
        ]
    ])
    
    await update.message.reply_text(matn, parse_mode="Markdown", reply_markup=keyboard)
    return TASDIQLASH

async def tasdiqlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bronni tasdiqlash"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "bekor":
        await query.edit_message_text("❌ Bron bekor qilindi. /start bosing.")
        return ConversationHandler.END
    
    data = user_data_store.get(update.effective_user.id, {})
    user = update.effective_user
    
    # Adminга xabar yuborish
    xona_nomlari = ", ".join([x[1]["nomi"] for x in data.get("mos_xonalar", [])[:3]])
    
    admin_xabar = (
        "🔔 *YANGI BRON SO'ROVI!*\n\n"
        f"👤 Ism: {data.get('ism', '-')}\n"
        f"📞 Telefon: {data.get('telefon', '-')}\n"
        f"📅 Sana: {data.get('sana', '-')}\n"
        f"👥 Kishi soni: {data.get('kishi_soni', '-')}\n"
        f"🏘 Guruh turi: {data.get('guruh_turi', '-')}\n"
        f"🏨 Mos xonalar: {xona_nomlari}\n\n"
        f"📱 Telegram: @{user.username or 'username yoq'}\n"
        f"🆔 ID: {user.id}"
    )
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_xabar,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Admin ga xabar yuborishda xato: {e}")
    
    await query.edit_message_text(
        "✅ *Bron so'rovingiz qabul qilindi!*\n\n"
        "Tez orada siz bilan bog'lanamiz.\n"
        "📞 Savollar uchun: +998XXXXXXXXX",
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END

async def bekor_qilish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jarayonni bekor qilish"""
    if update.effective_user.id in user_data_store:
        del user_data_store[update.effective_user.id]
    
    await update.message.reply_text(
        "❌ Bekor qilindi.\n/start bosib qaytadan boshlang."
    )
    return ConversationHandler.END

async def bosh_xonalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha bo'sh xonalarni ko'rsatish"""
    bugun = datetime.now().strftime("%d.%m.%Y")
    
    matn = "🏨 *Tog' Tagi Resort — Xonalar:*\n\n"
    matn += "🏠 *1-qavat (Oilalar uchun qulay):*\n"
    
    for xona_id in [1, 2, 3, 4]:
        xona = XONALAR[xona_id]
        holat = "🔴 Band" if xona_band_mi(xona_id, bugun) else "🟢 Bo'sh"
        matn += f"  • {xona['nomi']} — {xona[\"sig'im\"]} kishi — {holat}\n"
    
    matn += "\n🏢 *2-qavat (Do'stlar uchun qulay):*\n"
    
    for xona_id in [5, 6, 7, 8, 9, 10]:
        xona = XONALAR[xona_id]
        holat = "🔴 Band" if xona_band_mi(xona_id, bugun) else "🟢 Bo'sh"
        matn += f"  • {xona['nomi']} — {xona[\"sig'im\"]} kishi — {holat}\n"
    
    matn += "\n_Bron qilish uchun 🏨 Xona bron qilish tugmasini bosing_"
    
    await update.message.reply_text(matn, parse_mode="Markdown")

async def manzil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manzil va lokatsiya"""
    await update.message.reply_text(
        "📍 *Tog' Tagi Resort manzili:*\n\n"
        "📌 [Manzilni shu yerga kiriting]\n\n"
        "🗺 Lokatsiya:",
        parse_mode="Markdown"
    )
    # Lokatsiya yuborish (koordinatalarni o'zgartiring)
    await update.message.reply_location(
        latitude=41.2995,   # ← O'zingizning koordinatangizni kiriting
        longitude=69.2401   # ← O'zingizning koordinatangizni kiriting
    )

async def boglanish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bog'lanish ma'lumotlari"""
    await update.message.reply_text(
        "📞 *Bog'lanish:*\n\n"
        "📱 Telefon: +998XXXXXXXXX\n"
        "💬 Telegram: @username\n"
        "📸 Instagram: @togtagi_resort\n\n"
        "⏰ Ish vaqti: 24/7",
        parse_mode="Markdown"
    )

# ==================== ADMIN BUYRUQLARI ====================

async def admin_band(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: xonani band qilish. Format: /band 1 15.06.2025"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        args = context.args
        xona_id = int(args[0])
        sana = args[1]
        
        if xona_id not in XONALAR:
            await update.message.reply_text("❌ Xona topilmadi")
            return
        
        if sana not in XONALAR[xona_id]["band_kunlar"]:
            XONALAR[xona_id]["band_kunlar"].append(sana)
        
        await update.message.reply_text(
            f"✅ {XONALAR[xona_id]['nomi']} — {sana} sanasida BAND qilindi"
        )
    except (IndexError, ValueError):
        await update.message.reply_text(
            "❌ Format: /band 1 15.06.2025\n(xona raqami va sana)"
        )

async def admin_bosh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: xonani bo'sh qilish. Format: /bosh 1 15.06.2025"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        args = context.args
        xona_id = int(args[0])
        sana = args[1]
        
        if xona_id not in XONALAR:
            await update.message.reply_text("❌ Xona topilmadi")
            return
        
        if sana in XONALAR[xona_id]["band_kunlar"]:
            XONALAR[xona_id]["band_kunlar"].remove(sana)
        
        await update.message.reply_text(
            f"✅ {XONALAR[xona_id]['nomi']} — {sana} sanasida BO'SH qilindi"
        )
    except (IndexError, ValueError):
        await update.message.reply_text(
            "❌ Format: /bosh 1 15.06.2025\n(xona raqami va sana)"
        )

async def admin_holat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: barcha xonalar holati"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    matn = "📊 *Barcha xonalar holati:*\n\n"
    
    for xona_id, xona in XONALAR.items():
        band = xona["band_kunlar"]
        if band:
            band_matn = ", ".join(band[-3:])  # Oxirgi 3 ta
            matn += f"🔴 {xona['nomi']} ({xona[\"sig'im\"]} kishi) — Band: {band_matn}\n"
        else:
            matn += f"🟢 {xona['nomi']} ({xona[\"sig'im\"]} kishi) — Bo'sh\n"
    
    matn += "\n*Buyruqlar:*\n"
    matn += "/band [xona] [sana] — Band qilish\n"
    matn += "/bosh [xona] [sana] — Bo'sh qilish\n"
    matn += "Misol: /band 1 15.06.2025"
    
    await update.message.reply_text(matn, parse_mode="Markdown")

# ==================== ASOSIY FUNKSIYA ====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Bron qilish suhbati
    bron_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🏨 Xona bron qilish$"), bron_boshlash)
        ],
        states={
            NECHA_KISHI: [MessageHandler(filters.TEXT & ~filters.COMMAND, necha_kishi)],
            GURUH_TURI: [MessageHandler(filters.TEXT & ~filters.COMMAND, guruh_turi)],
            SANA: [MessageHandler(filters.TEXT & ~filters.COMMAND, sana_olish)],
            ISM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ism_olish)],
            TELEFON: [MessageHandler(filters.TEXT & ~filters.COMMAND, telefon_olish)],
            TASDIQLASH: [CallbackQueryHandler(tasdiqlash)],
        },
        fallbacks=[CommandHandler("bekor", bekor_qilish)],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(bron_handler)
    
    # Menyu tugmalari
    app.add_handler(MessageHandler(filters.Regex("^📋 Bo'sh xonalarni ko'rish$"), bosh_xonalar))
    app.add_handler(MessageHandler(filters.Regex("^📍 Manzil va lokatsiya$"), manzil))
    app.add_handler(MessageHandler(filters.Regex("^📞 Bog'lanish$"), boglanish))
    
    # Admin buyruqlari
    app.add_handler(CommandHandler("band", admin_band))
    app.add_handler(CommandHandler("bosh", admin_bosh))
    app.add_handler(CommandHandler("holat", admin_holat))
    
    print("✅ Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
