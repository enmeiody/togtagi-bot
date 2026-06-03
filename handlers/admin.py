import logging
from datetime import datetime, timedelta
from io import BytesIO
from telebot import types
from db_module import (db, get_xonalar, get_binolar, xona_band_mi, xona_kunlar_band,
                      band_qil, bosh_qil_bron, bosh_qil_sana, bekor_qil_bron,
                      get_bron, get_bron_xonalar, tugash_sanasi as db_tugash,
                      format_narx, is_admin, is_director, log_harakat, qidir_mijoz,
                      bugungi_statistika)
from texts import TELEFON1, TELEFON2
from utils import bron_id_gen, tugash_sanasi, sana_tugmalari, kunlar_tugmalari, o_n_kunlik_holat

DIRECTOR_IDS = [8886176055, 7323184602]


def admin_menu(uid=None):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        "🏨 Xonalar", "📋 Bronlar (10 kun)",
        "📊 Bugungi holat", "👥 Hozirgi mehmonlar",
        "📅 10 kunlik holat", "👤 Mijoz qidirish",
        "➕ Tezkor bron", "📸 Galereya boshqaruv",
        "📄 Barcha bronlar", "🤖 AI malumot",
        "🔙 Asosiy menyu"
    )
    if uid and is_director(uid):
        kb.add("👮 Adminlar", "📊 Statistika")
    return kb


