import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = 8886176055
ADMIN_CHAT_ID = 8886176055

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

XONALAR = {
    1: {"nomi": "1-xona", "qavat": 1, "sigim": 3, "band_kunlar": []},
    2: {"nomi": "2-xona", "qavat": 1, "sigim": 3, "band_kunlar": []},
    3: {"nomi": "3-xona", "qavat": 1, "sigim": 7, "band_kunlar": []},
    4: {"nomi": "4-xona", "qavat": 1, "sigim": 7, "band_kunlar": []},
    5: {"nomi": "5-xona", "qavat": 2, "sigim": 3, "band_kunlar": []},
    6: {"nomi": "6-xona", "qavat": 2, "sigim": 3, "band_kunlar": []},
    7: {"nomi": "7-xona", "qavat": 2, "sigim": 3, "band_kunlar": []},
    8: {"nomi": "8-xona", "qavat": 2, "sigim": 3, "band_kunlar": []},
    9: {"nomi": "9-xona", "qavat": 2, "sigim": 3, "band_kunlar": []},
    10: {"nomi": "10-xona", "qavat": 2, "sigim": 3, "band_kunlar": []},
}

class BronState(StatesGroup):
    necha_kishi = State()
    guruh_turi = State()
    sana = State()
    ism = State()
    telefon = State()
    tasdiqlash = State()

def xona_band_mi(xona_id, sana):
    return sana in XONALAR[xona_id]["band_kunlar"]

def mos_xonalar_top(kishi_soni, guruh_turi, sana):
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

def asosiy_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Xona bron qilish")],
        [KeyboardButton(text="Bosh xonalarni korish")],
        [KeyboardButton(text="Manzil va lokatsiya")],
        [KeyboardButton(text="Boglanish")],
    ], resize_keyboard=True)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Tog Tagi Resort ga xush kelibsiz!\n\nTog bagride dam olish uchun eng yaxshi joy.\nQuyidagi bolimlardan birini tanlang:",
        reply_markup=asosiy_menu()
    )

@dp.message(F.text == "Xona bron qilish")
async def bron_boshlash(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
        [KeyboardButton(text="4"), KeyboardButton(text="5"), KeyboardButton(text="6")],
        [KeyboardButton(text="7"), KeyboardButton(text="8"), KeyboardButton(text="9")],
    ], resize_keyboard=True)
    await message.answer("Nechta kishi kelmoqchisiz?\n\nRaqam tanlang:", reply_markup=kb)
    await state.set_state(BronState.necha_kishi)

@dp.message(BronState.necha_kishi)
async def necha_kishi_handler(message: types.Message, state: FSMContext):
    try:
        son = int(message.text.strip())
        if son < 1 or son > 14:
            raise ValueError
        await state.update_data(kishi_soni=son)
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Oila bilan")],
            [KeyboardButton(text="Dostlar yoki erkaklar guruh")],
        ], resize_keyboard=True)
        await message.answer(f"{son} kishi.\n\nKimlar bilan kelmoqchisiz?", reply_markup=kb)
        await state.set_state(BronState.guruh_turi)
    except ValueError:
        await message.answer("Iltimos, togri raqam kiriting (1-14)")

@dp.message(BronState.guruh_turi)
async def guruh_turi_handler(message: types.Message, state: FSMContext):
    if "Oila" in message.text:
        guruh = "oila"
    else:
        guruh = "dostlar"
    await state.update_data(guruh_turi=guruh)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/bekor")]], resize_keyboard=True)
    await message.answer("Qaysi sanada kelmoqchisiz?\n\nMasalan: 15.06.2025", reply_markup=kb)
    await state.set_state(BronState.sana)

@dp.message(BronState.sana)
async def sana_handler(message: types.Message, state: FSMContext):
    matn = message.text.strip()
    try:
        sana_obj = datetime.strptime(matn, "%d.%m.%Y")
        if sana_obj.date() < datetime.now().date():
            await message.answer("Otgan sana kiritdingiz. Kelajakdagi sana kiriting.")
            return
        data = await state.get_data()
        mos = mos_xonalar_top(data["kishi_soni"], data["guruh_turi"], matn)
        if not mos:
            await message.answer("Bu sanada sizga mos bosh xona yoq. Boshqa sana sinab koring.")
            return
        await state.update_data(sana=matn, mos_xonalar=[(x[0], x[1]["nomi"]) for x in mos[:3]])
        xona_txt = "Sizga mos bosh xonalar:\n\n"
        for xona_id, xona, _ in mos[:5]:
            qavat = "1-qavat (oilalar uchun)" if xona["qavat"] == 1 else "2-qavat (dostlar uchun)"
            xona_txt += f"{xona['nomi']} — {xona['sigim']} kishi — {qavat}\n"
        kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/bekor")]], resize_keyboard=True)
        await message.answer(f"Sana: {matn}\n\n{xona_txt}\nIsmingizni kiriting:", reply_markup=kb)
        await state.set_state(BronState.ism)
    except ValueError:
        await message.answer("Nototri format. Iltimos: 15.06.2025")

