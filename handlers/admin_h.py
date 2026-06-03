from telebot import types
from datetime import datetime, timedelta
from io import BytesIO
from db import (get_db, get_xonalar, get_binolar, xona_band_mi, band_qil,
                bosh_qil_sana, bosh_qil_bron, bekor_qil_bron, get_bron,
                get_bron_xonalar, tugash_sanasi, format_narx, is_admin,
                is_director, bron_id_gen, qidir_mijoz, bugungi_stat, log_stat)
from config import TELEFON1, DIRECTOR_IDS
from keyboards import (admin_kb, binolar_kb, xonalar_admin_kb, xona_detail_kb,
                       sana_kb, kunlar_kb)


def register(bot):

    @bot.message_handler(commands=["admin"])
    def cmd_admin(msg):
        if not is_admin(msg.from_user.id):
            bot.send_message(msg.chat.id, "Ruxsat yoq")
            return
        bot.send_message(msg.chat.id, "Admin panel:", reply_markup=admin_kb(msg.from_user.id))

    # ===== ASOSIY TUGMALAR =====

    @bot.message_handler(func=lambda m: m.text == "🏨 Xonalar" and is_admin(m.from_user.id))
    def h_xonalar(msg):
        bot.send_message(msg.chat.id, "Binoni tanlang:", reply_markup=binolar_kb())
        if is_director(msg.from_user.id):
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("➕ Yangi bino", callback_data="YANGI_BINO"))
            bot.send_message(msg.chat.id, "Yangi bino:", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "📋 Bronlar" and is_admin(m.from_user.id))
    def h_bronlar(msg):
        bugun = datetime.now().date()
        oxiri = bugun + timedelta(days=10)
        conn = get_db()
        bronlar = conn.execute(
            "SELECT * FROM bronlar WHERE holat != 'bekor' ORDER BY sana").fetchall()
        conn.close()
        bronlar = [b for b in bronlar
                   if b["sana"] >= bugun.strftime("%d.%m.%Y")
                   and b["sana"] <= oxiri.strftime("%d.%m.%Y")]
        if not bronlar:
            bot.send_message(msg.chat.id, "10 kunda bron yoq", reply_markup=admin_kb(msg.from_user.id))
            return
        matn = f"10 kunlik bronlar ({len(bronlar)} ta):\n\n"
        kb = types.InlineKeyboardMarkup(row_width=1)
        for b in bronlar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            h = "✅" if b["holat"] == "tasdiqlangan" else "⏳"
            matn += f"{h} #{b['id']} | {b['xona']}\n{b['ism']} | {b['sana']}-{tugash}\n\n"
            kb.add(types.InlineKeyboardButton(
                f"{h} #{b['id']} - {b['ism']} ({b['sana']})",
                callback_data=f"BDET_{b['id']}"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "📊 Bugungi holat" and is_admin(m.from_user.id))
    def h_bugungi(msg):
        bugun = datetime.now().strftime("%d.%m.%Y")
        matn = f"Bugungi holat ({bugun}):\n\n"
        conn = get_db()
        for b in get_binolar():
            matn += f"🏢 {b['nomi']}:\n"
            for x in get_xonalar(b["id"]):
                h = "🔴 Band" if xona_band_mi(x["id"], bugun) else "🟢 Bosh"
                info = ""
                if xona_band_mi(x["id"], bugun):
                    brow = conn.execute("SELECT bron_id FROM band WHERE xona_id=? AND sana=?",
                                       (x["id"], bugun)).fetchone()
                    if brow and brow["bron_id"] != "admin":
                        bron = conn.execute("SELECT * FROM bronlar WHERE id=?",
                                           (brow["bron_id"],)).fetchone()
                        if bron:
                            tugash = tugash_sanasi(bron["sana"], bron["kunlar"])
                            info = f" | {bron['ism']} | -{tugash}"
                matn += f"  {x['nomi']}({x['sigim']}) - {h}{info}\n"
            matn += "\n"
        conn.close()
        bot.send_message(msg.chat.id, matn, reply_markup=admin_kb(msg.from_user.id))

    @bot.message_handler(func=lambda m: m.text == "👥 Mehmonlar" and is_admin(m.from_user.id))
    def h_mehmonlar(msg):
        bugun = datetime.now().strftime("%d.%m.%Y")
        conn = get_db()
        bids = conn.execute(
            "SELECT DISTINCT bron_id FROM band WHERE sana=? AND bron_id != 'admin'",
            (bugun,)).fetchall()
        mehmonlar = []
        for r in bids:
            b = conn.execute("SELECT * FROM bronlar WHERE id=? AND holat='tasdiqlangan'",
                             (r["bron_id"],)).fetchone()
            if b:
                mehmonlar.append(b)
        conn.close()
        if not mehmonlar:
            bot.send_message(msg.chat.id, f"Bugun ({bugun}) mehmon yoq",
                             reply_markup=admin_kb(msg.from_user.id))
            return
        jami = sum(b["kishi"] for b in mehmonlar)
        matn = f"Hozirgi mehmonlar ({bugun}):\nJami: {len(mehmonlar)} xona | {jami} kishi\n\n"
        for b in mehmonlar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            matn += f"#{b['id']} | {b['xona']}\n{b['ism']} | {b['telefon']}\n{b['sana']}-{tugash}\n\n"
        bot.send_message(msg.chat.id, matn, reply_markup=admin_kb(msg.from_user.id))

    @bot.message_handler(func=lambda m: m.text == "📅 10 kunlik" and is_admin(m.from_user.id))
    def h_10kun(msg):
        bugun = datetime.now().date()
        sanalar = [(bugun + timedelta(days=i)) for i in range(10)]
        matn = "10 kunlik holat:\n\n"
        matn += "    " + " ".join(k.strftime("%d/%m") for k in sanalar) + "\n\n"
        kb = types.InlineKeyboardMarkup(row_width=1)
        for x in get_xonalar():
            satri = f"{x['nomi']:8} "
            for kun in sanalar:
                satri += "🔴" if xona_band_mi(x["id"], kun.strftime("%d.%m.%Y")) else "🟢"
            matn += satri + "\n"
            kb.add(types.InlineKeyboardButton(
                f"{x['nomi']} - Ko'rish/Bron",
                callback_data=f"AX_{x['id']}"))
        matn += "\n🟢=Bosh 🔴=Band"
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "👤 Mijoz qidirish" and is_admin(m.from_user.id))
    def h_mijoz_qidir(msg):
        from handlers.astate import astate
        astate[msg.from_user.id] = {"step": "mijoz_qidir"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(msg.chat.id, "Telefon, bron ID yoki username kiriting:", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "➕ Tezkor bron" and is_admin(m.from_user.id))
    def h_tezkor(msg):
        from handlers.astate import astate
        astate[msg.from_user.id] = {"step": "tb_kishi", "ab": {}}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
        for i in range(1, 11):
            kb.add(str(i))
        kb.add("🔙 Admin menyu")
        bot.send_message(msg.chat.id, "Tezkor bron\nNechta kishi?", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "📸 Galereya" and is_admin(m.from_user.id))
    def h_galereya(msg):
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("📸 Umumiy rasmlar", callback_data="GAL_RASM"),
            types.InlineKeyboardButton("🎥 Videolar", callback_data="GAL_VIDEO"),
            types.InlineKeyboardButton("🖼 Greeting rasmi", callback_data="GAL_GREETING"),
        )
        bot.send_message(msg.chat.id, "Galereya:", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "📄 Hisobot" and is_admin(m.from_user.id))
    def h_hisobot(msg):
        conn = get_db()
        bronlar = conn.execute("SELECT * FROM bronlar ORDER BY created_at DESC").fetchall()
        conn.close()
        if not bronlar:
            bot.send_message(msg.chat.id, "Bron yoq")
            return
        matn = "BARCHA BRONLAR\n" + "="*40 + "\n\n"
        for b in bronlar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            matn += (f"#{b['id']} | {b['holat'].upper()}\n"
                     f"Ism: {b['ism']} | Tel: {b['telefon']}\n"
                     f"Sana: {b['sana']}-{tugash} | {b['kunlar']} kun\n"
                     f"Xona: {b['xona']} | Kishi: {b['kishi']}\n"
                     f"Narx: {format_narx(b['narx'])} som\n"
                     + "-"*30 + "\n")
        buf = BytesIO(matn.encode("utf-8"))
        buf.name = "bronlar.txt"
        bot.send_document(msg.chat.id, buf, caption=f"Jami: {len(bronlar)} ta")

    @bot.message_handler(func=lambda m: m.text == "🤖 AI malumot" and is_admin(m.from_user.id))
    def h_ai(msg):
        from handlers.astate import astate
        astate[msg.from_user.id] = {"step": "ai_info"}
        conn = get_db()
        rows = conn.execute("SELECT * FROM ai_info ORDER BY id DESC LIMIT 5").fetchall()
        conn.close()
        matn = "AI malumotlar:\n\n"
        kb = types.InlineKeyboardMarkup(row_width=1)
        for r in rows:
            matn += f"• {r['matn'][:60]}\n"
            kb.add(types.InlineKeyboardButton(f"🗑 #{r['id']}", callback_data=f"DEL_AI_{r['id']}"))
        kb.add(types.InlineKeyboardButton("🗑 Hammasini ochir", callback_data="DEL_AI_ALL"))
        reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        reply_kb.add("🔙 Admin menyu")
        bot.send_message(msg.chat.id, matn + "\nYangi malumot yozing:", reply_markup=reply_kb)
        if rows:
            bot.send_message(msg.chat.id, "Ochirish:", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "📊 Statistika" and is_director(m.from_user.id))
    def h_stat(msg):
        stat = bugungi_stat()
        bugun = datetime.now().strftime("%d.%m.%Y")
        matn = (f"Statistika ({bugun}):\n\n"
                f"Foydalanuvchilar: {stat['foydalanuvchilar']}\n"
                f"Yangi bronlar: {stat['bronlar']}\n\nHarakatlar:\n")
        for h in stat["harakatlar"]:
            matn += f"  {h['harakat']}: {h['c']} marta\n"
        bot.send_message(msg.chat.id, matn, reply_markup=admin_kb(msg.from_user.id))

    @bot.message_handler(func=lambda m: m.text == "👮 Adminlar" and is_director(m.from_user.id))
    def h_adminlar(msg):
        conn = get_db()
        adminlar = conn.execute("SELECT * FROM adminlar").fetchall()
        conn.close()
        matn = f"Adminlar:\n\n"
        for a in adminlar:
            matn += f"ID: {a['user_id']} | {a['ism'] or 'Admin'}\n"
        matn += f"\nDirectorlar: {', '.join(str(d) for d in DIRECTOR_IDS)}"
        kb = types.InlineKeyboardMarkup(row_width=1)
        for a in adminlar:
            kb.add(types.InlineKeyboardButton(
                f"Del: {a['ism'] or a['user_id']}",
                callback_data=f"DEL_ADM_{a['user_id']}"))
        kb.add(types.InlineKeyboardButton("➕ Admin qoshish", callback_data="ADD_ADM"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "🔙 Asosiy menyu" and is_admin(m.from_user.id))
    def h_asosiy(msg):
        from handlers.astate import astate
        astate.pop(msg.from_user.id, None)
        from keyboards import asosiy_kb
        bot.send_message(msg.chat.id, "Asosiy menyu", reply_markup=asosiy_kb(msg.from_user.id))

    @bot.message_handler(func=lambda m: m.text == "🔙 Admin menyu" and is_admin(m.from_user.id))
    def h_admin_menyu(msg):
        from handlers.astate import astate
        astate.pop(msg.from_user.id, None)
        bot.send_message(msg.chat.id, "Admin panel:", reply_markup=admin_kb(msg.from_user.id))

    # ===== CALLBACKS =====

    @bot.callback_query_handler(func=lambda c: c.data.startswith("BINO_"))
    def cb_bino(call):
        if not is_admin(call.from_user.id): return
        bino_id = int(call.data.replace("BINO_", ""))
        conn = get_db()
        bino = conn.execute("SELECT * FROM binolar WHERE id=?", (bino_id,)).fetchone()
        conn.close()
        kb = xonalar_admin_kb(bino_id)
        if is_director(call.from_user.id):
            kb.add(types.InlineKeyboardButton(
                f"➕ Yangi xona ({bino['nomi']})",
                callback_data=f"YANGI_XONA_{bino_id}"))
        try:
            bot.edit_message_text(f"🏢 {bino['nomi']}:",
                                  call.message.chat.id, call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, f"🏢 {bino['nomi']}:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AX_") and not c.data.startswith("AXB") and not c.data.startswith("AXBAND") and not c.data.startswith("AXBOSH") and not c.data.startswith("AXRASM") and not c.data.startswith("AXVIDEO") and not c.data.startswith("AXNARX"))
    def cb_ax(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AX_", ""))
        conn = get_db()
        x = conn.execute("SELECT x.*, COALESCE(b.nomi,'1-bino') as bino_nomi FROM xonalar x LEFT JOIN binolar b ON x.bino_id=b.id WHERE x.id=?", (xid,)).fetchone()
        rasmlar = conn.execute("SELECT COUNT(*) as c FROM xona_media WHERE xona_id=? AND tur='photo'", (xid,)).fetchone()["c"]
        conn.close()
        bugun = datetime.now().strftime("%d.%m.%Y")
        h = "🔴 Band" if xona_band_mi(xid, bugun) else "🟢 Bosh"
        matn = (f"{x['nomi']} | {x['bino_nomi']}\n"
                f"Qavat: {x['qavat']} | Joy: {x['sigim']}👤\n"
                f"Narx: {format_narx(x['narx'])} som\n"
                f"Bugun: {h} | Rasmlar: {rasmlar}")
        try:
            bot.edit_message_text(matn, call.message.chat.id, call.message.message_id,
                                  reply_markup=xona_detail_kb(xid, x["bino_id"]))
        except:
            bot.send_message(call.message.chat.id, matn, reply_markup=xona_detail_kb(xid, x["bino_id"]))
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXB_"))
    def cb_axb(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AXB_", ""))
        conn = get_db()
        x = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()
        bids = conn.execute("SELECT DISTINCT bron_id FROM bron_xonalar WHERE xona_id=?", (xid,)).fetchall()
        bronlar = []
        for r in bids:
            b = conn.execute("SELECT * FROM bronlar WHERE id=? AND holat != 'bekor'", (r["bron_id"],)).fetchone()
            if b:
                bronlar.append(b)
        conn.close()
        matn = f"{x['nomi']} bronlari:\n\n"
        kb = types.InlineKeyboardMarkup(row_width=1)
        for b in bronlar[-8:]:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            h = "✅" if b["holat"] == "tasdiqlangan" else "⏳"
            matn += f"{h} #{b['id']} | {b['sana']}-{tugash}\n{b['ism']} | {b['telefon']}\n\n"
            kb.add(types.InlineKeyboardButton(f"{h} #{b['id']} - {b['ism']}", callback_data=f"BDET_{b['id']}"))
        # 15 kun
        matn += "15 kunlik holat:\n"
        bugun = datetime.now().date()
        for i in range(15):
            kun = bugun + timedelta(days=i)
            h = "🔴" if xona_band_mi(xid, kun.strftime("%d.%m.%Y")) else "🟢"
            matn += f"{h}{kun.strftime('%d/%m')} "
            if (i+1) % 5 == 0:
                matn += "\n"
        kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"AX_{xid}"))
        try:
            bot.edit_message_text(matn, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, matn, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("BDET_"))
    def cb_bdet(call):
        if not is_admin(call.from_user.id): return
        bid = call.data.replace("BDET_", "")
        b = get_bron(bid)
        if not b: return
        tugash = tugash_sanasi(b["sana"], b["kunlar"])
        matn = (f"Bron #{b['id']}\n\nIsm: {b['ism']}\nTel: {b['telefon']}\n"
                f"Xona: {b['xona']}\nSana: {b['sana']}-{tugash}\n"
                f"Kunlar: {b['kunlar']} | Kishi: {b['kishi']}\n"
                f"Narx: {format_narx(b['narx'])} som\nHolat: {b['holat']}")
        kb = types.InlineKeyboardMarkup(row_width=2)
        if b["holat"] == "kutilmoqda":
            kb.add(
                types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ATASDIQ_ha_{bid}"),
                types.InlineKeyboardButton("❌ Rad etish", callback_data=f"ATASDIQ_yoq_{bid}"))
        if b["holat"] != "bekor":
            kb.add(types.InlineKeyboardButton("🗑 Bekor qilish", callback_data=f"ABEKOR_{bid}"))
        try:
            bot.edit_message_text(matn, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, matn, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ATASDIQ_"))
    def cb_atasdiq(call):
        if not is_admin(call.from_user.id): return
        parts = call.data.split("_")
        action, bid = parts[1], parts[2]
        b = get_bron(bid)
        if not b:
            bot.answer_callback_query(call.id, "Topilmadi")
            return
        if action == "ha":
            xid_list = get_bron_xonalar(bid)
            for xid in xid_list:
                band_qil(xid, b["sana"], b["kunlar"], bid)
            conn = get_db()
            conn.execute("UPDATE bronlar SET holat='tasdiqlangan' WHERE id=?", (bid,))
            conn.commit()
            conn.close()
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            if b["user_id"]:
                try:
                    from db import get_til
                    bot.send_message(b["user_id"],
                        f"Broningiz tasdiqlandi! #{bid}\n"
                        f"Xona: {b['xona']}\nSana: {b['sana']}-{tugash}\n"
                        f"Kishi: {b['kishi']}\nNarx: {format_narx(b['narx'])} som\n\n"
                        f"Kelishingizni kutamiz! {TELEFON1}")
                except: pass
            bot.edit_message_text(f"Bron #{bid} TASDIQLANDI",
                                  call.message.chat.id, call.message.message_id)
        else:
            bekor_qil_bron(bid)
            if b["user_id"]:
                try:
                    bot.send_message(b["user_id"], f"Bron #{bid} rad etildi. {TELEFON1}")
                except: pass
            bot.edit_message_text(f"Bron #{bid} RAD ETILDI",
                                  call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ABEKOR_"))
    def cb_abekor(call):
        if not is_admin(call.from_user.id): return
        bid = call.data.replace("ABEKOR_", "")
        b = get_bron(bid)
        bekor_qil_bron(bid)
        if b and b["user_id"]:
            try:
                bot.send_message(b["user_id"], f"Bron #{bid} admin tomonidan bekor qilindi. {TELEFON1}")
            except: pass
        bot.edit_message_text(f"Bron #{bid} bekor qilindi",
                              call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXBAND_"))
    def cb_axband(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AXBAND_", ""))
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "band_sana", "xid": xid}
        conn = get_db()
        xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
        conn.close()
        bot.send_message(call.message.chat.id, f"{xnomi} - band qilish\nSana tanlang:", reply_markup=sana_kb())
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXBOSH_"))
    def cb_axbosh(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AXBOSH_", ""))
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "bosh_sana", "xid": xid}
        conn = get_db()
        xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
        conn.close()
        bot.send_message(call.message.chat.id, f"{xnomi} - bosh qilish\nSana tanlang:", reply_markup=sana_kb())
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXRASM_"))
    def cb_axrasm(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AXRASM_", ""))
        conn = get_db()
        rasmlar = conn.execute("SELECT * FROM xona_media WHERE xona_id=? AND tur='photo'", (xid,)).fetchall()
        xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
        conn.close()
        kb = types.InlineKeyboardMarkup(row_width=2)
        for r in rasmlar:
            kb.add(types.InlineKeyboardButton(f"🗑 #{r['id']}", callback_data=f"DEL_XRASM_{r['id']}_{xid}"))
        kb.add(types.InlineKeyboardButton("➕ Rasm qoshish", callback_data=f"ADD_XRASM_{xid}"))
        kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"AX_{xid}"))
        bot.send_message(call.message.chat.id,
                         f"{xnomi} rasmlari ({len(rasmlar)} ta):", reply_markup=kb)
        if rasmlar:
            try:
                media = [types.InputMediaPhoto(rasmlar[0]["file_id"])]
                for r in rasmlar[1:5]:
                    media.append(types.InputMediaPhoto(r["file_id"]))
                bot.send_media_group(call.message.chat.id, media)
            except: pass
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("DEL_XRASM_"))
    def cb_del_xrasm(call):
        if not is_admin(call.from_user.id): return
        parts = call.data.split("_")
        rid, xid = int(parts[2]), int(parts[3])
        conn = get_db()
        conn.execute("DELETE FROM xona_media WHERE id=?", (rid,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Ochirildi!")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ADD_XRASM_"))
    def cb_add_xrasm(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("ADD_XRASM_", ""))
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "xona_rasm", "xid": xid}
        bot.send_message(call.message.chat.id, "Rasmlarni yuboring.\n/done - tugallash")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXVIDEO_"))
    def cb_axvideo(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AXVIDEO_", ""))
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "xona_video", "xid": xid}
        bot.send_message(call.message.chat.id, "Video yuboring.\n/done - tugallash")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXNARX_"))
    def cb_axnarx(call):
        if not is_director(call.from_user.id): return
        xid = int(call.data.replace("AXNARX_", ""))
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "narx", "xid": xid}
        bot.send_message(call.message.chat.id, "Yangi narxni kiriting (som):")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "YANGI_BINO")
    def cb_yangi_bino(call):
        if not is_director(call.from_user.id): return
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "yangi_bino"}
        bot.send_message(call.message.chat.id, "Yangi bino nomini kiriting:")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("YANGI_XONA_"))
    def cb_yangi_xona(call):
        if not is_director(call.from_user.id): return
        bino_id = int(call.data.replace("YANGI_XONA_", ""))
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "yangi_xona", "bino_id": bino_id}
        bot.send_message(call.message.chat.id,
                         "Format: nom,qavat,joy_soni,narx\nMisol: 11-xona,1,3,300000")
        bot.answer_callback_query(call.id)

    # Galereya callbacklari
    @bot.callback_query_handler(func=lambda c: c.data == "GAL_RASM")
    def cb_gal_rasm(call):
        if not is_admin(call.from_user.id): return
        conn = get_db()
        rasmlar = conn.execute("SELECT * FROM umumiy_media WHERE tur='photo' ORDER BY id").fetchall()
        conn.close()
        kb = types.InlineKeyboardMarkup(row_width=3)
        for r in rasmlar:
            kb.add(types.InlineKeyboardButton(f"🗑 #{r['id']}", callback_data=f"DEL_URASM_{r['id']}"))
        kb.add(types.InlineKeyboardButton("➕ Rasm yuklash", callback_data="ADD_URASM"))
        bot.edit_message_text(f"Umumiy rasmlar ({len(rasmlar)} ta):",
                              call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("DEL_URASM_"))
    def cb_del_urasm(call):
        if not is_admin(call.from_user.id): return
        mid = int(call.data.replace("DEL_URASM_", ""))
        conn = get_db()
        conn.execute("DELETE FROM umumiy_media WHERE id=?", (mid,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Ochirildi!")
        cb_gal_rasm(call)

    @bot.callback_query_handler(func=lambda c: c.data == "ADD_URASM")
    def cb_add_urasm(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "umumiy_rasm"}
        bot.send_message(call.message.chat.id, "Rasmlarni yuboring.\n/done - tugallash")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "GAL_VIDEO")
    def cb_gal_video(call):
        if not is_admin(call.from_user.id): return
        conn = get_db()
        videolar = conn.execute("SELECT * FROM umumiy_media WHERE tur='video' ORDER BY id").fetchall()
        conn.close()
        kb = types.InlineKeyboardMarkup(row_width=2)
        for v in videolar:
            kb.add(types.InlineKeyboardButton(f"🗑 #{v['id']}", callback_data=f"DEL_VID_{v['id']}"))
        kb.add(types.InlineKeyboardButton("➕ Video yuklash", callback_data="ADD_VID"))
        bot.edit_message_text(f"Videolar ({len(videolar)} ta):",
                              call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("DEL_VID_"))
    def cb_del_vid(call):
        if not is_admin(call.from_user.id): return
        vid = int(call.data.replace("DEL_VID_", ""))
        conn = get_db()
        conn.execute("DELETE FROM umumiy_media WHERE id=?", (vid,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Ochirildi!")
        cb_gal_video(call)

    @bot.callback_query_handler(func=lambda c: c.data == "ADD_VID")
    def cb_add_vid(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "umumiy_video"}
        bot.send_message(call.message.chat.id, "Video yuboring.\n/done - tugallash")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "GAL_GREETING")
    def cb_greeting(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "greeting"}
        bot.send_message(call.message.chat.id, "Greeting rasmini yuboring:")
        bot.answer_callback_query(call.id)

    # Admin qoshish/ochirish
    @bot.callback_query_handler(func=lambda c: c.data == "ADD_ADM")
    def cb_add_adm(call):
        if not is_director(call.from_user.id): return
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "add_admin"}
        bot.send_message(call.message.chat.id, "Yangi admin ID kiriting:")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("DEL_ADM_"))
    def cb_del_adm(call):
        if not is_director(call.from_user.id): return
        uid = int(call.data.replace("DEL_ADM_", ""))
        conn = get_db()
        conn.execute("DELETE FROM adminlar WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        bot.edit_message_text(f"Admin {uid} ochirildi", call.message.chat.id, call.message.message_id)
        try:
            bot.send_message(uid, "Admin huquqingiz bekor qilindi.")
        except: pass
        bot.answer_callback_query(call.id)

    # AI info ochirish
    @bot.callback_query_handler(func=lambda c: c.data.startswith("DEL_AI_"))
    def cb_del_ai(call):
        if not is_admin(call.from_user.id): return
        data = call.data.replace("DEL_AI_", "")
        conn = get_db()
        if data == "ALL":
            conn.execute("DELETE FROM ai_info")
        else:
            conn.execute("DELETE FROM ai_info WHERE id=?", (int(data),))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Ochirildi!")

    # Tezkor bron xona tanlash
    @bot.callback_query_handler(func=lambda c: c.data.startswith("TBXT_"))
    def cb_tbxt(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        xid = int(call.data.replace("TBXT_", ""))
        conn = get_db()
        x = conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()
        conn.close()
        st = astate.get(call.from_user.id, {})
        kunlar = st["ab"].get("kunlar", 1)
        st["ab"]["xona_ids"] = [xid]
        st["ab"]["xona_nomi"] = x["nomi"]
        st["ab"]["narx"] = x["narx"] * kunlar
        st["step"] = "tb_ism"
        astate[call.from_user.id] = st
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(call.message.chat.id, f"{x['nomi']} tanlandi\n\nMijoz ismi:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "TB_BARCHASI")
    def cb_tb_barchasi(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        st = astate.get(call.from_user.id, {})
        sana = st["ab"].get("sana", "")
        kunlar = st["ab"].get("kunlar", 1)
        kb = xonalar_kb(sana, kunlar)
        # Callback ni TBXT_ ga o'zgartirish
        new_kb = types.InlineKeyboardMarkup(row_width=1)
        for row in kb.keyboard:
            for btn in row:
                if btn.callback_data and btn.callback_data.startswith("XT_"):
                    parts = btn.callback_data.split("_")
                    xid = parts[1]
                    new_kb.add(types.InlineKeyboardButton(btn.text, callback_data=f"TBXT_{xid}"))
        bot.edit_message_text("Barcha bosh xonalar:",
                              call.message.chat.id, call.message.message_id, reply_markup=new_kb)
        bot.answer_callback_query(call.id)

    # Media qabul qilish
    @bot.message_handler(content_types=["photo"])
    def h_photo(msg):
        if not is_admin(msg.from_user.id): return
        from handlers.astate import astate
        st = astate.get(msg.from_user.id, {})
        step = st.get("step")
        file_id = msg.photo[-1].file_id
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        conn = get_db()
        if step == "xona_rasm":
            conn.execute("INSERT INTO xona_media (xona_id,tur,file_id) VALUES (?,?,?)",
                        (st["xid"], "photo", file_id))
            cnt = conn.execute("SELECT COUNT(*) as c FROM xona_media WHERE xona_id=? AND tur='photo'", (st["xid"],)).fetchone()["c"]
            conn.commit()
            conn.close()
            bot.send_message(msg.chat.id, f"Saqlandi! Jami: {cnt} ta\n/done - tugallash")
        elif step == "umumiy_rasm":
            conn.execute("INSERT INTO umumiy_media (tur,file_id) VALUES (?,?)", ("photo", file_id))
            cnt = conn.execute("SELECT COUNT(*) as c FROM umumiy_media WHERE tur='photo'").fetchone()["c"]
            conn.commit()
            conn.close()
            bot.send_message(msg.chat.id, f"Saqlandi! Jami: {cnt} ta\n/done - tugallash")
        elif step == "greeting":
            conn.execute("DELETE FROM greeting_media")
            conn.execute("INSERT INTO greeting_media (id,file_id,tur) VALUES (1,?,?)", (file_id, "photo"))
            conn.commit()
            conn.close()
            astate.pop(msg.from_user.id, None)
            bot.send_message(msg.chat.id, "Greeting rasmi saqlandi!", reply_markup=admin_kb(msg.from_user.id))
        else:
            conn.close()

    @bot.message_handler(content_types=["video"])
    def h_video(msg):
        if not is_admin(msg.from_user.id): return
        from handlers.astate import astate
        st = astate.get(msg.from_user.id, {})
        step = st.get("step")
        file_id = msg.video.file_id
        conn = get_db()
        if step == "xona_video":
            conn.execute("INSERT INTO xona_media (xona_id,tur,file_id) VALUES (?,?,?)",
                        (st["xid"], "video", file_id))
            cnt = conn.execute("SELECT COUNT(*) as c FROM xona_media WHERE xona_id=? AND tur='video'", (st["xid"],)).fetchone()["c"]
            conn.commit()
            conn.close()
            bot.send_message(msg.chat.id, f"Video saqlandi! Jami: {cnt} ta\n/done - tugallash")
        elif step == "umumiy_video":
            conn.execute("INSERT INTO umumiy_media (tur,file_id) VALUES (?,?)", ("video", file_id))
            cnt = conn.execute("SELECT COUNT(*) as c FROM umumiy_media WHERE tur='video'").fetchone()["c"]
            conn.commit()
            conn.close()
            bot.send_message(msg.chat.id, f"Video saqlandi! Jami: {cnt} ta\n/done - tugallash")
        else:
            conn.close()

    @bot.message_handler(commands=["done"])
    def cmd_done(msg):
        if not is_admin(msg.from_user.id): return
        from handlers.astate import astate
        astate.pop(msg.from_user.id, None)
        bot.send_message(msg.chat.id, "Saqlandi!", reply_markup=admin_kb(msg.from_user.id))


def admin_matn_handler(bot, msg, uid, text, astate):
    """Admin matn xabarlarini handle qilish"""
    st = astate.get(uid, {})
    step = st.get("step")
    cid = msg.chat.id

    if step == "tb_kishi":
        try:
            n = int(text)
            st["ab"]["kishi"] = n
            st["step"] = "tb_sana"
            astate[uid] = st
            bot.send_message(cid, f"{n} kishi\nSana tanlang:", reply_markup=sana_kb())
        except:
            bot.send_message(cid, "Raqam kiriting")
        return

    if step == "tb_ism":
        st["ab"]["ism"] = text
        st["step"] = "tb_tel"
        astate[uid] = st
        bot.send_message(cid, "Telefon raqami:")
        return

    if step == "tb_tel":
        ab = st["ab"]
        bid = bron_id_gen()
        tugash = tugash_sanasi(ab["sana"], ab["kunlar"])
        conn = get_db()
        conn.execute("""INSERT INTO bronlar
            (id,ism,telefon,sana,kunlar,kishi,xona,narx,holat,user_id,username,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (bid, ab["ism"], text, ab["sana"], ab["kunlar"],
             ab["kishi"], ab["xona_nomi"], ab["narx"], "tasdiqlangan",
             DIRECTOR_IDS[0], "admin", datetime.now().strftime("%d.%m.%Y %H:%M")))
        for xid in ab["xona_ids"]:
            conn.execute("INSERT OR IGNORE INTO bron_xonalar VALUES (?,?)", (bid, xid))
        conn.commit()
        conn.close()
        for xid in ab["xona_ids"]:
            band_qil(xid, ab["sana"], ab["kunlar"], bid)

        havola = f"t.me/togtagi_bot?start=bron_{bid}"
        bot.send_message(cid,
            f"Bron #{bid} qoshildi!\n{ab['xona_nomi']} | {ab['sana']}-{tugash}\n"
            f"{format_narx(ab['narx'])} som\n\nMijozga yuboring:\n{havola}",
            reply_markup=admin_kb(uid))

        # Agar mijoz bazada bo'lsa xabar yuborish
        try:
            conn2 = get_db()
            m2 = None
            if len(text) >= 9:
                all_m = conn2.execute("SELECT * FROM mijozlar").fetchall()
                for mm in all_m:
                    if mm["telefon"] and str(mm["telefon"])[-9:] == text[-9:]:
                        m2 = mm
                        break
            conn2.close()
            if m2 and m2["user_id"]:
                bot.send_message(m2["user_id"],
                    f"Broningiz tasdiqlandi! #{bid}\n{ab['xona_nomi']}\n"
                    f"{ab['sana']}-{tugash}\n{format_narx(ab['narx'])} som")
        except: pass
        astate.pop(uid, None)
        return

    if step == "mijoz_qidir":
        natija = qidir_mijoz(text)
        if natija:
            mijoz = natija.get("mijoz")
            bron = natija.get("bron")
            if mijoz:
                blok = "Bloklangan" if mijoz.get("bloklangan") else "Faol"
                matn = (f"Mijoz: {mijoz['ism']}\nTel: {mijoz.get('telefon','')}\n"
                        f"TG: @{mijoz.get('username','')}\nHolat: {blok}")
                kb = types.InlineKeyboardMarkup()
                if mijoz.get("bloklangan"):
                    kb.add(types.InlineKeyboardButton("Blokdan chiqarish", callback_data=f"UNBLK_{mijoz['user_id']}"))
                else:
                    kb.add(types.InlineKeyboardButton("Bloklash", callback_data=f"BLK_{mijoz['user_id']}"))
                if mijoz.get("user_id"):
                    kb.add(types.InlineKeyboardButton("Xabar yuborish", callback_data=f"XBYR_{mijoz['user_id']}"))
                bot.send_message(cid, matn, reply_markup=kb)
            if bron:
                tugash = tugash_sanasi(bron["sana"], bron["kunlar"])
                bot.send_message(cid,
                    f"Bron #{bron['id']}\n{bron['xona']}\n{bron['sana']}-{tugash}\n{bron['holat']}")
        else:
            bot.send_message(cid, f"'{text}' topilmadi")
        return

    if step == "ai_info":
        conn = get_db()
        conn.execute("INSERT INTO ai_info (matn,created_at) VALUES (?,?)",
                    (text, datetime.now().strftime("%d.%m.%Y %H:%M")))
        conn.commit()
        conn.close()
        bot.send_message(cid, f"AI ga qoshildi:\n{text}\n\nYana yozing yoki menyuga qayting.")
        return

    if step == "narx":
        try:
            narx = int(text.replace(" ", "").replace(",", ""))
            conn = get_db()
            conn.execute("UPDATE xonalar SET narx=? WHERE id=?", (narx, st["xid"]))
            conn.commit()
            conn.close()
            astate.pop(uid, None)
            bot.send_message(cid, f"Narx {format_narx(narx)} som ga ozgartirildi!", reply_markup=admin_kb(uid))
        except:
            bot.send_message(cid, "Raqam kiriting (masalan: 350000)")
        return

    if step == "yangi_bino":
        conn = get_db()
        conn.execute("INSERT INTO binolar (nomi) VALUES (?)", (text,))
        conn.commit()
        conn.close()
        astate.pop(uid, None)
        bot.send_message(cid, f"Yangi bino '{text}' yaratildi!", reply_markup=admin_kb(uid))
        return

    if step == "yangi_xona":
        try:
            parts = text.split(",")
            nomi, qavat, sigim, narx = parts[0].strip(), int(parts[1]), int(parts[2]), int(parts[3])
            bino_id = st["bino_id"]
            conn = get_db()
            conn.execute("INSERT INTO xonalar (bino_id,nomi,qavat,sigim,narx) VALUES (?,?,?,?,?)",
                        (bino_id, nomi, qavat, sigim, narx))
            conn.commit()
            conn.close()
            astate.pop(uid, None)
            bot.send_message(cid, f"Yangi xona '{nomi}' yaratildi!", reply_markup=admin_kb(uid))
        except:
            bot.send_message(cid, "Format: nom,qavat,joy_soni,narx")
        return

    if step == "add_admin":
        try:
            new_id = int(text)
            if new_id in DIRECTOR_IDS:
                bot.send_message(cid, "Bu director ID")
                return
            conn = get_db()
            conn.execute("INSERT OR REPLACE INTO adminlar (user_id,ism,qoshilgan) VALUES (?,?,?)",
                        (new_id, "Admin", datetime.now().strftime("%d.%m.%Y %H:%M")))
            conn.commit()
            conn.close()
            astate.pop(uid, None)
            bot.send_message(cid, f"{new_id} admin qilindi!", reply_markup=admin_kb(uid))
            try:
                bot.send_message(new_id, "Siz admin qilindingiz! /admin bosing.")
            except: pass
        except:
            bot.send_message(cid, "Faqat raqam kiriting")
        return

    if step == "xabar_yuborish":
        target = st.get("xabar_uid")
        if target:
            try:
                bot.send_message(target, f"Admin xabari:\n\n{text}")
                bot.send_message(cid, "Xabar yuborildi!", reply_markup=admin_kb(uid))
            except:
                bot.send_message(cid, "Yuborib bolmadi (bot bloklangan)")
        astate.pop(uid, None)
        return