def register(bot):

    @bot.message_handler(commands=["admin"])
    def admin_panel(msg):
        if not is_admin(msg.from_user.id):
            bot.send_message(msg.chat.id, "Ruxsat yoq")
            return
        bot.send_message(msg.chat.id, "Admin panel:",
                         reply_markup=admin_menu(msg.from_user.id))

    # ==================== XONALAR BOSHQARUVI ====================

    @bot.message_handler(func=lambda m: m.text == "🏨 Xonalar" and is_admin(m.from_user.id))
    def xonalar_panel(msg):
        binolar = get_binolar()
        kb = types.InlineKeyboardMarkup(row_width=1)
        for b in binolar:
            kb.add(types.InlineKeyboardButton(f"🏢 {b['nomi']}", callback_data=f"bino_{b['id']}"))
        if is_director(msg.from_user.id):
            kb.add(types.InlineKeyboardButton("➕ Yangi bino", callback_data="yangi_bino"))
        bot.send_message(msg.chat.id, "Binoni tanlang:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("bino_"))
    def cb_bino(call):
        if not is_admin(call.from_user.id): return
        bino_id = int(call.data.replace("bino_", ""))
        with db() as conn:
            bino = conn.execute("SELECT * FROM binolar WHERE id=?", (bino_id,)).fetchone()
        xonalar = get_xonalar(bino_id)
        kb = types.InlineKeyboardMarkup(row_width=2)
        for x in xonalar:
            bugun = datetime.now().strftime("%d.%m.%Y")
            h = "🔴" if xona_band_mi(x["id"], bugun) else "🟢"
            kb.add(types.InlineKeyboardButton(
                f"{h} {x['nomi']} ({x['sigim']} kishi)",
                callback_data=f"ax_{x['id']}"))
        if is_director(call.from_user.id):
            kb.add(types.InlineKeyboardButton(f"➕ Yangi xona ({bino['nomi']})",
                                               callback_data=f"yangi_xona_{bino_id}"))
        kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="ax_back_binolar"))
        bot.edit_message_text(f"🏢 {bino['nomi']} xonalari:",
                              call.message.chat.id, call.message.message_id,
                              reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ax_") and not c.data.startswith("ax_back"))
    def cb_ax(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("ax_", ""))
        with db() as conn:
            x = conn.execute(
                "SELECT x.*, b.nomi as bino_nomi FROM xonalar x JOIN binolar b ON x.bino_id=b.id WHERE x.id=?",
                (xid,)).fetchone()
            rasmlar = conn.execute("SELECT COUNT(*) as c FROM xona_media WHERE xona_id=? AND tur='photo'", (xid,)).fetchone()["c"]
            videolar = conn.execute("SELECT COUNT(*) as c FROM xona_media WHERE xona_id=? AND tur='video'", (xid,)).fetchone()["c"]

        bugun = datetime.now().strftime("%d.%m.%Y")
        h = "🔴 Band" if xona_band_mi(xid, bugun) else "🟢 Bosh"

        matn = (f"Xona: {x['nomi']} | {x['bino_nomi']}\n"
                f"Qavat: {x['qavat']} | Joy: {x['sigim']} kishi\n"
                f"Narx: {format_narx(x['narx'])} som\n"
                f"Bugun: {h}\n"
                f"Rasmlar: {rasmlar} | Videolar: {videolar}")

        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("📅 Bronlar", callback_data=f"ax_bronlar_{xid}"),
            types.InlineKeyboardButton("🔴 Band", callback_data=f"ax_band_{xid}"),
            types.InlineKeyboardButton("🟢 Bosh", callback_data=f"ax_bosh_{xid}"),
            types.InlineKeyboardButton("📸 Rasmlar", callback_data=f"ax_rasmlar_{xid}"),
            types.InlineKeyboardButton("🎥 Videolar", callback_data=f"ax_videolar_{xid}"),
        )
        if is_director(call.from_user.id):
            kb.add(types.InlineKeyboardButton("💰 Narx o'zgartirish", callback_data=f"ax_narx_{xid}"))
        kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"bino_{x['bino_id']}"))
        bot.edit_message_text(matn, call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ax_bronlar_"))
    def cb_ax_bronlar(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("ax_bronlar_", ""))
        with db() as conn:
            bron_ids = conn.execute("SELECT DISTINCT bron_id FROM bron_xonalar WHERE xona_id=?", (xid,)).fetchall()
            bronlar = []
            for r in bron_ids:
                b = conn.execute("SELECT * FROM bronlar WHERE id=? AND holat != 'bekor'", (r["bron_id"],)).fetchone()
                if b: bronlar.append(b)

        matn = f"Xona bronlari:\n\n"
        kb = types.InlineKeyboardMarkup(row_width=1)

        for b in bronlar[-10:]:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            holat = "✅" if b["holat"] == "tasdiqlangan" else "⏳"
            matn += f"{holat} #{b['id']} | {b['sana']}-{tugash}\n{b['ism']} | {b['telefon']}\n\n"
            kb.add(types.InlineKeyboardButton(
                f"#{b['id']} - {b['ism']} ({b['sana']})",
                callback_data=f"bron_detail_{b['id']}"))

        # 15 kunlik holat
        matn += "15 kunlik holat:\n"
        bugun = datetime.now().date()
        for i in range(15):
            kun = bugun + timedelta(days=i)
            sana_str = kun.strftime("%d.%m.%Y")
            h = "🔴" if xona_band_mi(xid, sana_str) else "🟢"
            matn += f"{h}{kun.strftime('%d/%m')} "
            if (i+1) % 5 == 0: matn += "\n"

        kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"ax_{xid}"))
        bot.edit_message_text(matn, call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("bron_detail_"))
    def cb_bron_detail(call):
        if not is_admin(call.from_user.id): return
        bron_id = call.data.replace("bron_detail_", "")
        b = get_bron(bron_id)
        if not b:
            bot.answer_callback_query(call.id, "Bron topilmadi")
            return
        tugash = tugash_sanasi(b["sana"], b["kunlar"])
        matn = (f"Bron #{b['id']}\n\n"
                f"Ism: {b['ism']}\nTel: {b['telefon']}\n"
                f"Xona: {b['xona']}\n"
                f"Sana: {b['sana']} - {tugash}\n"
                f"Kunlar: {b['kunlar']} | Kishi: {b['kishi']}\n"
                f"Narx: {format_narx(b['narx'])} som\n"
                f"Holat: {b['holat']}")
        kb = types.InlineKeyboardMarkup(row_width=2)
        if b["holat"] == "kutilmoqda":
            kb.add(
                types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_tasdiq_ha_{b['id']}"),
                types.InlineKeyboardButton("❌ Rad etish", callback_data=f"admin_tasdiq_yoq_{b['id']}"))
        if b["holat"] != "bekor":
            kb.add(types.InlineKeyboardButton("🗑 Bekor qilish", callback_data=f"admin_bekor_{b['id']}"))
        bot.edit_message_text(matn, call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("admin_bekor_"))
    def cb_admin_bekor(call):
        if not is_admin(call.from_user.id): return
        bron_id = call.data.replace("admin_bekor_", "")
        b = get_bron(bron_id)
        bekor_qil_bron(bron_id)
        bot.edit_message_text(f"Bron #{bron_id} bekor qilindi",
                              call.message.chat.id, call.message.message_id)
        if b and b["user_id"]:
            try:
                bot.send_message(b["user_id"],
                    f"Bron #{bron_id} admin tomonidan bekor qilindi.\nBoglanish: {TELEFON1}")
            except: pass
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("admin_tasdiq_"))
    def cb_admin_tasdiq(call):
        if not is_admin(call.from_user.id): return
        parts = call.data.split("_")
        action = parts[2]
        bron_id = parts[3]
        b = get_bron(bron_id)
        if not b:
            bot.answer_callback_query(call.id, "Bron topilmadi")
            return

        if action == "ha":
            xid_list = get_bron_xonalar(bron_id)
            for xid in xid_list:
                band_qil(xid, b["sana"], b["kunlar"], bron_id)
            with db() as conn:
                conn.execute("UPDATE bronlar SET holat='tasdiqlangan' WHERE id=?", (bron_id,))
                conn.commit()
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            if b["user_id"]:
                try:
                    bot.send_message(b["user_id"],
                        f"Broningiz tasdiqlandi! #{bron_id}\n\n"
                        f"Xona: {b['xona']}\nSana: {b['sana']} - {tugash}\n"
                        f"Kishi: {b['kishi']}\nNarx: {format_narx(b['narx'])} som\n\n"
                        f"Kelishingizni kutamiz! {TELEFON1}")
                except: pass
            bot.edit_message_text(f"Bron #{bron_id} TASDIQLANDI",
                                  call.message.chat.id, call.message.message_id)
        else:
            bekor_qil_bron(bron_id)
            if b["user_id"]:
                try:
                    bot.send_message(b["user_id"],
                        f"Bron #{bron_id} rad etildi.\nBoglanish: {TELEFON1}")
                except: pass
            bot.edit_message_text(f"Bron #{bron_id} RAD ETILDI",
                                  call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    # ==================== BAND/BOSH ====================

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ax_band_"))
    def cb_ax_band(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("ax_band_", ""))
        from handlers.admin_state import admin_state
        admin_state[call.from_user.id] = {"step": "ax_band_sana", "ax_xid": xid}
        bot.send_message(call.message.chat.id,
            f"Band qilish - xona {xid}\nBoshlanish sanasini tanlang:",
            reply_markup=sana_tugmalari())
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ax_bosh_"))
    def cb_ax_bosh(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("ax_bosh_", ""))
        from handlers.admin_state import admin_state
        admin_state[call.from_user.id] = {"step": "ax_bosh_sana", "ax_xid": xid}
        bot.send_message(call.message.chat.id,
            f"Bosh qilish - xona {xid}\nBoshlanish sanasini tanlang:",
            reply_markup=sana_tugmalari())
        bot.answer_callback_query(call.id)

    # ==================== RASMLAR BOSHQARUVI ====================

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ax_rasmlar_"))
    def cb_ax_rasmlar(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("ax_rasmlar_", ""))
        with db() as conn:
            rasmlar = conn.execute(
                "SELECT * FROM xona_media WHERE xona_id=? AND tur='photo' ORDER BY id",
                (xid,)).fetchall()
            xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]

        if rasmlar:
            matn = f"{xnomi} rasmlari ({len(rasmlar)} ta):\n\nRasmni o'chirish uchun ustiga bosing:"
            kb = types.InlineKeyboardMarkup(row_width=3)
            for r in rasmlar:
                kb.add(types.InlineKeyboardButton(f"🗑 Rasm #{r['id']}", callback_data=f"del_rasm_{r['id']}_{xid}"))
            kb.add(types.InlineKeyboardButton("➕ Yangi rasm", callback_data=f"add_rasm_{xid}"))
            kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"ax_{xid}"))
            bot.send_message(call.message.chat.id, matn, reply_markup=kb)
            # Rasmlarni ko'rsatish
            try:
                media = [types.InputMediaPhoto(rasmlar[0]["file_id"])]
                for r in rasmlar[1:5]:
                    media.append(types.InputMediaPhoto(r["file_id"]))
                bot.send_media_group(call.message.chat.id, media)
            except: pass
        else:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("➕ Rasm yuklash", callback_data=f"add_rasm_{xid}"))
            kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"ax_{xid}"))
            bot.send_message(call.message.chat.id, f"{xnomi} uchun rasm yo'q", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("del_rasm_"))
    def cb_del_rasm(call):
        if not is_admin(call.from_user.id): return
        parts = call.data.split("_")
        rasm_id, xid = int(parts[2]), int(parts[3])
        with db() as conn:
            conn.execute("DELETE FROM xona_media WHERE id=?", (rasm_id,))
            conn.commit()
        bot.answer_callback_query(call.id, "Rasm o'chirildi")
        cb_ax_rasmlar(call)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("add_rasm_"))
    def cb_add_rasm(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("add_rasm_", ""))
        from handlers.admin_state import admin_state
        admin_state[call.from_user.id] = {"step": "xona_rasm", "rasm_xona_id": xid}
        bot.send_message(call.message.chat.id, "Rasmlarni yuboring.\n/done - tugallash")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ax_videolar_"))
    def cb_ax_videolar(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("ax_videolar_", ""))
        from handlers.admin_state import admin_state
        admin_state[call.from_user.id] = {"step": "xona_video", "video_xona_id": xid}
        bot.send_message(call.message.chat.id, "Videolarni yuboring.\n/done - tugallash")
        bot.answer_callback_query(call.id)

    # ==================== BUGUNGI HOLAT ====================

    @bot.message_handler(func=lambda m: m.text == "📊 Bugungi holat" and is_admin(m.from_user.id))
    def bugungi_holat(msg):
        bugun = datetime.now().strftime("%d.%m.%Y")
        matn = f"Bugungi holat ({bugun}):\n\n"
        with db() as conn:
            for b in get_binolar():
                matn += f"🏢 {b['nomi']}:\n"
                for x in get_xonalar(b["id"]):
                    h = "🔴 Band" if xona_band_mi(x["id"], bugun) else "🟢 Bosh"
                    band_info = ""
                    if xona_band_mi(x["id"], bugun):
                        brow = conn.execute(
                            "SELECT bron_id FROM band WHERE xona_id=? AND sana=?",
                            (x["id"], bugun)).fetchone()
                        if brow and brow["bron_id"] != "admin":
                            bron = conn.execute("SELECT * FROM bronlar WHERE id=?", (brow["bron_id"],)).fetchone()
                            if bron:
                                tugash = tugash_sanasi(bron["sana"], bron["kunlar"])
                                band_info = f" | {bron['ism']} | {bron['sana']}-{tugash}"
                    matn += f"  {x['nomi']} ({x['sigim']}) - {h}{band_info}\n"
                matn += "\n"
        bot.send_message(msg.chat.id, matn, reply_markup=admin_menu(msg.from_user.id))

    # ==================== HOZIRGI MEHMONLAR ====================

    @bot.message_handler(func=lambda m: m.text == "👥 Hozirgi mehmonlar" and is_admin(m.from_user.id))
    def hozirgi_mehmonlar(msg):
        bugun = datetime.now().strftime("%d.%m.%Y")
        with db() as conn:
            band_bron_ids = conn.execute(
                "SELECT DISTINCT bron_id FROM band WHERE sana=? AND bron_id != 'admin'",
                (bugun,)).fetchall()
            mehmonlar = []
            for r in band_bron_ids:
                b = conn.execute(
                    "SELECT * FROM bronlar WHERE id=? AND holat='tasdiqlangan'",
                    (r["bron_id"],)).fetchone()
                if b: mehmonlar.append(b)

        if not mehmonlar:
            bot.send_message(msg.chat.id, f"Bugun ({bugun}) hech kim yo'q",
                             reply_markup=admin_menu(msg.from_user.id))
            return

        jami_kishi = sum(b["kishi"] for b in mehmonlar)
        matn = f"Hozirgi mehmonlar ({bugun}):\n\nJami: {len(mehmonlar)} xona | {jami_kishi} kishi\n\n"

        kb = types.InlineKeyboardMarkup(row_width=1)
        for b in mehmonlar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            matn += (f"#{b['id']} | {b['xona']}\n"
                     f"{b['ism']} | {b['telefon']}\n"
                     f"{b['sana']} - {tugash} ({b['kunlar']} kun)\n\n")
            kb.add(types.InlineKeyboardButton(
                f"#{b['id']} - {b['ism']} - Joylashtirildi",
                callback_data=f"mehmon_holat_{b['id']}"))

        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("mehmon_holat_"))
    def cb_mehmon_holat(call):
        if not is_admin(call.from_user.id): return
        bron_id = call.data.replace("mehmon_holat_", "")
        b = get_bron(bron_id)
        if not b: return
        tugash = tugash_sanasi(b["sana"], b["kunlar"])
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("✅ Joylashtirildi", callback_data=f"mehmon_joylash_{bron_id}"))
        kb.add(types.InlineKeyboardButton("🗑 Bronni bekor qilish", callback_data=f"admin_bekor_{bron_id}"))
        bot.edit_message_text(
            f"Mehmon #{bron_id}\n{b['ism']} | {b['telefon']}\n{b['xona']}\n{b['sana']}-{tugash}",
            call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    # ==================== 10 KUNLIK HOLAT ====================

    @bot.message_handler(func=lambda m: m.text == "📅 10 kunlik holat" and is_admin(m.from_user.id))
    def o_n_kunlik(msg):
        bugun = datetime.now().date()
        sanalar = [(bugun + timedelta(days=i)) for i in range(10)]
        xonalar = get_xonalar()

        matn = "10 kunlik xonalar holati:\n\n"
        matn += "Sana: " + " | ".join(k.strftime("%d/%m") for k in sanalar) + "\n\n"

        kb = types.InlineKeyboardMarkup(row_width=1)
        for x in xonalar:
            kun_satri = ""
            for kun in sanalar:
                sana_str = kun.strftime("%d.%m.%Y")
                kun_satri += "🔴" if xona_band_mi(x["id"], sana_str) else "🟢"
            matn += f"{x['nomi']} ({x['sigim']}): {kun_satri}\n"
            kb.add(types.InlineKeyboardButton(
                f"{x['nomi']} - Bron qilish/Ko'rish",
                callback_data=f"ax_{x['id']}"))

        matn += "\n🟢=Bosh 🔴=Band"
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    # ==================== BRONLAR RO'YXATI ====================

    @bot.message_handler(func=lambda m: m.text == "📋 Bronlar (10 kun)" and is_admin(m.from_user.id))
    def bronlar_royxati(msg):
        bugun = datetime.now().date()
        oxiri = bugun + timedelta(days=10)
        with db() as conn:
            bronlar = conn.execute(
                "SELECT * FROM bronlar WHERE holat != 'bekor' ORDER BY sana",
            ).fetchall()
            bronlar = [b for b in bronlar if b["sana"] >= bugun.strftime("%d.%m.%Y") and b["sana"] <= oxiri.strftime("%d.%m.%Y")]

        if not bronlar:
            bot.send_message(msg.chat.id, "Kelayotgan 10 kunda bron yo'q",
                             reply_markup=admin_menu(msg.from_user.id))
            return

        matn = f"Kelayotgan 10 kunlik bronlar ({len(bronlar)} ta):\n\n"
        kb = types.InlineKeyboardMarkup(row_width=1)
        for b in bronlar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            h = "✅" if b["holat"] == "tasdiqlangan" else "⏳"
            matn += f"{h} #{b['id']} | {b['xona']}\n{b['ism']} | {b['sana']}-{tugash}\n\n"
            kb.add(types.InlineKeyboardButton(
                f"{h} #{b['id']} - {b['ism']} ({b['sana']})",
                callback_data=f"bron_detail_{b['id']}"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "📄 Barcha bronlar" and is_admin(m.from_user.id))
    def barcha_bronlar(msg):
        with db() as conn:
            bronlar = conn.execute(
                "SELECT * FROM bronlar ORDER BY created_at DESC").fetchall()
        if not bronlar:
            bot.send_message(msg.chat.id, "Hozircha bron yo'q")
            return
        # Fayl sifatida yuborish
        matn = "BARCHA BRONLAR\n" + "="*40 + "\n\n"
        for b in bronlar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            matn += (f"#{b['id']} | {b['holat'].upper()}\n"
                     f"Ism: {b['ism']} | Tel: {b['telefon']}\n"
                     f"Sana: {b['sana']} - {tugash} | {b['kunlar']} kun\n"
                     f"Xona: {b['xona']} | Kishi: {b['kishi']}\n"
                     f"Narx: {format_narx(b['narx'])} som\n"
                     f"Yaratilgan: {b['created_at']}\n"
                     + "-"*30 + "\n")
        buf = BytesIO(matn.encode("utf-8"))
        buf.name = "bronlar.txt"
        bot.send_document(msg.chat.id, buf, caption=f"Jami: {len(bronlar)} ta bron")

    # ==================== MIJOZ QIDIRISH ====================

    @bot.message_handler(func=lambda m: m.text == "👤 Mijoz qidirish" and is_admin(m.from_user.id))
    def mijoz_qidirish(msg):
        from handlers.admin_state import admin_state
        admin_state[msg.from_user.id] = {"step": "mijoz_qidir"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(msg.chat.id,
            "Mijoz telefon, bron ID yoki username kiriting:",
            reply_markup=kb)

    # ==================== TEZKOR BRON ====================

    @bot.message_handler(func=lambda m: m.text == "➕ Tezkor bron" and is_admin(m.from_user.id))
    def tezkor_bron(msg):
        from handlers.admin_state import admin_state
        admin_state[msg.from_user.id] = {"step": "tb_kishi", "ab": {}}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
        for i in range(1, 11): kb.add(str(i))
        kb.add("🔙 Admin menyu")
        bot.send_message(msg.chat.id, "Tezkor bron\nNechta kishi?", reply_markup=kb)

    # ==================== GALEREYA BOSHQARUVI ====================

    @bot.message_handler(func=lambda m: m.text == "📸 Galereya boshqaruv" and is_admin(m.from_user.id))
    def galereya_boshqaruv(msg):
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("📸 Umumiy rasmlar", callback_data="galereya_umumiy"),
            types.InlineKeyboardButton("🎥 Videolar", callback_data="galereya_videolar"),
            types.InlineKeyboardButton("🖼 Greeting rasmi", callback_data="galereya_greeting"),
        )
        bot.send_message(msg.chat.id, "Galereya:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "galereya_umumiy")
    def cb_galereya_umumiy(call):
        if not is_admin(call.from_user.id): return
        with db() as conn:
            rasmlar = conn.execute("SELECT * FROM umumiy_media WHERE tur='photo' ORDER BY id").fetchall()

        kb = types.InlineKeyboardMarkup(row_width=2)
        for r in rasmlar:
            kb.add(types.InlineKeyboardButton(f"🗑 #{r['id']}", callback_data=f"del_umumiy_{r['id']}"))
        kb.add(types.InlineKeyboardButton("➕ Rasm yuklash", callback_data="add_umumiy_rasm"))

        bot.edit_message_text(
            f"Umumiy rasmlar ({len(rasmlar)} ta):",
            call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("del_umumiy_"))
    def cb_del_umumiy(call):
        if not is_admin(call.from_user.id): return
        mid = int(call.data.replace("del_umumiy_", ""))
        with db() as conn:
            conn.execute("DELETE FROM umumiy_media WHERE id=?", (mid,))
            conn.commit()
        bot.answer_callback_query(call.id, "O'chirildi!")
        cb_galereya_umumiy(call)

    @bot.callback_query_handler(func=lambda c: c.data == "add_umumiy_rasm")
    def cb_add_umumiy(call):
        if not is_admin(call.from_user.id): return
        from handlers.admin_state import admin_state
        admin_state[call.from_user.id] = {"step": "umumiy_rasm"}
        bot.send_message(call.message.chat.id, "Rasmlarni yuboring.\n/done - tugallash")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "galereya_greeting")
    def cb_galereya_greeting(call):
        if not is_admin(call.from_user.id): return
        from handlers.admin_state import admin_state
        admin_state[call.from_user.id] = {"step": "greeting_rasm"}
        bot.send_message(call.message.chat.id, "Greeting rasmini yuboring (faqat 1 ta):")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "galereya_videolar")
    def cb_galereya_videolar(call):
        if not is_admin(call.from_user.id): return
        with db() as conn:
            videolar = conn.execute("SELECT * FROM umumiy_media WHERE tur='video' ORDER BY id").fetchall()
        kb = types.InlineKeyboardMarkup(row_width=2)
        for v in videolar:
            kb.add(types.InlineKeyboardButton(f"🗑 Video #{v['id']}", callback_data=f"del_video_{v['id']}"))
        kb.add(types.InlineKeyboardButton("➕ Video yuklash", callback_data="add_video"))
        bot.edit_message_text(f"Videolar ({len(videolar)} ta):",
                              call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "add_video")
    def cb_add_video(call):
        if not is_admin(call.from_user.id): return
        from handlers.admin_state import admin_state
        admin_state[call.from_user.id] = {"step": "umumiy_video"}
        bot.send_message(call.message.chat.id, "Video yuboring.\n/done - tugallash")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("del_video_"))
    def cb_del_video(call):
        if not is_admin(call.from_user.id): return
        vid = int(call.data.replace("del_video_", ""))
        with db() as conn:
            conn.execute("DELETE FROM umumiy_media WHERE id=?", (vid,))
            conn.commit()
        bot.answer_callback_query(call.id, "O'chirildi!")
        cb_galereya_videolar(call)

    # ==================== AI MALUMOT ====================

    @bot.message_handler(func=lambda m: m.text == "🤖 AI malumot" and is_admin(m.from_user.id))
    def ai_malumot(msg):
        from handlers.admin_state import admin_state
        admin_state[msg.from_user.id] = {"step": "ai_info"}
        with db() as conn:
            rows = conn.execute("SELECT * FROM ai_info ORDER BY id DESC LIMIT 5").fetchall()

        matn = "AI malumotlar:\n\n"
        kb = types.InlineKeyboardMarkup(row_width=1)
        for r in rows:
            matn += f"• {r['matn'][:60]}...\n" if len(r['matn']) > 60 else f"• {r['matn']}\n"
            kb.add(types.InlineKeyboardButton(f"🗑 #{r['id']}", callback_data=f"del_aiinfo_{r['id']}"))
        kb.add(types.InlineKeyboardButton("🗑 Hammasini o'chirish", callback_data="del_all_aiinfo"))

        reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        reply_kb.add("🔙 Admin menyu")
        bot.send_message(msg.chat.id, matn + "\nYangi malumot yozing:", reply_markup=reply_kb)
        if rows:
            bot.send_message(msg.chat.id, "O'chirish:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("del_aiinfo_"))
    def cb_del_aiinfo(call):
        if not is_admin(call.from_user.id): return
        mid = int(call.data.replace("del_aiinfo_", ""))
        with db() as conn:
            conn.execute("DELETE FROM ai_info WHERE id=?", (mid,))
            conn.commit()
        bot.answer_callback_query(call.id, "O'chirildi!")

    @bot.callback_query_handler(func=lambda c: c.data == "del_all_aiinfo")
    def cb_del_all_aiinfo(call):
        if not is_admin(call.from_user.id): return
        with db() as conn:
            conn.execute("DELETE FROM ai_info")
            conn.commit()
        bot.edit_message_text("Barcha AI malumotlar o'chirildi",
                              call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    # ==================== ORQAGA ====================

    @bot.message_handler(func=lambda m: m.text == "🔙 Asosiy menyu" and is_admin(m.from_user.id))
    def admin_back(msg):
        from handlers.mijoz import asosiy_menu
        bot.send_message(msg.chat.id, "Asosiy menyu",
                         reply_markup=asosiy_menu(msg.from_user.id))

    @bot.message_handler(func=lambda m: m.text == "🔙 Admin menyu" and is_admin(m.from_user.id))
    def admin_menyu_back(msg):
        from handlers.admin_state import admin_state
        admin_state.pop(msg.from_user.id, None)
        bot.send_message(msg.chat.id, "Admin panel:",
                         reply_markup=admin_menu(msg.from_user.id))

    # ==================== NARX O'ZGARTIRISH ====================

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ax_narx_") and is_director(c.from_user.id))
    def cb_ax_narx(call):
        xid = int(call.data.replace("ax_narx_", ""))
        from handlers.admin_state import admin_state
        admin_state[call.from_user.id] = {"step": "narx_ozgartir", "narx_xid": xid}
        bot.send_message(call.message.chat.id, "Yangi narxni kiriting (so'mda):")
        bot.answer_callback_query(call.id)

    # ==================== YANGI BINO/XONA ====================

    @bot.callback_query_handler(func=lambda c: c.data == "yangi_bino" and is_director(c.from_user.id))
    def cb_yangi_bino(call):
        from handlers.admin_state import admin_state
        admin_state[call.from_user.id] = {"step": "yangi_bino_nomi"}
        bot.send_message(call.message.chat.id, "Yangi bino nomini kiriting:")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("yangi_xona_") and is_director(c.from_user.id))
    def cb_yangi_xona(call):
        bino_id = int(call.data.replace("yangi_xona_", ""))
        from handlers.admin_state import admin_state
        admin_state[call.from_user.id] = {"step": "yangi_xona_nomi", "bino_id": bino_id}
        bot.send_message(call.message.chat.id,
            "Yangi xona malumotlarini kiriting:\nFormat: nom,qavat,joy_soni,narx\nMisol: 11-xona,1,3,300000")
        bot.answer_callback_query(call.id)

    # ==================== STATISTIKA ====================

    @bot.message_handler(func=lambda m: m.text == "📊 Statistika" and is_director(m.from_user.id))
    def statistika(msg):
        stat = bugungi_statistika()
        matn = (f"Bugungi statistika:\n\n"
                f"Foydalanuvchilar: {stat['jami_foydalanuvchi']}\n"
                f"Yangi bronlar: {stat['yangi_bronlar']}\n\n"
                "Harakatlar:\n")
        for h in stat["harakatlar"]:
            matn += f"  {h['harakat']}: {h['c']} marta\n"
        bot.send_message(msg.chat.id, matn, reply_markup=admin_menu(msg.from_user.id))

    # ==================== ADMINLAR BOSHQARUVI ====================

    @bot.message_handler(func=lambda m: m.text == "👮 Adminlar" and is_director(m.from_user.id))
    def adminlar_panel(msg):
        with db() as conn:
            adminlar = conn.execute("SELECT * FROM adminlar ORDER BY qoshilgan DESC").fetchall()
        matn = "Adminlar:\n\n"
        for a in adminlar:
            ism = a["ism"] or "Nomalum"
            matn += f"ID: {a['user_id']} | {ism}\n"
        matn += f"\nDirectorlar: {', '.join(str(d) for d in DIRECTOR_IDS)}"

        kb = types.InlineKeyboardMarkup(row_width=1)
        for a in adminlar:
            kb.add(types.InlineKeyboardButton(
                f"Del: {a['ism'] or a['user_id']}",
                callback_data=f"del_admin_{a['user_id']}"))
        kb.add(types.InlineKeyboardButton("➕ Admin qo'shish", callback_data="add_admin"))

        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "add_admin" and is_director(c.from_user.id))
    def cb_add_admin(call):
        from handlers.admin_state import admin_state
        admin_state[call.from_user.id] = {"step": "add_admin_id"}
        bot.send_message(call.message.chat.id, "Yangi admin ID sini kiriting:")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("del_admin_") and is_director(c.from_user.id))
    def cb_del_admin(call):
        uid = int(call.data.replace("del_admin_", ""))
        with db() as conn:
            conn.execute("DELETE FROM adminlar WHERE user_id=?", (uid,))
            conn.commit()
        bot.edit_message_text(f"Admin {uid} o'chirildi",
                              call.message.chat.id, call.message.message_id)
        try:
            bot.send_message(uid, "Admin huquqingiz bekor qilindi.")
        except: pass
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ax_back"))
    def cb_ax_back(call):
        if not is_admin(call.from_user.id): return
        binolar = get_binolar()
        kb = types.InlineKeyboardMarkup(row_width=1)
        for b in binolar:
            kb.add(types.InlineKeyboardButton(f"🏢 {b['nomi']}", callback_data=f"bino_{b['id']}"))
        bot.edit_message_text("Binoni tanlang:",
                              call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)
