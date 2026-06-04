import os
import pytz

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Vaqt zonasi - Uzbekiston (UTC+5)
TZ = pytz.timezone("Asia/Tashkent")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

TELEFON1 = "+998993342035"
TELEFON2 = "+998704902025"
INSTAGRAM = "https://instagram.com/togtagi"
DIRECTOR_IDS = [8886176055, 7323184602]

# Til matni
M = {
    "uz": {
        "xush_kelibsiz": "Tog Tagi Resort ga xush kelibsiz!\n\nShohimardon tog'lari bag'rida dam oling!\n\n🌊 Soy | 💦 Sharshara | 🍽 Oshxona\n🔥 Mangal | 🛖 Tapchanlar | 🚗 Parking\n\n📍 Ko'lqubondan 300 metr pastda\n\n📞 +998993342035  |  +998704902025",
        "bron": "🛏 Xona bron qilish",
        "bosh_x": "📅 Bo'sh xonalar",
        "galereya": "🖼 Galereya",
        "xizmatlar": "🌿 Xizmatlar",
        "manzil": "📍 Manzil",
        "boglanish": "📞 Bog'lanish",
        "bronlarim": "🎫 Mening bronlarim",
        "bosh_menu": "🏠 Bosh menyu",
        "necha_kishi": "Nechta kishi kelmoqchisiz?",
        "kimlar": "Kimlar bilan kelmoqchisiz?",
        "oila": "👨‍👩‍👧‍👦 Oila bilan",
        "dostlar": "👬 Do'stlar / Erkaklar",
        "qaysi_sana": "Qaysi sanada kelmoqchisiz?",
        "necha_kun": "Necha kun turmoqchisiz?",
        "ism_kirit": "Ismingizni kiriting:",
        "tel_yuvor": "Telefon raqamingizni yuboring:\n\nYoki kiriting: +998901234567",
        "kontakt": "📱 Kontaktni yuborish",
        "tasdiq": "Tasdiqlaysizmi?",
        "ha": "✅ Tasdiqlash",
        "bekor": "❌ Bekor",
        "bron_yuborildi": "Sorovingiz qabul qilindi!\n\nBron ID: #{bid}\nXona: {xona}\nSana: {sana} - {tugash}\nKishi: {kishi}\nNarx: {narx} som\n\nAdmin tasdiqlashini kuting.\n+998993342035",
        "bron_tasdiq": "Broningiz tasdiqlandi!\n\nBron ID: #{bid}\nXona: {xona}\nSana: {sana} - {tugash}\nKishi: {kishi}\nNarx: {narx} som\n\nKelishingizni kutamiz!",
        "bron_rad": "Bron #{bid} rad etildi. Boglanish: +998993342035",
        "bron_bekor": "Bron #{bid} bekor qilindi.",
        "eslatma_1kun": "Eslatma! Ertaga resortga kelasiz:\nBron #{bid} | {xona} | {sana}",
        "vaqt_tugaydi": "Bugun 12:00 da xonadagi vaqtingiz tugaydi.\nXonani boshatishingizni so'raymiz.\nTapchanlardan kechgacha foydalanishingiz mumkin!",
        "xona_yoq": "Bu sanada mos bosh xona yoq.\n\nBoglanish: +998993342035",
        "ortiqcha": "{xona}da {sigim} joy bor, siz {kishi} kishi. 1 kishi qoshimcha joy topishi kerak.",
        "xizm_matn": "Tog Tagi Resort Xizmatlari:\n\n🌊 Soy boyida\n💦 Sharshara\n🍽 Oshxona (ozingiz pishirasiz)\n🔥 Mangal\n🥩 Shashlik\n📶 WiFi\n📺 Televizor\n🛏 Yotoq joylar\n🛖 Tapchanlar\n🚗 Bepul parking\n🌿 Yashil tabiat\n\n📞 +998993342035",
        "manzil_matn": "Tog Tagi Resort:\n\nShohimardon, Fargona viloyati\nKolqubondan 300 metr pastda\n\n📞 +998993342035",
        "boglanish_matn": "Boglanish:\n\n📱 +998993342035\n📱 +998704902025\n📸 @togtagi\n⏰ 24/7",
        "galereya_yoq": "Hozircha rasm/video yoq.",
        "bronlarim_yoq": "Hozircha bronlaringiz yoq.",
        "ijtimoiy": "🌐 Ijtimoiy tarmoqlar",
        "ijtimoiy_yoq": "Hozircha ijtimoiy tarmoqlar yoq.",
        "xato": "Xatolik yuz berdi. Boglanish: +998993342035",
    },
    "uz_kril": {
        "xush_kelibsiz": "Тог Таги Резортга хуш келибсиз!\n\nШоҳимардон тоғлари бағрида дам олинг!\n\n🌊 Соy | 💦 Шаршара | 🍽 Ошхона\n🔥 Мангал | 🛖 Тапчанлар | 🚗 Паркинг\n\n📍 Кўлқубондан 300 метр пастда\n\n📞 +998993342035  |  +998704902025",
        "bron": "🛏 Хона брон қилиш",
        "bosh_x": "📅 Бўш хоналар",
        "galereya": "🖼 Галерея",
        "xizmatlar": "🌿 Хизматлар",
        "manzil": "📍 Манзил",
        "boglanish": "📞 Боғланиш",
        "bronlarim": "🎫 Менинг бронларим",
        "bosh_menu": "🏠 Бош меню",
        "necha_kishi": "Неча киши келмоқчисиз?",
        "kimlar": "Кимлар билан келмоқчисиз?",
        "oila": "👨‍👩‍👧‍👦 Оила билан",
        "dostlar": "👬 Дўстлар / Эркаклар",
        "qaysi_sana": "Қайси санада келмоқчисиз?",
        "necha_kun": "Неча кун турмоқчисиз?",
        "ism_kirit": "Исмингизни киритинг:",
        "tel_yuvor": "Телефон рақамингизни юборинг:\n\nЁки киритинг: +998901234567",
        "kontakt": "📱 Контактни юбориш",
        "tasdiq": "Тасдиқлайсизми?",
        "ha": "✅ Тасдиқлаш",
        "bekor": "❌ Бекор",
        "bron_yuborildi": "Сўровингиз қабул қилинди!\n\nБрон ID: #{bid}\nХона: {xona}\nСана: {sana} - {tugash}\nКиши: {kishi}\nНарх: {narx} сўм\n\nАдмин тасдиқлашини кутинг.",
        "bron_tasdiq": "Бронингиз тасдиқланди!\n\nБрон ID: #{bid}\nХона: {xona}\nСана: {sana} - {tugash}\nКиши: {kishi}\nНарх: {narx} сўм",
        "bron_rad": "Брон #{bid} рад этилди.",
        "bron_bekor": "Брон #{bid} бекор қилинди.",
        "eslatma_1kun": "Эслатма! Эртага резортга келасиз:\nБрон #{bid} | {xona} | {sana}",
        "vaqt_tugaydi": "Бугун 12:00 да хонадаги вақтингиз тугайди.\nТапчанлардан кечгача фойдаланишингиз мумкин!",
        "xona_yoq": "Бу санада мос бўш хона йўқ.\n\nБоғланиш: +998993342035",
        "ortiqcha": "{xona}да {sigim} жой бор, сиз {kishi} киши. 1 киши қўшимча жой топиши керак.",
        "xizm_matn": "Тог Таги Резорт Хизматлари:\n\n🌊 Соy бўйида\n💦 Шаршара\n🍽 Ошхона\n🔥 Мангал\n🥩 Шашлик\n📶 WiFi\n📺 Телевизор\n🛏 Ётоқ жойлар\n🛖 Тапчанлар\n🚗 Бепул паркинг",
        "manzil_matn": "Тог Таги Резорт:\n\nШоҳимардон, Фарғона вилояти\nКўлқубондан 300 метр пастда",
        "boglanish_matn": "Боғланиш:\n\n📱 +998993342035\n📱 +998704902025\n📸 @togtagi\n⏰ 24/7",
        "galereya_yoq": "Ҳозирча расм/видео йўқ.",
        "bronlarim_yoq": "Ҳозирча бронларингиз йўқ.",
        "ijtimoiy": "🌐 Ижтимоий тармоқлар",
        "ijtimoiy_yoq": "Ҳозирча йўқ.",
        "xato": "Хатолик юз берди. Боғланиш: +998993342035",
    },
    "ru": {
        "xush_kelibsiz": "Добро пожаловать в Tog Tagi Resort!\n\nОтдохните в горах Шахимардона!\n\n🌊 Река | 💦 Водопад | 🍽 Кухня\n🔥 Мангал | 🛖 Беседки | 🚗 Парковка\n\n📍 В 300 метрах ниже Кулькубона\n\n📞 +998993342035  |  +998704902025",
        "bron": "🛏 Забронировать",
        "bosh_x": "📅 Свободные номера",
        "galereya": "🖼 Галерея",
        "xizmatlar": "🌿 Услуги",
        "manzil": "📍 Адрес",
        "boglanish": "📞 Контакты",
        "bronlarim": "🎫 Мои брони",
        "bosh_menu": "🏠 Главное меню",
        "necha_kishi": "Сколько человек приедет?",
        "kimlar": "С кем приедете?",
        "oila": "👨‍👩‍👧‍👦 С семьёй",
        "dostlar": "👬 С друзьями",
        "qaysi_sana": "На какую дату?",
        "necha_kun": "На сколько ночей?",
        "ism_kirit": "Введите ваше имя:",
        "tel_yuvor": "Отправьте номер телефона:\n\nИли введите: +998901234567",
        "kontakt": "📱 Отправить контакт",
        "tasdiq": "Подтверждаете?",
        "ha": "✅ Подтвердить",
        "bekor": "❌ Отмена",
        "bron_yuborildi": "Заявка принята!\n\nID брони: #{bid}\nНомер: {xona}\nДата: {sana} - {tugash}\nЧел.: {kishi}\nСумма: {narx} сум\n\nОжидайте подтверждения.",
        "bron_tasdiq": "Бронь подтверждена!\n\nID: #{bid}\nНомер: {xona}\nДата: {sana} - {tugash}\nЧел.: {kishi}\nСумма: {narx} сум",
        "bron_rad": "Бронь #{bid} отклонена.",
        "bron_bekor": "Бронь #{bid} отменена.",
        "eslatma_1kun": "Напоминание! Завтра приедете:\nБронь #{bid} | {xona} | {sana}",
        "vaqt_tugaydi": "Сегодня в 12:00 время в номере заканчивается.\nБеседки до вечера в вашем распоряжении!",
        "xona_yoq": "На эту дату нет свободных номеров.\n\nСвяжитесь: +998993342035",
        "ortiqcha": "В {xona} мест {sigim}, вас {kishi}. 1 человек лишний.",
        "xizm_matn": "Услуги Tog Tagi Resort:\n\n🌊 Берег реки\n💦 Водопад\n🍽 Кухня (готовите сами)\n🔥 Мангал\n🥩 Шашлык\n📶 WiFi\n📺 Телевизор\n🛏 Спальные места\n🛖 Беседки\n🚗 Бесплатная парковка",
        "manzil_matn": "Tog Tagi Resort:\n\nШахимардон, Ферганская область\nВ 300 метрах ниже Кулькубона",
        "boglanish_matn": "Контакты:\n\n📱 +998993342035\n📱 +998704902025\n📸 @togtagi\n⏰ 24/7",
        "galereya_yoq": "Пока нет фото/видео.",
        "bronlarim_yoq": "У вас пока нет броней.",
        "ijtimoiy": "🌐 Социальные сети",
        "ijtimoiy_yoq": "Пока нет.",
        "xato": "Произошла ошибка. Свяжитесь: +998993342035",
    }
}


def txt(uid, kalit, **kw):
    from db import get_til
    til = get_til(uid) or "uz"
    s = M.get(til, M["uz"]).get(kalit, kalit)
    try:
        return s.format(**kw)
    except:
        return s