@dp.message(BronState.ism)
async def ism_handler(message: types.Message, state: FSMContext):
    await state.update_data(ism=message.text.strip())
    await message.answer("Telefon raqamingizni kiriting:\n\nMasalan: +998901234567")
    await state.set_state(BronState.telefon)

@dp.message(BronState.telefon)
async def telefon_handler(message: types.Message, state: FSMContext):
    await state.update_data(telefon=message.text.strip())
    data = await state.get_data()
    xona_nomlari = ", ".join([x[1] for x in data["mos_xonalar"]])
    matn = (
        "Bron malumotlari:\n\n"
        f"Ism: {data['ism']}\n"
        f"Telefon: {data['telefon']}\n"
        f"Sana: {data['sana']}\n"
        f"Kishi soni: {data['kishi_soni']}\n"
        f"Mos xonalar: {xona_nomlari}\n\n"
        "Malumotlar togrimikin?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Ha, tasdiqlash", callback_data="tasdiqlash"),
            InlineKeyboardButton(text="Bekor qilish", callback_data="bekor"),
        ]
    ])
    await message.answer(matn, reply_markup=kb)
    await state.set_state(BronState.tasdiqlash)

@dp.callback_query(F.data == "bekor")
async def bekor_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Bron bekor qilindi.")
    await callback.answer()

@dp.callback_query(F.data == "tasdiqlash")
async def tasdiqlash_callback(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user
    xona_nomlari = ", ".join([x[1] for x in data.get("mos_xonalar", [])])
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
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_xabar)
    except Exception as e:
        logger.error(f"Admin ga xabar yuborishda xato: {e}")
    await callback.message.edit_text(
        "Bron sorovingiz qabul qilindi!\n\nTez orada siz bilan boglanamiz.\nSavollar uchun: +998XXXXXXXXX"
    )
    await state.clear()
    await callback.answer()

@dp.message(Command("bekor"))
async def bekor_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi. /start bosing.", reply_markup=asosiy_menu())

@dp.message(F.text == "Bosh xonalarni korish")
async def bosh_xonalar(message: types.Message):
    bugun = datetime.now().strftime("%d.%m.%Y")
    matn = "Tog Tagi Resort — Xonalar:\n\n1-qavat (Oilalar uchun qulay):\n"
    for xona_id in [1, 2, 3, 4]:
        xona = XONALAR[xona_id]
        holat = "Band" if xona_band_mi(xona_id, bugun) else "Bosh"
        matn += f"  {xona['nomi']} — {xona['sigim']} kishi — {holat}\n"
    matn += "\n2-qavat (Dostlar uchun qulay):\n"
    for xona_id in [5, 6, 7, 8, 9, 10]:
        xona = XONALAR[xona_id]
        holat = "Band" if xona_band_mi(xona_id, bugun) else "Bosh"
        matn += f"  {xona['nomi']} — {xona['sigim']} kishi — {holat}\n"
    matn += "\nBron qilish uchun 'Xona bron qilish' tugmasini bosing"
    await message.answer(matn)

@dp.message(F.text == "Manzil va lokatsiya")
async def manzil(message: types.Message):
    await message.answer("Tog Tagi Resort manzili:\n\nManzilni shu yerga kiriting")
    await message.answer_location(latitude=41.2995, longitude=69.2401)

@dp.message(F.text == "Boglanish")
async def boglanish(message: types.Message):
    await message.answer(
        "Boglanish:\n\nTelefon: +998XXXXXXXXX\nInstagram: @togtagi_resort\n\nIsh vaqti: 24/7"
    )

@dp.message(Command("band"))
async def admin_band(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        args = message.text.split()[1:]
        xona_id = int(args[0])
        sana = args[1]
        if xona_id not in XONALAR:
            await message.answer("Xona topilmadi")
            return
        if sana not in XONALAR[xona_id]["band_kunlar"]:
            XONALAR[xona_id]["band_kunlar"].append(sana)
        await message.answer(f"{XONALAR[xona_id]['nomi']} — {sana} BAND qilindi")
    except (IndexError, ValueError):
        await message.answer("Format: /band 1 15.06.2025")

@dp.message(Command("bosh"))
async def admin_bosh(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        args = message.text.split()[1:]
        xona_id = int(args[0])
        sana = args[1]
        if xona_id not in XONALAR:
            await message.answer("Xona topilmadi")
            return
        if sana in XONALAR[xona_id]["band_kunlar"]:
            XONALAR[xona_id]["band_kunlar"].remove(sana)
        await message.answer(f"{XONALAR[xona_id]['nomi']} — {sana} BOSH qilindi")
    except (IndexError, ValueError):
        await message.answer("Format: /bosh 1 15.06.2025")

@dp.message(Command("holat"))
async def admin_holat(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    matn = "Barcha xonalar holati:\n\n"
    for xona_id, xona in XONALAR.items():
        band = xona["band_kunlar"]
        if band:
            matn += f"Band: {xona['nomi']} ({xona['sigim']} kishi) — {', '.join(band[-3:])}\n"
        else:
            matn += f"Bosh: {xona['nomi']} ({xona['sigim']} kishi)\n"
    matn += "\n/band 1 15.06.2025 — band qilish\n/bosh 1 15.06.2025 — bosh qilish"
    await message.answer(matn)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
