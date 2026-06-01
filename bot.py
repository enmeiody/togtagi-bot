import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = 8886176055
ADMIN_CHAT_ID = 8886176055

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

logging.basicConfig(level=logging.INFO)

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

class Bron(StatesGroup):
    kishi = State()
    guruh = State()
    sana = State()
    ism = State()
    telefon = State()
    tasdiq = State()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

def asosiy_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Xona bron qilish"))
    kb.add(KeyboardButton("Bosh xonalarni korish"))
    kb.add(KeyboardButton("Manzil va lokatsiya"))
    kb.add(KeyboardButton("Boglanish"))
    return kb

def mos_xonalar(kishi_soni, guruh, sana):
    mos = []
    for xid, x in XONALAR.items():
        if sana in x["band"]:
            continue
        if x["sigim"] < kishi_soni:
            continue
        p = 1 if (guruh == "oila" and x["qavat"] == 1) or (guruh == "dost" and x["qavat"] == 2) else 2
        mos.append((xid, x, p))
    mos.sort(key=lambda a: (a[2], a[0]))
    return mos

@dp.message_handler(commands=["start"], state="*")
async def start(msg: types.Message, state: FSMContext):
    await state.finish()
    await msg.answer("Tog Tagi Resort ga xush kelibsiz!\n\nQuyidagi bolimlardan birini tanlang:", reply_markup=asosiy_menu())

@dp.message_handler(lambda m: m.text == "Xona bron qilish", state="*")
async def bron_start(msg: types.Message, state: FSMContext):
    await state.finish()
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add("1","2","3","4","5","6","7","8","9")
    await msg.answer("Nechta kishi kelmoqchisiz?", reply_markup=kb)
    await Bron.kishi.set()

@dp.message_handler(state=Bron.kishi)
async def kishi_handler(msg: types.Message, state: FSMContext):
    try:
        n = int(msg.text)
        if n < 1 or n > 14:
            raise ValueError
        await state.update_data(kishi=n)
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("Oila bilan", "Dostlar yoki erkaklar")
        await msg.answer(f"{n} kishi.\n\nKimlar bilan kelmoqchisiz?", reply_markup=kb)
        await Bron.guruh.set()
    except ValueError:
        await msg.answer("Iltimos 1-14 orasida raqam kiriting.")

@dp.message_handler(state=Bron.guruh)
async def guruh_handler(msg: types.Message, state: FSMContext):
    g = "oila" if "Oila" in msg.text else "dost"
    await state.update_data(guruh=g)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("/bekor")
    await msg.answer("Qaysi sanada kelmoqchisiz?\n\nMasalan: 15.06.2025", reply_markup=kb)
    await Bron.sana.set()

@dp.message_handler(state=Bron.sana)
async def sana_handler(msg: types.Message, state: FSMContext):
    t = msg.text.strip()
    try:
        d = datetime.strptime(t, "%d.%m.%Y")
        if d.date() < datetime.now().date():
            await msg.answer("Otgan sana. Kelajakdagi sana kiriting.")
            return
        data = await state.get_data()
        mos = mos_xonalar(data["kishi"], data["guruh"], t)
        if not mos:
            await msg.answer("Bu sanada mos bosh xona yoq. Boshqa sana kiriting.")
            return
        await state.update_data(sana=t, xonalar=[(a[0], a[1]["nomi"]) for a in mos[:3]])
        txt = "Sizga mos xonalar:\n\n"
        for xid, x, _ in mos[:5]:
            q = "1-qavat (oila)" if x["qavat"]==1 else "2-qavat (dostlar)"
            txt += f"{x['nomi']} — {x['sigim']} kishi — {q}\n"
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("/bekor")
        await msg.answer(f"Sana: {t}\n\n{txt}\nIsmingizni kiriting:", reply_markup=kb)
        await Bron.ism.set()
    except ValueError:
        await msg.answer("Format: 15.06.2025")

@dp.message_handler(state=Bron.ism)
async def ism_handler(msg: types.Message, state: FSMContext):
    await state.update_data(ism=msg.text.strip())
    await msg.answer("Telefon raqamingizni kiriting:\nMasalan: +998901234567")
    await Bron.telefon.set()

