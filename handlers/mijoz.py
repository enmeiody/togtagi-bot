from telebot import types
from db import (get_til, set_til, saqlash_mijoz, format_narx, tugash_sanasi,
                bron_id_gen, get_bron, get_bron_xonalar, bekor_qil_bron,
                band_qil, mos_kombinatsiya, is_admin, get_db, log_stat, xona_kunlar_band)
from config import txt, M, TELEFON1, TELEFON2, INSTAGRAM, DIRECTOR_IDS
from keyboards import asosiy_kb, til_kb, sana_kb, kunlar_kb, xonalar_kb
from datetime import datetime

# Mijoz holati
state = {}


def register(bot):

    # ===== START =====

    @bot.message_handler(commands=["start"])
    def cmd_start(msg):
        uid = msg.from_user.id
        saqlash_mijoz(uid, msg.from_user.first_name, msg.from_user.username)
        log_stat(uid, "start")
        state.pop(uid, None)

        # Bron havola
        if msg.text and "bron_" in msg.text:
            bid = msg.text.split("bron_")[-1].strip().upper()
            b = get_bron(bid)
            if b:
                tugash = tugash_sanasi(b["sana"], b["kunlar"])
                bot.send_message(uid,
                    f"Bron malumotlari:\n\nID: #{b['id']}\nXona: {b['xona']}\n"
                    f"Sana: {b['sana']} - {tugash}\nKishi: {b['kishi']}\n"
                    f"Narx: {format_narx(b['narx'])} som\n\n{TELEFON1}",
                    reply_markup=asosiy_kb(uid))
                conn = get_db()
                conn.execute("UPDATE mijozlar SET user_id=? WHERE telefon=?", (uid, b["telefon"]))
                conn.execute("UPDATE bronlar SET user_id=? WHERE id=?", (uid, bid))
                conn.commit()
                conn.close()
            else:
                bot.send_message(uid, f"Bron #{bid} topilmadi. {TELEFON1}")
            return

        bot.send_message(uid, "Tilni tanlang / Выберите язык:", reply_markup=til_kb())

    # ===== TIL =====

    @bot.callback_query_handler(func=lambda c: c.data.startswith("til_"))
    def cb_til(call):
        uid = call.from_user.id
        til = call.data.replace("til_", "")
        set_til(uid, til)
        state.pop(uid, None)
        try:
            bot.edit_message_text("✅", call.message.chat.id, call.message.message_id)
        except:
            pass
        # Greeting
        conn = get_db()
        gr = conn.execute("SELECT * FROM greeting_media").fetchone()
        conn.close()
        matn = txt(uid, "xush_kelibsiz")
        if gr:
            try:
                bot.send_photo(uid, gr["file_id"], caption=matn, reply_markup=asosiy_kb(uid))
                bot.answer_callback_query(call.id)
                return
            except:
                pass
        bot.send_message(uid, matn, reply_markup=asosiy_kb(uid))
        bot.answer_callback_query(call.id)

    # ===== ASOSIY TUGMALAR =====

    @bot.message_handler(func=lambda m: m.text and _is_btn(m, "bron"))
    def h_bron(msg):
        uid = msg.from_user.id
        conn = get_db()
        blok = conn.execute("SELECT bloklangan FROM mijozlar WHERE user_id=?", (uid,)).fetchone()
        conn.close()
        if blok and blok["bloklangan"]:
            bot.send_message(uid, f"Boglanish: {TELEFON1}")
            return
        state[uid] = {"step": "kishi"}
        log_stat(uid, "bron")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
        for i in range(1, 11):
            kb.add(str(i))
        kb.add(txt(uid, "bosh_menu"))
        bot.send_message(uid, txt(uid, "necha_kishi"), reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text and _is_btn(m, "bosh_x"))
    def h_bosh_x(msg):
        uid = msg.from_user.id
        state[uid] = {"step": "bosh_kishi"}
        log_stat(uid, "bosh_xonalar")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
        for i in range(1, 11):
            kb.add(str(i))
        kb.add(txt(uid, "bosh_menu"))
        bot.send_message(uid, txt(uid, "necha_kishi"), reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text and _is_btn(m, "galereya"))
    def h_galereya(msg):
        uid = msg.from_user.id
        log_stat(uid, "galereya")
        conn = get_db()
        photos = conn.execute("SELECT file_id FROM umumiy_media WHERE tur='photo' ORDER BY id").fetchall()
        videos = conn.execute("SELECT file_id FROM umumiy_media WHERE tur='video' ORDER BY id LIMIT 3").fetchall()
        conn.close()
        if not photos and not videos:
            bot.send_message(uid, txt(uid, "galereya_yoq"))
            return
        if photos:
            try:
                media = [types.InputMediaPhoto(photos[0]["file_id"], caption="Tog' Tagi Resort")]
                for p in photos[1:10]:
                    media.append(types.InputMediaPhoto(p["file_id"]))
                bot.send_media_group(uid, media)
            except:
                pass
        for v in videos:
            try:
                bot.send_video(uid, v["file_id"])
            except:
                pass

    @bot.message_handler(func=lambda m: m.text and _is_btn(m, "xizmatlar"))
    def h_xizmatlar(msg):
        log_stat(msg.from_user.id, "xizmatlar")
        bot.send_message(msg.from_user.id, txt(msg.from_user.id, "xizm_matn"))

    @bot.message_handler(func=lambda m: m.text and _is_btn(m, "manzil"))
    def h_manzil(msg):
        uid = msg.from_user.id
        log_stat(uid, "manzil")
        bot.send_message(uid, txt(uid, "manzil_matn"))
        bot.send_location(uid, latitude=39.961311, longitude=71.836921)

    @bot.message_handler(func=lambda m: m.text and _is_btn(m, "boglanish"))
    def h_boglanish(msg):
        uid = msg.from_user.id
        log_stat(uid, "boglanish")
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton(f"📞 {TELEFON1}", url=f"tel:{TELEFON1}"),
            types.InlineKeyboardButton(f"📞 {TELEFON2}", url=f"tel:{TELEFON2}"),
            types.InlineKeyboardButton("📸 Instagram", url=INSTAGRAM),
            types.InlineKeyboardButton(txt(uid, "bron"), callback_data="CB_BRON"),
        )
        bot.send_message(uid, txt(uid, "boglanish_matn"), reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text and _is_btn(m, "bronlarim"))
    def h_bronlarim(msg):
        uid = msg.from_user.id
        log_stat(uid, "bronlarim")
        conn = get_db()
        bronlar = conn.execute(
            "SELECT * FROM bronlar WHERE user_id=? AND holat != 'bekor' ORDER BY sana DESC LIMIT 10",
            (uid,)).fetchall()
        conn.close()
        if not bronlar:
            bot.send_message(uid, txt(uid, "bronlarim_yoq"))
            return
        for b in bronlar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            emoji = {"kutilmoqda": "⏳", "tasdiqlangan": "✅"}.get(b["holat"], "❓")
            matn = (f"{emoji} #{b['id']}\nXona: {b['xona']}\n"
                    f"Sana: {b['sana']} - {tugash}\n"
                    f"Kishi: {b['kishi']} | Narx: {format_narx(b['narx'])} som")
            kb = types.InlineKeyboardMarkup()
            if b["holat"] in ["kutilmoqda", "tasdiqlangan"]:
                kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data=f"MBEKOR_{b['id']}"))
            bot.send_message(uid, matn, reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text and _is_btn(m, "bosh_menu"))
    def h_bosh_menu(msg):
        uid = msg.from_user.id
        state.pop(uid, None)
        bot.send_message(uid, "👇", reply_markup=asosiy_kb(uid))

    @bot.message_handler(func=lambda m: m.text == "🌐 Ijtimoiy tarmoqlar")
    def h_ijtimoiy(msg):
        uid = msg.from_user.id
        from keyboards import ijtimoiy_kb
        kb = ijtimoiy_kb()
        if not kb.keyboard:
            bot.send_message(uid, "Hozircha ijtimoiy tarmoqlar yoq.")
        else:
            bot.send_message(uid, "🌐 Ijtimoiy tarmoqlar:", reply_markup=kb)

    # ===== CALLBACKS =====

    @bot.callback_query_handler(func=lambda c: c.data == "CB_BRON")
    def cb_bron(call):
        uid = call.from_user.id
        state[uid] = {"step": "kishi"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
        for i in range(1, 11):
            kb.add(str(i))
        kb.add(txt(uid, "bosh_menu"))
        bot.send_message(uid, txt(uid, "necha_kishi"), reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("MBEKOR_"))
    def cb_mbekor(call):
        uid = call.from_user.id
        bid = call.data.replace("MBEKOR_", "")
        b = get_bron(bid)
        if not b or b["user_id"] != uid:
            bot.answer_callback_query(call.id, "Topilmadi")
            return
        bekor_qil_bron(bid)
        bot.edit_message_text(txt(uid, "bron_bekor").format(bid=bid),
                              call.message.chat.id, call.message.message_id)
        for aid in DIRECTOR_IDS:
            try:
                bot.send_message(aid, f"Bron #{bid} BEKOR QILINDI (mijoz)\n{b['ism']} | {b['telefon']}")
            except:
                pass
        bot.answer_callback_query(call.id)

    # ===== SANA & KUN CALLBACKS =====

    @bot.callback_query_handler(func=lambda c: c.data.startswith("S_"))
    def cb_sana(call):
        uid = call.from_user.id
        cid = call.message.chat.id
        sana = call.data.replace("S_", "")

        # Admin step tekshirish
        from handlers.astate import astate
        if is_admin(uid) and uid in astate:
            st = astate[uid].get("step")
            if st == "band_sana":
                astate[uid]["sana"] = sana
                astate[uid]["step"] = "band_kun"
                bot.send_message(cid, f"Sana: {sana}\nNecha kun?", reply_markup=kunlar_kb())
                bot.answer_callback_query(call.id)
                return
            elif st == "bosh_sana":
                astate[uid]["sana"] = sana
                astate[uid]["step"] = "bosh_kun"
                bot.send_message(cid, f"Sana: {sana}\nNecha kun?", reply_markup=kunlar_kb())
                bot.answer_callback_query(call.id)
                return
            elif st == "tb_sana":
                astate[uid]["ab"]["sana"] = sana
                astate[uid]["step"] = "tb_kun"
                bot.send_message(cid, f"Sana: {sana}\nNecha kun?", reply_markup=kunlar_kb())
                bot.answer_callback_query(call.id)
                return
            elif st == "joyla_sana":
                astate[uid]["joyla_sana"] = sana
                astate[uid]["step"] = "joyla_kun"
                bot.send_message(cid, f"Sana: {sana}\nNecha kun turadi?", reply_markup=kunlar_kb())
                bot.answer_callback_query(call.id)
                return
            elif st == "ozg_sana":
                bid = astate[uid]["bron_id"]
                conn = get_db()
                conn.execute("UPDATE bronlar SET sana=? WHERE id=?", (sana, bid))
                conn.commit()
                conn.close()
                astate.pop(uid, None)
                from keyboards import admin_kb
                bot.send_message(cid, f"✅ Sana {sana} ga o'zgartirildi!", reply_markup=admin_kb(uid))
                bot.answer_callback_query(call.id)
                return

        # Mijoz
        st = state.get(uid, {})
        if st.get("step") not in ["sana", "bosh_sana"]:
            bot.answer_callback_query(call.id)
            return
        state[uid]["sana"] = sana
        state[uid]["step"] = "kun"
        try:
            bot.edit_message_text(f"Sana: {sana}\n\n{txt(uid, 'necha_kun')}",
                                  cid, call.message.message_id, reply_markup=kunlar_kb())
        except:
            bot.send_message(cid, txt(uid, "necha_kun"), reply_markup=kunlar_kb())
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("K_"))
    def cb_kun(call):
        uid = call.from_user.id
        cid = call.message.chat.id
        kunlar = int(call.data.replace("K_", ""))

        # Admin step
        from handlers.astate import astate
        if is_admin(uid) and uid in astate:
            from db import band_qil, bosh_qil_sana, get_db as gdb
            st = astate[uid].get("step")
            if st == "band_kun":
                xid = astate[uid]["xid"]
                sana = astate[uid]["sana"]
                band_qil(xid, sana, kunlar, "admin")
                conn = gdb()
                xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
                conn.close()
                astate.pop(uid, None)
                from keyboards import admin_kb
                bot.send_message(cid, f"{xnomi} - {sana} dan {kunlar} kun BAND", reply_markup=admin_kb(uid))
                bot.answer_callback_query(call.id)
                return
            elif st == "bosh_kun":
                xid = astate[uid]["xid"]
                sana = astate[uid]["sana"]
                bosh_qil_sana(xid, sana, kunlar)
                conn = gdb()
                xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
                conn.close()
                astate.pop(uid, None)
                from keyboards import admin_kb
                bot.send_message(cid, f"{xnomi} - {sana} dan {kunlar} kun BOSH", reply_markup=admin_kb(uid))
                bot.answer_callback_query(call.id)
                return
            elif st == "tb_kun":
                astate[uid]["ab"]["kunlar"] = kunlar
                sana = astate[uid]["ab"]["sana"]
                kishi = astate[uid]["ab"].get("kishi", 1)
                kombinatsiyalar = mos_kombinatsiya(kishi, "oila", sana, kunlar)
                tugash = tugash_sanasi(sana, kunlar)
                kb = types.InlineKeyboardMarkup(row_width=1)
                if kombinatsiyalar:
                    for x in kombinatsiyalar[0]["xonalar"]:
                        narx = format_narx(x["narx"] * kunlar)
                        kb.add(types.InlineKeyboardButton(
                            f"{x['nomi']} | {x['sigim']}👤 | {narx}",
                            callback_data=f"TBXT_{x['id']}"))
                kb.add(types.InlineKeyboardButton("Barcha bosh xonalar", callback_data="TB_BARCHASI"))
                astate[uid]["step"] = "tb_xona"
                bot.send_message(cid, f"Sana: {sana}-{tugash} | {kunlar} kun\nXona:", reply_markup=kb)
                bot.answer_callback_query(call.id)
                return

        # Mijoz
        st = state.get(uid, {})
        if st.get("step") not in ["kun", "bosh_kun"]:
            bot.answer_callback_query(call.id)
            return

        sana = st.get("sana", "")
        kishi = st.get("kishi", 1)
        guruh = st.get("guruh", "oila")
        tugash = tugash_sanasi(sana, kunlar)
        state[uid]["kunlar"] = kunlar

        if st.get("step") == "bosh_kun":
            # Bo'sh xonalar ko'rsatish
            matn = f"Sana: {sana} - {tugash} | {kunlar} kun\nKishi: {kishi}\n\nBosh xonalar:"
            kb = xonalar_kb(sana, kunlar, kishi)
            try:
                bot.edit_message_text(matn, cid, call.message.message_id, reply_markup=kb)
            except:
                bot.send_message(cid, matn, reply_markup=kb)
            bot.answer_callback_query(call.id)
            return

        # Barcha variantlarni ko'rsat
        from db import barcha_variantlar
        variantlar = barcha_variantlar(kishi, guruh, sana, kunlar)
        
        if not variantlar:
            try:
                bot.edit_message_text(txt(uid, "xona_yoq"), cid, call.message.message_id, reply_markup=sana_kb())
            except:
                bot.send_message(cid, txt(uid, "xona_yoq"), reply_markup=sana_kb())
            bot.answer_callback_query(call.id)
            return

        matn = f"📅 {sana} - {tugash} | {kunlar} kun | 👥 {kishi} kishi\n\n"
        matn += "Xona variantlari:\n\n"
        
        kb = types.InlineKeyboardMarkup(row_width=1)
        
        tur_emoji = {
            "bitta": "✅",
            "ortiqcha_1": "⚠️",
            "kombinatsiya": "🔢",
            "kombinatsiya_2": "🔄"
        }
        tur_izoh = {
            "bitta": "",
            "ortiqcha_1": " (1 kishi ko'p yotadi)",
            "kombinatsiya": " (bir necha xona)",
            "kombinatsiya_2": " (aralash qavat)"
        }
        
        for v in variantlar:
            xonalar = v["xonalar"]
            jami_narx = sum(x["narx"] for x in xonalar) * kunlar
            xona_nomi = " + ".join(x["nomi"] for x in xonalar)
            jami_sigim = v["jami_sigim"]
            emoji = tur_emoji.get(v["tur"], "🔹")
            izoh = tur_izoh.get(v["tur"], "")
            narx_str = format_narx(jami_narx)
            
            matn += f"{emoji} {xona_nomi} — {jami_sigim}👤 — {narx_str} som{izoh}\n"
            
            ids = "_".join(str(x["id"]) for x in xonalar)
            kb.add(types.InlineKeyboardButton(
                f"{emoji} {xona_nomi} — {narx_str}",
                callback_data=f"XT_{ids}_{sana}_{kunlar}"))

        kb.add(types.InlineKeyboardButton("📋 Barcha bosh xonalar", callback_data=f"BARCHAX_{sana}_{kunlar}_{kishi}"))

        try:
            bot.edit_message_text(matn, cid, call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(cid, matn, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("BARCHAX_"))
    def cb_barchax(call):
        uid = call.from_user.id
        parts = call.data.split("_")
        sana, kunlar, kishi = parts[1], int(parts[2]), int(parts[3])
        kb = xonalar_kb(sana, kunlar, kishi)
        try:
            bot.edit_message_text(f"Sana: {sana} | {kunlar} kun\n\nBosh xonalar:",
                                  call.message.chat.id, call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, "Bosh xonalar:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("XT_"))
    def cb_xt(call):
        uid = call.from_user.id
        cid = call.message.chat.id
        parts = call.data.split("_")
        kunlar = int(parts[-1])
        sana = parts[-2]
        xid_list = [int(x) for x in parts[1:-2]]

        conn = get_db()
        xonalar_info = []
        for xid in xid_list:
            x = conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()
            if x:
                xonalar_info.append(dict(x))
        conn.close()

        if not xonalar_info:
            bot.answer_callback_query(call.id, "Xona topilmadi")
            return

        jami_narx = sum(x["narx"] for x in xonalar_info) * kunlar
        xona_nomi = " + ".join(x["nomi"] for x in xonalar_info)
        tugash = tugash_sanasi(sana, kunlar)
        kishi = state.get(uid, {}).get("kishi", 1)
        jami_sigim = sum(x["sigim"] for x in xonalar_info)

        state[uid] = {
            **state.get(uid, {}),
            "xona_ids": xid_list, "sana": sana, "kunlar": kunlar,
            "xona_nomi": xona_nomi, "jami_narx": jami_narx,
            "tugash": tugash, "step": "ism"
        }

        # Xona rasmlari
        for xid in xid_list:
            conn = get_db()
            rasmlar = conn.execute("SELECT file_id FROM xona_media WHERE xona_id=? AND tur='photo' LIMIT 5", (xid,)).fetchall()
            xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
            conn.close()
            if rasmlar:
                try:
                    media = [types.InputMediaPhoto(rasmlar[0]["file_id"], caption=xnomi)]
                    for r in rasmlar[1:]:
                        media.append(types.InputMediaPhoto(r["file_id"]))
                    bot.send_media_group(cid, media)
                except:
                    pass

        if kishi > jami_sigim:
            bot.send_message(cid, f"Eslatma: {jami_sigim} joy bor, siz {kishi} kishisiz. {kishi-jami_sigim} kishi qoshimcha joy kerak.")

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(txt(uid, "bosh_menu"))
        try:
            bot.edit_message_text(
                f"Tanlandi: {xona_nomi}\nSana: {sana}-{tugash} | {kunlar} kun\nNarx: {format_narx(jami_narx)} som\n\n{txt(uid, 'ism_kirit')}",
                cid, call.message.message_id)
        except:
            pass
        bot.send_message(cid, txt(uid, "ism_kirit"), reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("MTASDIQ_"))
    def cb_mtasdiq(call):
        uid = call.from_user.id
        cid = call.message.chat.id
        action = call.data.replace("MTASDIQ_", "")
        st = state.get(uid, {})

        if action == "ha":
            try:
                bid = bron_id_gen()
                tugash = tugash_sanasi(st["sana"], st["kunlar"])
                conn = get_db()
                conn.execute("""INSERT INTO bronlar
                    (id,ism,telefon,sana,kunlar,kishi,xona,narx,holat,user_id,username,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (bid, st["ism"], st["telefon"], st["sana"], st["kunlar"],
                     st["kishi"], st["xona_nomi"], st["jami_narx"], "kutilmoqda",
                     uid, call.from_user.username or "",
                     datetime.now().strftime("%d.%m.%Y %H:%M")))
                for xid in st["xona_ids"]:
                    conn.execute("INSERT OR IGNORE INTO bron_xonalar VALUES (?,?)", (bid, xid))
                try:
                    conn.execute("""INSERT OR REPLACE INTO mijozlar
                        (user_id,ism,telefon,username,last_active)
                        VALUES (?,?,?,?,?)""",
                        (uid, st["ism"], st["telefon"],
                         call.from_user.username or "",
                         datetime.now().strftime("%d.%m.%Y %H:%M")))
                except:
                    pass
                conn.commit()
                conn.close()

                try:
                    bot.edit_message_text(
                        txt(uid, "bron_yuborildi").format(
                            bid=bid, xona=st["xona_nomi"], sana=st["sana"],
                            tugash=tugash, kishi=st["kishi"],
                            narx=format_narx(st["jami_narx"])),
                        cid, call.message.message_id)
                except:
                    pass
                bot.send_message(cid, "👇", reply_markup=asosiy_kb(uid))

                # Adminlarga
                kb_a = types.InlineKeyboardMarkup()
                kb_a.add(
                    types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ATASDIQ_ha_{bid}"),
                    types.InlineKeyboardButton("❌ Rad etish", callback_data=f"ATASDIQ_yoq_{bid}"))
                atxt = (f"YANGI BRON #{bid}\n\n{st['ism']} | {st['telefon']}\n"
                        f"Sana: {st['sana']}-{tugash} | {st['kunlar']} kun\n"
                        f"Kishi: {st['kishi']} | Xona: {st['xona_nomi']}\n"
                        f"Narx: {format_narx(st['jami_narx'])} som\n"
                        f"TG: @{call.from_user.username or 'yoq'}")
                for aid in DIRECTOR_IDS:
                    try:
                        bot.send_message(aid, atxt, reply_markup=kb_a)
                    except:
                        pass
                state.pop(uid, None)
            except Exception as e:
                import logging
                logging.error(f"Bron xato: {e}")
                bot.send_message(cid, txt(uid, "xato"))
        else:
            state.pop(uid, None)
            try:
                bot.edit_message_text(txt(uid, "bekor"), cid, call.message.message_id)
            except:
                pass
            bot.send_message(cid, "👇", reply_markup=asosiy_kb(uid))
        bot.answer_callback_query(call.id)

    # ===== CONTACT =====

    @bot.message_handler(content_types=["contact"])
    def h_contact(msg):
        uid = msg.from_user.id
        st = state.get(uid, {})
        if st.get("step") == "telefon":
            tel = msg.contact.phone_number
            if not tel.startswith("+"):
                tel = "+" + tel
            state[uid]["telefon"] = tel
            _tasdiq(bot, msg.chat.id, uid)

    # ===== MATN XABARLAR =====

    @bot.message_handler(func=lambda m: True, content_types=["text"])
    def h_matn(msg):
        uid = msg.from_user.id
        text = msg.text or ""

        # Admin tugmalarini o'tkazib yuborish
        ADMIN_BTNLAR = [
            "🏨 Xonalar", "📋 Bronlar", "📊 Bugungi holat", "👥 Mehmonlar",
            "📅 10 kunlik", "👤 Mijoz qidirish", "➕ Tezkor bron", "📸 Galereya",
            "📄 Hisobot", "🤖 AI malumot", "🔙 Asosiy menyu", "👮 Adminlar",
            "📊 Statistika", "🔙 Admin menyu", "🏠 Xonaga joylash",
            "🔗 Ijtimoiy tarmoqlar sozlash"
        ]
        if is_admin(uid) and text in ADMIN_BTNLAR:
            return

        if text.startswith("/"):
            return

        st = state.get(uid, {})
        step = st.get("step")

        if step == "bosh_kishi":
            try:
                n = int(text)
                state[uid]["kishi"] = n
                state[uid]["guruh"] = "oila"
                state[uid]["step"] = "bosh_sana"
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add(txt(uid, "bosh_menu"))
                bot.send_message(msg.chat.id, txt(uid, "qaysi_sana"), reply_markup=kb)
                bot.send_message(msg.chat.id, "30 kun:", reply_markup=sana_kb())
            except:
                bot.send_message(msg.chat.id, "Raqam kiriting")
            return

        if step == "kishi":
            try:
                n = int(text)
                if n < 1:
                    raise ValueError
                state[uid]["kishi"] = n
                state[uid]["step"] = "guruh"
                til = get_til(uid) or "uz"
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
                kb.add(M[til]["oila"], M[til]["dostlar"], M[til]["bosh_menu"])
                bot.send_message(msg.chat.id, txt(uid, "kimlar"), reply_markup=kb)
            except:
                bot.send_message(msg.chat.id, "Raqam kiriting")
            return

        if step == "guruh":
            til = get_til(uid) or "uz"
            g = "oila" if text == M[til]["oila"] else "dost"
            state[uid]["guruh"] = g
            state[uid]["step"] = "sana"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(txt(uid, "bosh_menu"))
            bot.send_message(msg.chat.id, txt(uid, "qaysi_sana"), reply_markup=kb)
            bot.send_message(msg.chat.id, "30 kun:", reply_markup=sana_kb())
            return

        if step == "ism":
            state[uid]["ism"] = text.strip()
            state[uid]["step"] = "telefon"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton(txt(uid, "kontakt"), request_contact=True))
            kb.add(txt(uid, "bosh_menu"))
            bot.send_message(msg.chat.id, txt(uid, "tel_yuvor"), reply_markup=kb)
            return

        if step == "telefon":
            state[uid]["telefon"] = text.strip()
            _tasdiq(bot, msg.chat.id, uid)
            return

        # Admin state tekshirish
        if is_admin(uid):
            from handlers.astate import astate
            if uid in astate and astate[uid].get("step"):
                _admin_matn(bot, msg, uid, text)
                return

        # AI javob
        if not step:
            from handlers.ai_handler import ai_javob
            log_stat(uid, f"savol:{text[:50]}")
            til = get_til(uid) or "uz"
            javob = ai_javob(text, til)
            if javob:
                if any(x in text.lower() for x in ["bron", "joy", "xona", "room", "номер"]):
                    kb = types.InlineKeyboardMarkup()
                    kb.add(types.InlineKeyboardButton(txt(uid, "bron"), callback_data="CB_BRON"))
                    bot.send_message(msg.chat.id, javob, reply_markup=kb)
                else:
                    bot.send_message(msg.chat.id, javob)
            else:
                bot.send_message(msg.chat.id, f"{TELEFON1}\n{TELEFON2}")


def _is_btn(msg, kalit):
    uid = msg.from_user.id
    til = get_til(uid) or "uz"
    return msg.text == M[til].get(kalit, "")


def _tasdiq(bot, cid, uid):
    st = state.get(uid, {})
    tugash = tugash_sanasi(st["sana"], st["kunlar"])
    matn = (f"Bron malumotlari:\n\n"
            f"Ism: {st['ism']}\nTel: {st['telefon']}\n"
            f"Sana: {st['sana']} - {tugash} | {st['kunlar']} kun\n"
            f"Kishi: {st['kishi']}\nXona: {st['xona_nomi']}\n"
            f"Narx: {format_narx(st['jami_narx'])} som\n\n"
            f"{txt(uid, 'tasdiq')}")
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(txt(uid, "ha"), callback_data="MTASDIQ_ha"),
        types.InlineKeyboardButton(txt(uid, "bekor"), callback_data="MTASDIQ_yoq"))
    bot.send_message(cid, matn, reply_markup=kb)
    state[uid]["step"] = "tasdiq"


def _admin_matn(bot, msg, uid, text):
    from handlers.astate import astate
    from handlers.admin_h import admin_matn_handler
    admin_matn_handler(bot, msg, uid, text, astate)
