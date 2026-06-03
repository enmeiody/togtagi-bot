import logging
from datetime import datetime, timedelta
from telebot import types
from db_module import (db, get_xonalar, get_binolar, xona_band_mi, xona_kunlar_band,
                      band_qil, bosh_qil_bron, bekor_qil_bron, get_bron, get_bron_xonalar,
                      format_narx, get_til, set_til, get_yoki_yarat_mijoz, log_harakat, is_admin)
from texts import t, TELEFON1, TELEFON2, INSTAGRAM, MATNLAR
from utils import bron_id_gen, tugash_sanasi, sana_tugmalari, kunlar_tugmalari, mos_kombinatsiya, barcha_bosh_xonalar

user_state = {}


def asosiy_menu(uid):
    til = get_til(uid) or "uz"
    m = MATNLAR[til]
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(m["bron_btn"], m["bosh_xonalar_btn"],
           m["galereya_btn"], m["xizmatlar_btn"],
           m["manzil_btn"], m["mening_bronlarim_btn"])
    return kb


def til_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🇺🇿 O'zbek (lotin)", callback_data="til_uz"),
        types.InlineKeyboardButton("🇺🇿 Ўзбек (кирил)", callback_data="til_uz_kril"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="til_ru"),
    )
    return kb


def register(bot):

    @bot.message_handler(commands=["start"])
    def start(msg):
        uid = msg.from_user.id
        get_yoki_yarat_mijoz(uid, msg.from_user.first_name, msg.from_user.username)
        log_harakat(uid, "start")

        # Bron havola
        if msg.text and "bron_" in msg.text:
            bron_id = msg.text.split("bron_")[-1].strip().upper()
            b = get_bron(bron_id)
            if b:
                tugash = tugash_sanasi(b["sana"], b["kunlar"])
                bot.send_message(uid,
                    f"Bron malumotlari:\n\nID: #{b['id']}\n"
                    f"Xona: {b['xona']}\nSana: {b['sana']} - {tugash}\n"
                    f"Kishi: {b['kishi']}\nNarx: {format_narx(b['narx'])} som\n\n"
                    f"Savollar: {TELEFON1}",
                    reply_markup=asosiy_menu(uid))
                with db() as conn:
                    conn.execute("UPDATE mijozlar SET user_id=? WHERE telefon=?", (uid, b["telefon"]))
                    conn.execute("UPDATE bronlar SET user_id=? WHERE id=?", (uid, bron_id))
                    conn.commit()
            else:
                bot.send_message(uid, f"Bron #{bron_id} topilmadi. Boglanish: {TELEFON1}")
            return

        # Til tanlash
        user_state.pop(uid, None)
        bot.send_message(uid, "Tilni tanlang / Выберите язык:", reply_markup=til_menu())

    @bot.callback_query_handler(func=lambda c: c.data.startswith("til_"))
    def cb_til(call):
        uid = call.from_user.id
        til = call.data.replace("til_", "")
        set_til(uid, til)
        user_state.pop(uid, None)
        try:
            bot.edit_message_text("✅", call.message.chat.id, call.message.message_id)
        except:
            pass

        # Greeting rasmi
        with db() as conn:
            gr = conn.execute("SELECT * FROM greeting_media").fetchone()
        if gr:
            if gr["tur"] == "photo":
                bot.send_photo(uid, gr["file_id"],
                    caption=t(uid, "xush_kelibsiz"),
                    parse_mode="Markdown", reply_markup=asosiy_menu(uid))
            else:
                bot.send_message(uid, t(uid, "xush_kelibsiz"),
                    parse_mode="Markdown", reply_markup=asosiy_menu(uid))
        else:
            bot.send_message(uid, t(uid, "xush_kelibsiz"),
                parse_mode="Markdown", reply_markup=asosiy_menu(uid))
        bot.answer_callback_query(call.id)

    # ==================== BRON ====================

    @bot.message_handler(func=lambda m: m.text and any(
        m.text == MATNLAR[til]["bron_btn"] for til in MATNLAR))
    def bron_start(msg):
        uid = msg.from_user.id
        with db() as conn:
            m2 = conn.execute("SELECT bloklangan FROM mijozlar WHERE user_id=?", (uid,)).fetchone()
            if m2 and m2["bloklangan"]:
                bot.send_message(uid, f"Boglanish: {TELEFON1}")
                return
        user_state[uid] = {"step": "kishi"}
        log_harakat(uid, "bron_boshlash")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
        for i in range(1, 11):
            kb.add(str(i))
        kb.add(t(uid, "bosh_menyu_btn"))
        bot.send_message(uid, t(uid, "necha_kishi"), reply_markup=kb)

    # ==================== BO'SH XONALAR ====================

    @bot.message_handler(func=lambda m: m.text and any(
        m.text == MATNLAR[til]["bosh_xonalar_btn"] for til in MATNLAR))
    def bosh_xonalar(msg):
        uid = msg.from_user.id
        user_state[uid] = {"step": "bosh_kishi"}
        log_harakat(uid, "bosh_xonalar")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
        for i in range(1, 11):
            kb.add(str(i))
        kb.add(t(uid, "bosh_menyu_btn"))
        bot.send_message(uid, t(uid, "necha_kishi"), reply_markup=kb)

    # ==================== GALEREYA ====================

    @bot.message_handler(func=lambda m: m.text and any(
        m.text == MATNLAR[til]["galereya_btn"] for til in MATNLAR))
    def galereya(msg):
        uid = msg.from_user.id
        log_harakat(uid, "galereya")
        with db() as conn:
            photos = conn.execute("SELECT file_id FROM umumiy_media WHERE tur='photo' ORDER BY id").fetchall()
            videos = conn.execute("SELECT file_id FROM umumiy_media WHERE tur='video' ORDER BY id").fetchall()

        if not photos and not videos:
            bot.send_message(uid, t(uid, "galereya_yoq"))
            return

        if photos:
            media_group = []
            for i, p in enumerate(photos[:10]):
                if i == 0:
                    media_group.append(types.InputMediaPhoto(p["file_id"], caption="Tog' Tagi Resort"))
                else:
                    media_group.append(types.InputMediaPhoto(p["file_id"]))
            bot.send_media_group(uid, media_group)

        for v in videos[:3]:
            try:
                bot.send_video(uid, v["file_id"])
            except:
                pass

    # ==================== XIZMATLAR ====================

    @bot.message_handler(func=lambda m: m.text and any(
        m.text == MATNLAR[til]["xizmatlar_btn"] for til in MATNLAR))
    def xizmatlar(msg):
        uid = msg.from_user.id
        log_harakat(uid, "xizmatlar")
        bot.send_message(uid, t(uid, "xizmatlar_matn"))

    # ==================== MANZIL ====================

    @bot.message_handler(func=lambda m: m.text and any(
        m.text == MATNLAR[til]["manzil_btn"] for til in MATNLAR))
    def manzil(msg):
        uid = msg.from_user.id
        log_harakat(uid, "manzil")
        bot.send_message(uid, t(uid, "manzil_matn"))
        bot.send_location(uid, latitude=39.961311, longitude=71.836921)

    # ==================== BOG'LANISH (inline kb bilan) ====================

    @bot.message_handler(func=lambda m: m.text and (
        "Bog" in (m.text or "") and "lanish" in (m.text or "") or
        "Боғланиш" in (m.text or "") or "Контакты" in (m.text or "")))
    def boglanish(msg):
        uid = msg.from_user.id
        log_harakat(uid, "boglanish")
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton(f"📞 {TELEFON1}", url=f"tel:{TELEFON1}"),
            types.InlineKeyboardButton(f"📞 {TELEFON2}", url=f"tel:{TELEFON2}"),
            types.InlineKeyboardButton("📸 Instagram", url=INSTAGRAM),
            types.InlineKeyboardButton(t(uid, "bron_btn"), callback_data="bron_start_cb"),
        )
        bot.send_message(uid, t(uid, "boglanish_matn"), reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "bron_start_cb")
    def cb_bron_start(call):
        uid = call.from_user.id
        user_state[uid] = {"step": "kishi"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
        for i in range(1, 11):
            kb.add(str(i))
        kb.add(t(uid, "bosh_menyu_btn"))
        bot.send_message(uid, t(uid, "necha_kishi"), reply_markup=kb)
        bot.answer_callback_query(call.id)

    # ==================== MENING BRONLARIM ====================

    @bot.message_handler(func=lambda m: m.text and any(
        m.text == MATNLAR[til]["mening_bronlarim_btn"] for til in MATNLAR))
    def mening_bronlarim(msg):
        uid = msg.from_user.id
        log_harakat(uid, "bronlarim")
        with db() as conn:
            bronlar = conn.execute(
                "SELECT * FROM bronlar WHERE user_id=? AND holat != 'bekor' ORDER BY sana DESC LIMIT 10",
                (uid,)).fetchall()

        if not bronlar:
            bot.send_message(uid, t(uid, "bronlarim_yoq"))
            return

        for b in bronlar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            holat_emoji = {"kutilmoqda": "⏳", "tasdiqlangan": "✅", "bekor": "❌"}.get(b["holat"], "❓")
            matn = (f"{holat_emoji} Bron #{b['id']}\n"
                    f"Xona: {b['xona']}\n"
                    f"Sana: {b['sana']} - {tugash}\n"
                    f"Kishi: {b['kishi']}\n"
                    f"Narx: {format_narx(b['narx'])} som")

            kb = types.InlineKeyboardMarkup()
            if b["holat"] in ["kutilmoqda", "tasdiqlangan"]:
                kb.add(types.InlineKeyboardButton(
                    "❌ Bekor qilish", callback_data=f"mijoz_bekor_{b['id']}"))
            bot.send_message(uid, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("mijoz_bekor_"))
    def cb_mijoz_bekor(call):
        uid = call.from_user.id
        bron_id = call.data.replace("mijoz_bekor_", "")
        b = get_bron(bron_id)
        if not b or b["user_id"] != uid:
            bot.answer_callback_query(call.id, "Bron topilmadi")
            return
        bekor_qil_bron(bron_id)
        bot.edit_message_text(t(uid, "bron_bekor").format(bid=bron_id),
                              call.message.chat.id, call.message.message_id)
        # Adminlarga xabar
        from texts import MATNLAR
        for aid in [8886176055, 7323184602]:
            try:
                bot.send_message(aid, f"Bron #{bron_id} BEKOR QILINDI\nMijoz tomonidan\n{b['ism']} | {b['telefon']}")
            except:
                pass
        bot.answer_callback_query(call.id)

    # ==================== BOSH MENYU ====================

    @bot.message_handler(func=lambda m: m.text and any(
        m.text == MATNLAR[til]["bosh_menyu_btn"] for til in MATNLAR))
    def bosh_menyu(msg):
        uid = msg.from_user.id
        user_state.pop(uid, None)
        bot.send_message(uid, "👇", reply_markup=asosiy_menu(uid))

    # ==================== SANA VA KUN CALLBACK ====================

    @bot.callback_query_handler(func=lambda c: c.data.startswith("sana_"))
    def cb_sana_mijoz(call):
        from handlers.admin_state import admin_state
        uid = call.from_user.id
        cid = call.message.chat.id
        sana = call.data.replace("sana_", "")

        # Admin uchun maxsus steplar
        if is_admin(uid):
            a_state = admin_state.get(uid, {})
            step = a_state.get("step")
            if step == "ax_band_sana":
                a_state["ax_sana"] = sana
                a_state["step"] = "ax_band_kunlar"
                admin_state[uid] = a_state
                bot.send_message(cid, f"Sana: {sana}\nNecha kun band?", reply_markup=kunlar_tugmalari())
                bot.answer_callback_query(call.id)
                return
            elif step == "ax_bosh_sana":
                a_state["ax_sana"] = sana
                a_state["step"] = "ax_bosh_kunlar"
                admin_state[uid] = a_state
                bot.send_message(cid, f"Sana: {sana}\nNecha kun bosh?", reply_markup=kunlar_tugmalari())
                bot.answer_callback_query(call.id)
                return
            elif step == "tb_sana":
                a_state["ab"]["sana"] = sana
                a_state["step"] = "tb_kunlar"
                admin_state[uid] = a_state
                bot.send_message(cid, f"Sana: {sana}\nNecha kun?", reply_markup=kunlar_tugmalari())
                bot.answer_callback_query(call.id)
                return

        state = user_state.get(uid, {})

        state["sana"] = sana
        state["step"] = "kunlar"
        user_state[uid] = state

        bot.edit_message_text(
            f"Sana: {sana}\n\n{t(uid, 'necha_kun')}",
            cid, call.message.message_id,
            reply_markup=kunlar_tugmalari())
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("kun_"))
    def cb_kun_mijoz(call):
        from handlers.admin_state import admin_state
        from db_module import band_qil, bosh_qil_sana, format_narx
        uid = call.from_user.id
        cid = call.message.chat.id
        kunlar = int(call.data.replace("kun_", ""))

        # Admin uchun maxsus steplar
        if is_admin(uid):
            a_state = admin_state.get(uid, {})
            step = a_state.get("step")
            if step == "ax_band_kunlar":
                xid = a_state["ax_xid"]
                sana = a_state["ax_sana"]
                band_qil(xid, sana, kunlar, "admin")
                admin_state.pop(uid, None)
                with db() as conn:
                    x = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()
                from handlers.admin import admin_menu
                bot.send_message(cid, f"{x['nomi']} - {sana} dan {kunlar} kun BAND qilindi", reply_markup=admin_menu(uid))
                bot.answer_callback_query(call.id)
                return
            elif step == "ax_bosh_kunlar":
                xid = a_state["ax_xid"]
                sana = a_state["ax_sana"]
                bosh_qil_sana(xid, sana, kunlar)
                admin_state.pop(uid, None)
                with db() as conn:
                    x = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()
                from handlers.admin import admin_menu
                bot.send_message(cid, f"{x['nomi']} - {sana} dan {kunlar} kun BOSH qilindi", reply_markup=admin_menu(uid))
                bot.answer_callback_query(call.id)
                return
            elif step == "tb_kunlar":
                a_state["ab"]["kunlar"] = kunlar
                a_state["step"] = "tb_xona"
                admin_state[uid] = a_state
                sana = a_state["ab"]["sana"]
                kishi = a_state["ab"].get("kishi", 1)
                kombinatsiyalar = mos_kombinatsiya(kishi, "oila", sana, kunlar)
                tugash = tugash_sanasi(sana, kunlar)
                from telebot import types as tb_types
                kb = tb_types.InlineKeyboardMarkup(row_width=1)
                if kombinatsiyalar:
                    for x in kombinatsiyalar[0]["xonalar"]:
                        narx = format_narx(x["narx"] * kunlar)
                        kb.add(tb_types.InlineKeyboardButton(
                            f"{x['nomi']} | {x['sigim']} kishi | {narx} so'm",
                            callback_data=f"tb_xona_{x['id']}"))
                kb.add(tb_types.InlineKeyboardButton("Barcha bosh xonalar", callback_data="tb_barchasi"))
                matn_tb = f"Sana: {sana}-{tugash} | {kunlar} kun\nXonani tanlang:"
                bot.send_message(cid, matn_tb, reply_markup=kb)
                bot.answer_callback_query(call.id)
                return
        uid = call.from_user.id
        cid = call.message.chat.id
        kunlar = int(call.data.replace("kun_", ""))
        state = user_state.get(uid, {})
        state["kunlar"] = kunlar
        state["step"] = "xona_tanlash"
        user_state[uid] = state

        sana = state.get("sana", "")
        kishi = state.get("kishi", 1)
        guruh = state.get("guruh", "oila")
        tugash = tugash_sanasi(sana, kunlar)

        kombinatsiyalar = mos_kombinatsiya(kishi, guruh, sana, kunlar)

        if not kombinatsiyalar:
            bot.edit_message_text(
                t(uid, "xona_yoq").format(tel=TELEFON1),
                cid, call.message.message_id,
                reply_markup=sana_tugmalari())
            bot.answer_callback_query(call.id)
            return

        kom = kombinatsiyalar[0]
        xonalar = kom["xonalar"]
        jami_narx = sum(x["narx"] for x in xonalar) * kunlar
        xona_nomi = " + ".join(x["nomi"] for x in xonalar)
        jami_sigim = sum(x["sigim"] for x in xonalar)

        matn = f"Sana: {sana} - {tugash}\nKunlar: {kunlar}\nKishi: {kishi}\n\n{t(uid, 'mos_xona')}\n\n"

        for x in xonalar:
            qavat = "1-qavat" if x["qavat"] == 1 else "2-qavat"
            matn += f"Xona: {x['nomi']} | {qavat} | {x['sigim']} joy\nNarx: {format_narx(x['narx'] * kunlar)} som\n\n"

        if len(xonalar) > 1:
            matn += f"Jami: {format_narx(jami_narx)} som\n\n"

        # Ortiqcha kishi ogohlantirish
        if kom["tur"] == "bitta_ortiqcha":
            matn += t(uid, "ortiqcha_kishi").format(
                xona=xonalar[0]["nomi"],
                sigim=xonalar[0]["sigim"],
                kishi=kishi) + "\n\n"

        kb = types.InlineKeyboardMarkup(row_width=1)
        ids = "_".join(str(x["id"]) for x in xonalar)
        kb.add(types.InlineKeyboardButton(
            f"✅ {xona_nomi} — {format_narx(jami_narx)} so'm",
            callback_data=f"xona_tanla_{ids}_{sana}_{kunlar}"))
        kb.add(types.InlineKeyboardButton(
            t(uid, "barcha_bosh"),
            callback_data=f"barcha_{sana}_{kunlar}_{kishi}"))

        bot.edit_message_text(matn, cid, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("barcha_"))
    def cb_barcha(call):
        uid = call.from_user.id
        parts = call.data.split("_")
        sana, kunlar, kishi = parts[1], int(parts[2]), int(parts[3])
        kb = barcha_bosh_xonalar(sana, kunlar, kishi)
        bot.edit_message_text(
            f"Sana: {sana} | {kunlar} kun\n\nBarcha bosh xonalar:",
            call.message.chat.id, call.message.message_id,
            reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("xona_tanla_"))
    def cb_xona_tanla(call):
        uid = call.from_user.id
        cid = call.message.chat.id
        parts = call.data.split("_")
        kunlar = int(parts[-1])
        sana = parts[-2]
        xid_list = [int(x) for x in parts[2:-2]]

        with db() as conn:
            xonalar_info = [dict(conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()) for xid in xid_list]

        jami_narx = sum(x["narx"] for x in xonalar_info) * kunlar
        xona_nomi = " + ".join(x["nomi"] for x in xonalar_info)
        tugash = tugash_sanasi(sana, kunlar)
        jami_sigim = sum(x["sigim"] for x in xonalar_info)

        state = user_state.get(uid, {})
        kishi = state.get("kishi", 1)

        state.update({
            "xona_ids": xid_list,
            "sana": sana, "kunlar": kunlar,
            "xona_nomi": xona_nomi,
            "jami_narx": jami_narx,
            "tugash": tugash,
            "step": "ism"
        })
        user_state[uid] = state

        # Xona rasmlarini yuborish
        for xid in xid_list:
            with db() as conn:
                rasmlar = conn.execute(
                    "SELECT file_id FROM xona_media WHERE xona_id=? AND tur='photo' LIMIT 5",
                    (xid,)).fetchall()
                xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
            if rasmlar:
                try:
                    media = [types.InputMediaPhoto(rasmlar[0]["file_id"], caption=xnomi)]
                    for r in rasmlar[1:]:
                        media.append(types.InputMediaPhoto(r["file_id"]))
                    bot.send_media_group(cid, media)
                except:
                    pass

        # Ortiqcha kishi ogohlantirish
        if kishi > jami_sigim:
            ortiqcha = kishi - jami_sigim
            bot.send_message(cid,
                f"Eslatma: Tanlangan xonalarda jami {jami_sigim} joy bor, siz {kishi} kishisiz.\n"
                f"{ortiqcha} kishi uchun qo'shimcha joy topish kerak bo'ladi.")

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(t(uid, "bosh_menyu_btn"))
        bot.edit_message_text(
            f"Tanlandi: {xona_nomi}\nSana: {sana} - {tugash}\nKunlar: {kunlar}\nNarx: {format_narx(jami_narx)} som\n\n{t(uid, 'ism')}",
            cid, call.message.message_id)
        bot.send_message(cid, "👇", reply_markup=kb)
        bot.answer_callback_query(call.id)

    # ==================== TASDIQLASH ====================

    @bot.callback_query_handler(func=lambda c: c.data.startswith("mijoz_tasdiq_"))
    def cb_mijoz_tasdiq(call):
        uid = call.from_user.id
        cid = call.message.chat.id
        state = user_state.get(uid, {})

        if call.data == "mijoz_tasdiq_ha":
            try:
                bron_id = bron_id_gen()
                tugash = tugash_sanasi(state["sana"], state["kunlar"])

                with db() as conn:
                    conn.execute("""INSERT INTO bronlar
                        (id,ism,telefon,sana,kunlar,kishi,xona,narx,holat,user_id,username,created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (bron_id, state["ism"], state["telefon"], state["sana"],
                         state["kunlar"], state["kishi"], state["xona_nomi"],
                         state["jami_narx"], "kutilmoqda", uid,
                         call.from_user.username or "",
                         datetime.now().strftime("%d.%m.%Y %H:%M")))
                    for xid in state["xona_ids"]:
                        conn.execute("INSERT OR IGNORE INTO bron_xonalar VALUES (?,?)", (bron_id, xid))
                    conn.execute("""INSERT OR REPLACE INTO mijozlar
                        (user_id,ism,telefon,username,created_at,last_active)
                        VALUES (?,?,?,?,?,?)""",
                        (uid, state["ism"], state["telefon"],
                         call.from_user.username or "",
                         datetime.now().strftime("%d.%m.%Y %H:%M"),
                         datetime.now().strftime("%d.%m.%Y %H:%M")))
                    conn.commit()

                bot.edit_message_text(
                    t(uid, "bron_yuborildi").format(
                        bid=bron_id, xona=state["xona_nomi"],
                        sana=state["sana"], tugash=tugash,
                        kishi=state["kishi"],
                        narx=format_narx(state["jami_narx"]),
                        tel=TELEFON1),
                    cid, call.message.message_id)
                bot.send_message(cid, "👇", reply_markup=asosiy_menu(uid))

                # Adminlarga yuborish
                from texts import MATNLAR
                admin_kb = types.InlineKeyboardMarkup()
                admin_kb.add(
                    types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_tasdiq_ha_{bron_id}"),
                    types.InlineKeyboardButton("❌ Rad etish", callback_data=f"admin_tasdiq_yoq_{bron_id}"))
                admin_txt = (
                    f"YANGI BRON #{bron_id}\n\n"
                    f"Ism: {state['ism']}\nTel: {state['telefon']}\n"
                    f"Sana: {state['sana']} - {tugash}\nKunlar: {state['kunlar']}\n"
                    f"Kishi: {state['kishi']}\nXona: {state['xona_nomi']}\n"
                    f"Narx: {format_narx(state['jami_narx'])} som\n"
                    f"TG: @{call.from_user.username or 'yoq'}")
                for aid in [8886176055, 7323184602]:
                    try:
                        bot.send_message(aid, admin_txt, reply_markup=admin_kb)
                    except:
                        pass

                user_state.pop(uid, None)
                log_harakat(uid, "bron_yaratildi", bron_id)

            except Exception as e:
                logging.error(f"Bron xato: {e}")
                bot.send_message(cid, t(uid, "xato"))
        else:
            user_state.pop(uid, None)
            bot.edit_message_text(t(uid, "bekor_btn"), cid, call.message.message_id)
            bot.send_message(cid, "👇", reply_markup=asosiy_menu(uid))

        bot.answer_callback_query(call.id)

    # ==================== CONTACT ====================

    @bot.message_handler(content_types=["contact"])
    def contact_handler(msg):
        uid = msg.from_user.id
        state = user_state.get(uid, {})
        if state.get("step") == "telefon":
            tel = msg.contact.phone_number
            if not tel.startswith("+"):
                tel = "+" + tel
            state["telefon"] = tel
            user_state[uid] = state
            _tasdiqlash(bot, msg.chat.id, uid)

    # ==================== UMUMIY XABARLAR ====================

    @bot.message_handler(func=lambda m: True, content_types=["text"])
    def barcha(msg):
        uid = msg.from_user.id
        cid = msg.chat.id
        state = user_state.get(uid, {})
        step = state.get("step")
        text = msg.text or ""

        if step == "bosh_kishi":
            try:
                n = int(text)
                state["kishi"] = n
                state["guruh"] = "oila"
                state["step"] = "bosh_sana"
                user_state[uid] = state
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add(t(uid, "bosh_menyu_btn"))
                bot.send_message(cid, t(uid, "qaysi_sana"), reply_markup=kb)
                bot.send_message(cid, t(uid, "sana_tanlang"), reply_markup=sana_tugmalari())
            except:
                bot.send_message(cid, "Raqam kiriting")
            return

        if step == "kishi":
            try:
                n = int(text)
                if n < 1:
                    raise ValueError
                state["kishi"] = n
                state["step"] = "guruh"
                user_state[uid] = state
                til = get_til(uid) or "uz"
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
                kb.add(MATNLAR[til]["oila_btn"], MATNLAR[til]["dostlar_btn"],
                       MATNLAR[til]["bosh_menyu_btn"])
                bot.send_message(cid, t(uid, "kimlar"), reply_markup=kb)
            except:
                bot.send_message(cid, "Raqam kiriting")
            return

        if step == "guruh":
            til = get_til(uid) or "uz"
            g = "oila" if text == MATNLAR[til]["oila_btn"] else "dost"
            state["guruh"] = g
            state["step"] = "sana"
            user_state[uid] = state
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(t(uid, "bosh_menyu_btn"))
            bot.send_message(cid, t(uid, "qaysi_sana"), reply_markup=kb)
            bot.send_message(cid, t(uid, "sana_tanlang"), reply_markup=sana_tugmalari())
            return

        if step == "ism":
            state["ism"] = text.strip()
            state["step"] = "telefon"
            user_state[uid] = state
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton(t(uid, "kontakt_btn"), request_contact=True))
            kb.add(t(uid, "bosh_menyu_btn"))
            bot.send_message(cid, t(uid, "telefon"), reply_markup=kb)
            return

        if step == "telefon":
            state["telefon"] = text.strip()
            user_state[uid] = state
            _tasdiqlash(bot, cid, uid)
            return

        # AI javob
        if not step and not text.startswith("/"):
            til = get_til(uid) or "uz"
            log_harakat(uid, "savol", text[:100])
            from handlers.ai import ai_javob
            javob = ai_javob(text, til)
            if javob:
                if any(x in text.lower() for x in ["bron", "joy", "xona", "room", "номер"]):
                    kb = types.InlineKeyboardMarkup()
                    kb.add(types.InlineKeyboardButton(t(uid, "bron_btn"), callback_data="bron_start_cb"))
                    bot.send_message(cid, javob, reply_markup=kb)
                else:
                    bot.send_message(cid, javob)
            else:
                bot.send_message(cid, f"{TELEFON1}\n{TELEFON2}")


def _tasdiqlash(bot, cid, uid):
    state = user_state.get(uid, {})
    tugash = tugash_sanasi(state["sana"], state["kunlar"])
    matn = (
        f"Bron malumotlari:\n\n"
        f"Ism: {state['ism']}\nTel: {state['telefon']}\n"
        f"Sana: {state['sana']} - {tugash}\nKunlar: {state['kunlar']}\n"
        f"Kishi: {state['kishi']}\nXona: {state['xona_nomi']}\n"
        f"Narx: {format_narx(state['jami_narx'])} som\n\n"
        f"{t(uid, 'tasdiq_btn')}?"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(t(uid, "tasdiq_btn"), callback_data="mijoz_tasdiq_ha"),
        types.InlineKeyboardButton(t(uid, "bekor_btn"), callback_data="mijoz_tasdiq_yoq"))
    bot.send_message(cid, matn, reply_markup=kb)
    state["step"] = "tasdiq"
    user_state[uid] = state