@dp.message_handler(state=Bron.telefon)
async def telefon_handler(msg: types.Message, state: FSMContext):
    await state.update_data(telefon=msg.text.strip())
    data = await state.get_data()
    xona_txt = ", ".join([x[1] for x in data["xonalar"]])
    matn = (
        "Bron malumotlari:\n\n"
        f"Ism: {data['ism']}\n"
        f"Telefon: {data['telefon']}\n"
        f"Sana: {data['sana']}\n"
        f"Kishi soni: {data['kishi']}\n"
        f"Mos xonalar: {xona_txt}\n\n"
        "Togrimikin?"
    )
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Ha, tasdiqlash", callback_data="tasdiq"),
        InlineKeyboardButton("Bekor", callback_data="bekor")
    )
    await msg.answer(matn, reply_markup=kb)
    await Bron.tasdiq.set()

@dp.callback_query_handler(lambda c: c.data == "bekor", state="*")
async def bekor_cb(cb: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await cb.message.edit_text("Bekor qilindi.")
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data == "tasdiq", state=Bron.tasdiq)
async def tasdiq_cb(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = cb.from_user
    xona_txt = ", ".join([x[1] for x in data.get("xonalar", [])])
    admin_txt = (
        "YANGI BRON SOROVI!\n\n"
        f"Ism: {data.get('ism')}\n"
        f"Telefon: {data.get('telefon')}\n"
        f"Sana: {data.get('sana')}\n"
        f"Kishi: {data.get('kishi')}\n"
        f"Guruh: {data.get('guruh')}\n"
        f"Xonalar: {xona_txt}\n"
        f"Telegram: @{user.username or 'yoq'}\n"
        f"ID: {user.id}"
    )
    try:
        await bot.send_message(ADMIN_CHAT_ID, admin_txt)
    except Exception as e:
        logging.error(e)
    await cb.message.edit_text("Bron sorovingiz qabul qilindi!\nTez orada boglanamiz.")
    await state.finish()
    await cb.answer()

@dp.message_handler(commands=["bekor"], state="*")
async def bekor_cmd(msg: types.Message, state: FSMContext):
    await state.finish()
    await msg.answer("Bekor qilindi.", reply_markup=asosiy_menu())

@dp.message_handler(lambda m: m.text == "Bosh xonalarni korish")
async def bosh_xonalar(msg: types.Message):
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
    await msg.answer(txt)

@dp.message_handler(lambda m: m.text == "Manzil va lokatsiya")
async def manzil(msg: types.Message):
    await msg.answer("Tog Tagi Resort manzili:\n[Manzilni kiriting]")
    await bot.send_location(msg.chat.id, latitude=41.2995, longitude=69.2401)

@dp.message_handler(lambda m: m.text == "Boglanish")
async def boglanish(msg: types.Message):
    await msg.answer("Boglanish:\n\nTelefon: +998XXXXXXXXX\nInstagram: @togtagi_resort\n\nIsh vaqti: 24/7")

@dp.message_handler(commands=["band"])
async def admin_band(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        _, xid, sana = msg.text.split()
        xid = int(xid)
        if sana not in XONALAR[xid]["band"]:
            XONALAR[xid]["band"].append(sana)
        await msg.answer(f"{XONALAR[xid]['nomi']} — {sana} BAND")
    except:
        await msg.answer("Format: /band 1 15.06.2025")

@dp.message_handler(commands=["bosh"])
async def admin_bosh(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        _, xid, sana = msg.text.split()
        xid = int(xid)
        if sana in XONALAR[xid]["band"]:
            XONALAR[xid]["band"].remove(sana)
        await msg.answer(f"{XONALAR[xid]['nomi']} — {sana} BOSH")
    except:
        await msg.answer("Format: /bosh 1 15.06.2025")

@dp.message_handler(commands=["holat"])
async def admin_holat(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    txt = "Xonalar holati:\n\n"
    for xid, x in XONALAR.items():
        if x["band"]:
            txt += f"Band: {x['nomi']} — {', '.join(x['band'][-3:])}\n"
        else:
            txt += f"Bosh: {x['nomi']}\n"
    await msg.answer(txt)

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
