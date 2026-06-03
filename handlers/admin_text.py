import logging
from datetime import datetime
from telebot import types
from db_module import (db, get_xonalar, format_narx, is_admin, is_director,
                      band_qil, bosh_qil_sana, bekor_qil_bron, get_bron, qidir_mijoz)
from texts import TELEFON1
from utils import bron_id_gen, tugash_sanasi, sana_tugmalari, kunlar_tugmalari

DIRECTOR_IDS = [8886176055, 7323184602]


def register(bot):

    @bot.message_handler(commands=["done"])
    def cmd_done(msg):
        if not is_admin(msg.from_user.id): return
        from handlers.admin_state import admin_state
        state = admin_state.get(msg.from_user.id, {})
        xid = state.get("rasm_xona_id") or state.get("video_xona_id")
        admin_state.pop(msg.from_user.id, None)
        from handlers.admin import admin_menu
        bot.send_message(msg.chat.id, "Saqlandi!", reply_markup=admin_menu(msg.from_user.id))

    @bot.message_handler(content_types=["photo"])
    def photo_handler(msg):
        if not is_admin(msg.from_user.id): return
        from handlers.admin_state import admin_state
        state = admin_state.get(msg.from_user.id, {})
        step = state.get("step")
        file_id = msg.photo[-1].file_id
        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        with db() as conn:
            if step == "xona_rasm":
                xid = state["rasm_xona_id"]
                conn.execute("INSERT INTO xona_media (xona_id,tur,file_id,created_at) VALUES (?,?,?,?)",
                            (xid, "photo", file_id, now))
                cnt = conn.execute("SELECT COUNT(*) as c FROM xona_media WHERE xona_id=? AND tur='photo'", (xid,)).fetchone()["c"]
                conn.commit()
                bot.send_message(msg.chat.id, f"Saqlandi! Jami: {cnt} ta\n/done - tugallash")

            elif step == "umumiy_rasm":
                conn.execute("INSERT INTO umumiy_media (tur,file_id,created_at) VALUES (?,?,?)",
                            ("photo", file_id, now))
                cnt = conn.execute("SELECT COUNT(*) as c FROM umumiy_media WHERE tur='photo'").fetchone()["c"]
                conn.commit()
                bot.send_message(msg.chat.id, f"Saqlandi! Jami: {cnt} ta\n/done - tugallash")

            elif step == "greeting_rasm":
                conn.execute("DELETE FROM greeting_media")
                conn.execute("INSERT INTO greeting_media (id,file_id,tur) VALUES (1,?,?)",
                            (file_id, "photo"))
                conn.commit()
                admin_state.pop(msg.from_user.id, None)
                from handlers.admin import admin_menu
                bot.send_message(msg.chat.id, "Greeting rasmi saqlandi!", reply_markup=admin_menu(msg.from_user.id))

    @bot.message_handler(content_types=["video"])
    def video_handler(msg):
        if not is_admin(msg.from_user.id): return
        from handlers.admin_state import admin_state
        state = admin_state.get(msg.from_user.id, {})
        step = state.get("step")
        file_id = msg.video.file_id
        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        with db() as conn:
            if step == "xona_video":
                xid = state["video_xona_id"]
                conn.execute("INSERT INTO xona_media (xona_id,tur,file_id,created_at) VALUES (?,?,?,?)",
                            (xid, "video", file_id, now))
                cnt = conn.execute("SELECT COUNT(*) as c FROM xona_media WHERE xona_id=? AND tur='video'", (xid,)).fetchone()["c"]
                conn.commit()
                bot.send_message(msg.chat.id, f"Video saqlandi! Jami: {cnt} ta\n/done - tugallash")

            elif step == "umumiy_video":
                conn.execute("INSERT INTO umumiy_media (tur,file_id,created_at) VALUES (?,?,?)",
                            ("video", file_id, now))
                cnt = conn.execute("SELECT COUNT(*) as c FROM umumiy_media WHERE tur='video'").fetchone()["c"]
                conn.commit()
                bot.send_message(msg.chat.id, f"Video saqlandi! Jami: {cnt} ta\n/done - tugallash")

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text and not m.text.startswith("/"), content_types=["text"])
    def admin_text_handler(msg):
        if not is_admin(msg.from_user.id): return
        from handlers.admin_state import admin_state
        from handlers.admin import admin_menu
        state = admin_state.get(msg.from_user.id, {})
        step = state.get("step")
        # Agar admin_state da step bo'lmasa - mijoz handleriga o'tkazish
        if not step: return
        text = msg.text.strip()
        cid = msg.chat.id
        uid = msg.from_user.id

        # ==================== SANA CALLBACK ====================
        # Bu yerda admin uchun sana tanlash callback lari ham ishlanadi

        if step == "ax_band_sana":
            state["ax_sana"] = text
            state["step"] = "ax_band_kunlar"
            admin_state[uid] = state
            bot.send_message(cid, f"Sana: {text}\nNecha kun band?", reply_markup=kunlar_tugmalari())
            return

        if step == "ax_bosh_sana":
            state["ax_sana"] = text
            state["step"] = "ax_bosh_kunlar"
            admin_state[uid] = state
            bot.send_message(cid, f"Sana: {text}\nNecha kun bosh?", reply_markup=kunlar_tugmalari())
            return

        if step == "narx_ozgartir":
            try:
                narx = int(text.replace(" ", "").replace(",", ""))
                xid = state["narx_xid"]
                with db() as conn:
                    conn.execute("UPDATE xonalar SET narx=? WHERE id=?", (narx, xid))
                    conn.commit()
                admin_state.pop(uid, None)
                bot.send_message(cid, f"Narx {format_narx(narx)} som ga o'zgartirildi!", reply_markup=admin_menu(uid))
            except:
                bot.send_message(cid, "Faqat raqam kiriting (masalan: 350000)")
            return

        if step == "yangi_bino_nomi":
            with db() as conn:
                conn.execute("INSERT INTO binolar (nomi) VALUES (?)", (text,))
                conn.commit()
            admin_state.pop(uid, None)
            bot.send_message(cid, f"Yangi bino '{text}' yaratildi!", reply_markup=admin_menu(uid))
            return

        if step == "yangi_xona_nomi":
            try:
                parts = text.split(",")
                nomi = parts[0].strip()
                qavat = int(parts[1].strip())
                sigim = int(parts[2].strip())
                narx = int(parts[3].strip())
                bino_id = state["bino_id"]
                with db() as conn:
                    conn.execute(
                        "INSERT INTO xonalar (bino_id,nomi,qavat,sigim,narx) VALUES (?,?,?,?,?)",
                        (bino_id, nomi, qavat, sigim, narx))
                    conn.commit()
                admin_state.pop(uid, None)
                bot.send_message(cid, f"Yangi xona '{nomi}' yaratildi!", reply_markup=admin_menu(uid))
            except:
                bot.send_message(cid, "Format: nom,qavat,joy_soni,narx\nMisol: 11-xona,1,3,300000")
            return

        if step == "add_admin_id":
            try:
                new_id = int(text)
                if new_id in DIRECTOR_IDS:
                    bot.send_message(cid, "Bu director ID, admin kerak emas")
                    return
                with db() as conn:
                    conn.execute("INSERT OR REPLACE INTO adminlar (user_id,ism,qoshilgan) VALUES (?,?,?)",
                                (new_id, "Admin", datetime.now().strftime("%d.%m.%Y %H:%M")))
                    conn.commit()
                admin_state.pop(uid, None)
                bot.send_message(cid, f"{new_id} admin qilindi!", reply_markup=admin_menu(uid))
                try:
                    bot.send_message(new_id, "Siz admin qilindingiz! /admin bosing.")
                except: pass
            except ValueError:
                bot.send_message(cid, "Faqat raqam kiriting")
            return

        if step == "ai_info":
            if text != "🔙 Admin menyu":
                with db() as conn:
                    conn.execute("INSERT INTO ai_info (matn,created_at) VALUES (?,?)",
                                (text, datetime.now().strftime("%d.%m.%Y %H:%M")))
                    conn.commit()
                bot.send_message(cid, f"AI ga qo'shildi:\n{text}\n\nYana yozing yoki menyuga qayting.")
            return

        if step == "mijoz_qidir":
            natija = qidir_mijoz(text)
            if natija:
                mijoz = natija.get("mijoz")
                bron = natija.get("bron")
                if mijoz:
                    blok = "Bloklangan" if mijoz["bloklangan"] else "Faol"
                    matn = (f"Mijoz: {mijoz['ism']}\n"
                            f"Tel: {mijoz['telefon']}\n"
                            f"TG: @{mijoz['username'] or 'yoq'}\n"
                            f"Holat: {blok}")
                    kb = types.InlineKeyboardMarkup()
                    if mijoz["bloklangan"]:
                        kb.add(types.InlineKeyboardButton("Blokdan chiqarish", callback_data=f"unblock_{mijoz['user_id']}"))
                    else:
                        kb.add(types.InlineKeyboardButton("Bloklash", callback_data=f"block_{mijoz['user_id']}"))
                    if mijoz.get("user_id"):
                        kb.add(types.InlineKeyboardButton("Xabar yuborish", callback_data=f"xabar_yukor_{mijoz['user_id']}"))
                    bot.send_message(cid, matn, reply_markup=kb)
                if bron:
                    tugash = tugash_sanasi(bron["sana"], bron["kunlar"])
                    bot.send_message(cid,
                        f"Bron #{bron['id']}\n{bron['xona']}\n{bron['sana']}-{tugash}\n"
                        f"{format_narx(bron['narx'])} som | {bron['holat']}")
            else:
                bot.send_message(cid, f"'{text}' topilmadi")
            return

        if step == "tb_kishi":
            try:
                n = int(text)
                state["ab"]["kishi"] = n
                state["step"] = "tb_sana"
                admin_state[uid] = state
                bot.send_message(cid, f"{n} kishi\nSana tanlang:", reply_markup=sana_tugmalari())
            except:
                bot.send_message(cid, "Raqam kiriting")
            return

        if step == "tb_ism":
            state["ab"]["ism"] = text
            state["step"] = "tb_telefon"
            admin_state[uid] = state
            bot.send_message(cid, "Telefon raqami:")
            return

        if step == "tb_telefon":
            ab = state["ab"]
            bron_id = bron_id_gen()
            tugash = tugash_sanasi(ab["sana"], ab["kunlar"])
            with db() as conn:
                conn.execute("""INSERT INTO bronlar
                    (id,ism,telefon,sana,kunlar,kishi,xona,narx,holat,user_id,username,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (bron_id, ab["ism"], text, ab["sana"], ab["kunlar"],
                     ab["kishi"], ab["xona_nomi"], ab["narx"],
                     "tasdiqlangan", DIRECTOR_IDS[0], "admin",
                     datetime.now().strftime("%d.%m.%Y %H:%M")))
                for xid in ab["xona_ids"]:
                    conn.execute("INSERT OR IGNORE INTO bron_xonalar VALUES (?,?)", (bron_id, xid))
                conn.commit()
            for xid in ab["xona_ids"]:
                band_qil(xid, ab["sana"], ab["kunlar"], bron_id)

            # Mijoz bazasida user_id topib xabar yuborish
            havola = f"t.me/togtagi_bot?start=bron_{bron_id}"
            bot.send_message(cid,
                f"Bron #{bron_id} qo'shildi!\n"
                f"{ab['xona_nomi']} | {ab['sana']}-{tugash} | {ab['kunlar']} kun\n"
                f"{format_narx(ab['narx'])} som\n\n"
                f"Mijozga yuboring:\n{havola}",
                reply_markup=admin_menu(uid))

            # Agar mijoz bazada bo'lsa xabar yuborish
            try:
                with db() as conn:
                    m2 = conn.execute("SELECT * FROM mijozlar WHERE telefon=?", (text,)).fetchone()
                    if not m2:
                        # Oxirgi 9 raqam bilan qidirish
                        if len(text) >= 9:
                            oxiri = text[-9:]
                            all_m = conn.execute("SELECT * FROM mijozlar").fetchall()
                            for mm in all_m:
                                if mm["telefon"] and str(mm["telefon"])[-9:] == oxiri:
                                    m2 = mm
                                    break
                if m2 and m2["user_id"]:
                    bot.send_message(m2["user_id"],
                        f"Broningiz tasdiqlandi! #{bron_id}\n"
                        f"Xona: {ab['xona_nomi']}\nSana: {ab['sana']}-{tugash}\n"
                        f"Narx: {format_narx(ab['narx'])} som\n\n"
                        f"Savollar: {TELEFON1}")
            except Exception as e:
                logging.error(e)

            admin_state.pop(uid, None)
            return

        if step == "xabar_yuborish":
            target_uid = state.get("xabar_uid")
            if target_uid:
                try:
                    bot.send_message(target_uid, f"Admin xabari:\n\n{text}")
                    bot.send_message(cid, "Xabar yuborildi!", reply_markup=admin_menu(uid))
                except:
                    bot.send_message(cid, "Xabar yuborib bo'lmadi (foydalanuvchi botni bloklagan)")
            admin_state.pop(uid, None)
            return

    # ==================== KUNLAR CALLBACK (Admin) ====================

    # kun_ callback mijoz.py da handle qilinadi
    # Admin uchun maxsus steplar mijoz.py da tekshiriladi

        if step == "ax_band_kunlar":
            xid = state["ax_xid"]
            sana = state["ax_sana"]
            band_qil(xid, sana, kunlar, "admin")
            admin_state.pop(uid, None)
            with db() as conn:
                x = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()
            bot.send_message(cid, f"{x['nomi']} - {sana} dan {kunlar} kun BAND qilindi",
                             reply_markup=admin_menu(uid))
            bot.answer_callback_query(call.id)
            return

        if step == "ax_bosh_kunlar":
            xid = state["ax_xid"]
            sana = state["ax_sana"]
            bosh_qil_sana(xid, sana, kunlar)
            admin_state.pop(uid, None)
            with db() as conn:
                x = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()
            bot.send_message(cid, f"{x['nomi']} - {sana} dan {kunlar} kun BOSH qilindi",
                             reply_markup=admin_menu(uid))
            bot.answer_callback_query(call.id)
            return

        if step == "tb_kunlar":
            state["ab"]["kunlar"] = kunlar
            state["step"] = "tb_xona"
            admin_state[uid] = state
            sana = state["ab"]["sana"]
            kishi = state["ab"].get("kishi", 1)
            from utils import mos_kombinatsiya
            kombinatsiyalar = mos_kombinatsiya(kishi, "oila", sana, kunlar)

            kb = types.InlineKeyboardMarkup(row_width=1)
            if kombinatsiyalar:
                for x in kombinatsiyalar[0]["xonalar"]:
                    tugash = __import__('utils').tugash_sanasi(sana, kunlar)
                    narx = format_narx(x["narx"] * kunlar)
                    kb.add(types.InlineKeyboardButton(
                        f"{x['nomi']} | {x['sigim']} kishi | {narx} so'm",
                        callback_data=f"tb_xona_{x['id']}"))
            kb.add(types.InlineKeyboardButton("Barcha bosh xonalar", callback_data="tb_barchasi"))
            bot.send_message(cid, f"Sana: {sana} | {kunlar} kun\nXonani tanlang:", reply_markup=kb)
            bot.answer_callback_query(call.id)
            return

        bot.answer_callback_query(call.id)

    # ==================== SANA CALLBACK (Admin) ====================

    # sana_ callback mijoz.py da handle qilinadi (admin uchun ham)

    # ==================== TEZKOR BRON XONA ====================

    @bot.callback_query_handler(func=lambda c: c.data.startswith("tb_xona_") and is_admin(c.from_user.id))
    def cb_tb_xona(call):
        from handlers.admin_state import admin_state
        from handlers.admin import admin_menu
        uid = call.from_user.id
        xid = int(call.data.replace("tb_xona_", ""))
        state = admin_state.get(uid, {})
        with db() as conn:
            x = conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()
        state["ab"]["xona_ids"] = [xid]
        state["ab"]["xona_nomi"] = x["nomi"]
        state["ab"]["narx"] = x["narx"] * state["ab"]["kunlar"]
        state["step"] = "tb_ism"
        admin_state[uid] = state
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(call.message.chat.id, f"{x['nomi']} tanlandi\n\nMijoz ismi:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "tb_barchasi" and is_admin(c.from_user.id))
    def cb_tb_barchasi(call):
        from handlers.admin_state import admin_state
        uid = call.from_user.id
        state = admin_state.get(uid, {})
        ab = state.get("ab", {})
        sana = ab.get("sana", "")
        kunlar = ab.get("kunlar", 1)
        from utils import barcha_bosh_xonalar
        kb = barcha_bosh_xonalar(sana, kunlar)
        # Tugmalar callback ni tb_ ga o'zgartirish
        new_kb = types.InlineKeyboardMarkup(row_width=1)
        for row in kb.keyboard:
            for btn in row:
                if btn.callback_data and btn.callback_data.startswith("xona_tanla_"):
                    parts = btn.callback_data.split("_")
                    xid = parts[2]
                    new_btn = types.InlineKeyboardButton(btn.text, callback_data=f"tb_xona_{xid}")
                    new_kb.add(new_btn)
        bot.edit_message_text("Barcha bosh xonalar:",
                              call.message.chat.id, call.message.message_id, reply_markup=new_kb)
        bot.answer_callback_query(call.id)

    # ==================== XABAR YUBORISH ====================

    @bot.callback_query_handler(func=lambda c: c.data.startswith("xabar_yukor_") and is_admin(c.from_user.id))
    def cb_xabar_yukor(call):
        from handlers.admin_state import admin_state
        from handlers.admin import admin_menu
        target = int(call.data.replace("xabar_yukor_", ""))
        admin_state[call.from_user.id] = {"step": "xabar_yuborish", "xabar_uid": target}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(call.message.chat.id, "Mijozga xabar yozing:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    # ==================== BLOKLASH ====================

    @bot.callback_query_handler(func=lambda c: c.data.startswith("block_") and is_admin(c.from_user.id))
    def cb_block(call):
        uid = int(call.data.replace("block_", ""))
        with db() as conn:
            conn.execute("UPDATE mijozlar SET bloklangan=1 WHERE user_id=?", (uid,))
            conn.commit()
        bot.edit_message_text(f"{uid} bloklandi", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Bloklandi!")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("unblock_") and is_admin(c.from_user.id))
    def cb_unblock(call):
        uid = int(call.data.replace("unblock_", ""))
        with db() as conn:
            conn.execute("UPDATE mijozlar SET bloklangan=0 WHERE user_id=?", (uid,))
            conn.commit()
        bot.edit_message_text(f"{uid} blokdan chiqarildi", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Blok ochildi!")
