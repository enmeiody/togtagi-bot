from telebot import types
from datetime import datetime, timedelta
from io import BytesIO
from db import (get_db, get_xonalar, get_binolar, xona_band_mi, band_qil,
                bosh_qil_sana, bosh_qil_bron, bekor_qil_bron, get_bron,
                get_bron_xonalar, tugash_sanasi, format_narx, is_admin,
                is_director, bron_id_gen, qidir_mijoz, bugungi_stat,
                log_stat, hozirgi_mehmonlar, bugungi_keluvchilar,
                xonaga_joylashtir, chiqish_qil, xona_kun_holati, HOLAT_EMOJI)
from config import TELEFON1, DIRECTOR_IDS, TZ
import pytz
from keyboards import (admin_kb, binolar_kb, xonalar_admin_kb, xona_detail_kb,
                       sana_kb, kunlar_kb, xonalar_kb)


def register(bot):

    @bot.message_handler(commands=["admin"])
    def cmd_admin(msg):
        if not is_admin(msg.from_user.id):
            bot.send_message(msg.chat.id, "Ruxsat yoq")
            return
        # Admin kirsa bugungi holat ko'rinsin
        _bugungi_qisqa(bot, msg.chat.id, msg.from_user.id)
        bot.send_message(msg.chat.id, "Admin panel:", reply_markup=admin_kb(msg.from_user.id))

    # ===== ASOSIY TUGMALAR =====

    @bot.message_handler(func=lambda m: m.text == "🏢 Xonalar" and is_admin(m.from_user.id))
    def h_xonalar(msg):
        bot.send_message(msg.chat.id, "Binoni tanlang:", reply_markup=binolar_kb())
        if is_director(msg.from_user.id):
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("➕ Yangi bino", callback_data="YANGI_BINO"))
            bot.send_message(msg.chat.id, "Yangi bino:", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "📋 Bronlar" and is_admin(m.from_user.id))
    def h_bronlar(msg):
        bugun = datetime.now(TZ).date()
        oxiri = bugun + timedelta(days=10)
        conn = get_db()
        bronlar = conn.execute("SELECT * FROM bronlar WHERE holat != 'bekor' ORDER BY sana").fetchall()
        conn.close()
        keluvchi = [b for b in bronlar
                    if b["sana"] >= bugun.strftime("%d.%m.%Y")
                    and b["sana"] <= oxiri.strftime("%d.%m.%Y")]
        if not keluvchi:
            matn = "10 kunda bron yoq"
        else:
            matn = f"Kelayotgan 10 kunlik bronlar ({len(keluvchi)} ta):\n\n"
            for b in keluvchi:
                tugash = tugash_sanasi(b["sana"], b["kunlar"])
                h = "✅" if b["holat"] == "tasdiqlangan" else "⏳"
                matn += f"{h} #{b['id']} | {b['xona']}\n👤 {b['ism']} | 📞 {b['telefon']}\n📅 {b['sana']} - {tugash}\n\n"

        kb = types.InlineKeyboardMarkup(row_width=1)
        for b in keluvchi:
            h = "✅" if b["holat"] == "tasdiqlangan" else "⏳"
            kb.add(types.InlineKeyboardButton(
                f"{h} #{b['id']} - {b['ism']} ({b['sana']})",
                callback_data=f"BDET_{b['id']}"))
        kb.add(types.InlineKeyboardButton("📄 Barcha bronlar", callback_data="BARCHA_BRONLAR"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "BARCHA_BRONLAR")
    def cb_barcha_bronlar(call):
        if not is_admin(call.from_user.id): return
        conn = get_db()
        bronlar = conn.execute("SELECT * FROM bronlar ORDER BY created_at DESC LIMIT 30").fetchall()
        conn.close()
        kb = types.InlineKeyboardMarkup(row_width=1)
        for b in bronlar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            h = {"tasdiqlangan": "✅", "kutilmoqda": "⏳", "bekor": "❌"}.get(b["holat"], "❓")
            kb.add(types.InlineKeyboardButton(
                f"{h} #{b['id']} | {b['xona']} | {b['ism']} ({b['sana']})",
                callback_data=f"BDET_{b['id']}"))
        try:
            bot.edit_message_text(f"Barcha bronlar (oxirgi 30 ta):",
                                  call.message.chat.id, call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, "Barcha bronlar:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=lambda m: m.text == "📊 Bugungi holat" and is_admin(m.from_user.id))
    def h_bugungi(msg):
        _bugungi_tolik(bot, msg.chat.id, msg.from_user.id)

    @bot.message_handler(func=lambda m: m.text == "👥 Mehmonlar" and is_admin(m.from_user.id))
    def h_mehmonlar(msg):
        mehmonlar = hozirgi_mehmonlar()
        if not mehmonlar:
            bot.send_message(msg.chat.id, "Hozir hech kim yo'q", reply_markup=admin_kb(msg.from_user.id))
            return
        jami_kishi = sum(m["kishi"] for m in mehmonlar)
        matn = f"🏨 HOZIRGI MEHMONLAR\n{'─'*25}\n\n"
        matn += f"Jami: {len(mehmonlar)} xona | {jami_kishi} kishi\n\n"
        kb = types.InlineKeyboardMarkup(row_width=1)
        for m in mehmonlar:
            matn += f"🛏 {m['xona_nomi']}\n👤 {m['ism']} | 📞 {m['telefon']}\n"
            matn += f"👥 {m['kishi']} kishi | 📅 {m['sana']} - {m['tugash']}\n\n"
            kb.add(types.InlineKeyboardButton(
                f"🚪 {m['xona_nomi']} - {m['ism']} chiqdi",
                callback_data=f"CHIQISH_{m['id']}"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("CHIQISH_"))
    def cb_chiqish(call):
        if not is_admin(call.from_user.id): return
        jid = int(call.data.replace("CHIQISH_", ""))
        chiqish_qil(jid)
        bot.edit_message_text("✅ Chiqish qayd qilindi!", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Chiqdi!")

    @bot.message_handler(func=lambda m: m.text == "🏨 Qabulxona" and is_admin(m.from_user.id))
    def h_qabulxona(msg):
        _qabulxona_yuborish(bot, msg.chat.id, msg.from_user.id)

    @bot.callback_query_handler(func=lambda c: c.data == "QABUL_30KUN")
    def cb_qabul_30kun(call):
        if not is_admin(call.from_user.id): return
        _qabulxona_30kun(bot, call.message.chat.id, call.from_user.id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "QABUL_10KUN")
    def cb_qabul_10kun(call):
        if not is_admin(call.from_user.id): return
        _qabulxona_yuborish(bot, call.message.chat.id, call.from_user.id)
        bot.answer_callback_query(call.id)

    # ===== XONAGA JOYLASH =====

    @bot.message_handler(func=lambda m: m.text == "🏠 Xonaga joylash" and is_admin(m.from_user.id))
    def h_joylash(msg):
        _joylash_menyusi(bot, msg.chat.id, msg.from_user.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("JOYLA_BRON_"))
    def cb_joyla_bron(call):
        if not is_admin(call.from_user.id): return
        bid = call.data.replace("JOYLA_BRON_", "")
        b = get_bron(bid)
        if not b:
            bot.answer_callback_query(call.id, "Topilmadi")
            return
        # Xonalarni joylashtirildi deb belgilash
        xid_list = get_bron_xonalar(bid)
        for xid in xid_list:
            conn = get_db()
            xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
            conn.close()
            xonaga_joylashtir(xid, xnomi, b["ism"], b["telefon"], b["kishi"], b["sana"], b["kunlar"], bid)
        # Bron holatini yangilash
        conn = get_db()
        conn.execute("UPDATE bronlar SET holat='joylashgan' WHERE id=?", (bid,))
        conn.commit()
        conn.close()
        tugash = tugash_sanasi(b["sana"], b["kunlar"])
        bot.edit_message_text(
            f"✅ JOYLASHTIRILDI!\n\n🛏 {b['xona']}\n👤 {b['ism']}\n📞 {b['telefon']}\n"
            f"👥 {b['kishi']} kishi\n📅 {b['sana']} - {tugash}\n\n"
            f"Checkout: {tugash} soat 12:00",
            call.message.chat.id, call.message.message_id)
        if b["user_id"]:
            try:
                bot.send_message(b["user_id"],
                    f"Xush kelibsiz! 🏔\n\nXonangiz tayyor: {b['xona']}\n"
                    f"Checkout: {tugash} soat 12:00\n\n{TELEFON1}")
            except: pass
        bot.answer_callback_query(call.id, "Joylashtirildi!")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("JOYLA_YANGI_"))
    def cb_joyla_yangi(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("JOYLA_YANGI_", ""))
        from handlers.astate import astate
        conn = get_db()
        x = conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()
        conn.close()
        # Bugun joylashadi, faqat kishi va kun so'rash
        bugun = datetime.now(TZ).strftime("%d.%m.%Y")
        astate[call.from_user.id] = {
            "step": "joyla_kishi",
            "joyla_xid": xid,
            "joyla_xnomi": x["nomi"],
            "joyla_sana": bugun  # Avtomatik bugun
        }
        # Inline keyboard - raqamlarni bosish orqali
        kb = types.InlineKeyboardMarkup(row_width=5)
        btns = [types.InlineKeyboardButton(str(i), callback_data=f"JOYLA_KISHI_{xid}_{i}") for i in range(1, 11)]
        kb.add(*btns)
        xnomi_str = x["nomi"]
        joyla_matn = "Xona: " + xnomi_str + " | Bugun: " + bugun + "\n\nNechta kishi?"
        bot.send_message(call.message.chat.id, joyla_matn, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("JOYLA_KISHI_"))
    def cb_joyla_kishi(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        parts = call.data.split("_")
        xid = int(parts[2])
        n = int(parts[3])
        bugun = datetime.now(TZ).strftime("%d.%m.%Y")
        conn = get_db()
        x = conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()
        conn.close()
        astate[call.from_user.id] = {
            "step": "joyla_kun",
            "joyla_xid": xid,
            "joyla_xnomi": x["nomi"],
            "joyla_xona_ids": [xid],
            "joyla_sana": bugun,
            "joyla_kishi": n,
            "joyla_sigim": x["sigim"]
        }
        kb = types.InlineKeyboardMarkup(row_width=5)
        btns = [types.InlineKeyboardButton(str(i), callback_data=f"JOYLA_KUN_{xid}_{i}") for i in range(1, 16)]
        kb.add(*btns)
        # Agar kishi > sigim bo'lsa qo'shimcha xona tanlash imkoni
        if n > x["sigim"]:
            qolgan = n - x["sigim"]
            matn = f"Xona: {x['nomi']} ({x['sigim']}👤)\nHali {qolgan} kishi uchun qo'shimcha xona kerak.\n\nBugun necha kun turadi?"
        else:
            matn = "Xona: " + x["nomi"] + " | " + str(n) + " kishi\nNecha kun turadi?"
        bot.edit_message_text(matn, call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("JOYLA_KUN_"))
    def cb_joyla_kun(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        parts = call.data.split("_")
        xid = int(parts[2])
        kunlar = int(parts[3])
        st = astate.get(call.from_user.id, {})
        astate[call.from_user.id]["joyla_kunlar"] = kunlar
        astate[call.from_user.id]["step"] = "joyla_ism"
        sana = st.get("joyla_sana", datetime.now(TZ).strftime("%d.%m.%Y"))
        tugash = tugash_sanasi(sana, kunlar)
        # Bron tekshirish
        ogoh = ""
        from datetime import timedelta as td2
        conn = get_db()
        bosh_dt = datetime.strptime(sana, "%d.%m.%Y").date()
        for i in range(1, kunlar + 1):
            kun = (bosh_dt + td2(days=i)).strftime("%d.%m.%Y")
            row = conn.execute("SELECT bron_id FROM band WHERE xona_id=? AND sana=?", (xid, kun)).fetchone()
            if row and row["bron_id"]:
                b2 = conn.execute("SELECT ism FROM bronlar WHERE id=?", (row["bron_id"],)).fetchone()
                if b2:
                    ogoh += "  " + kun + " — #" + row["bron_id"] + " " + (b2["ism"] or "") + "\n"
        conn.close()
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        info = sana + " - " + tugash + " | " + str(kunlar) + " kun"
        if ogoh:
            info += "\n\nDiqqat! Keyingi kunlarda bron bor:\n" + ogoh
        info += "\n\nMijoz ismi:"
        bot.send_message(call.message.chat.id, info, reply_markup=kb)
        bot.answer_callback_query(call.id)

    # Bronlar bo'limidan joylash
    @bot.callback_query_handler(func=lambda c: c.data.startswith("BRON_JOYLA_"))
    def cb_bron_joyla(call):
        if not is_admin(call.from_user.id): return
        bid = call.data.replace("BRON_JOYLA_", "")
        b = get_bron(bid)
        if not b:
            bot.answer_callback_query(call.id, "Topilmadi")
            return
        xid_list = get_bron_xonalar(bid)
        for xid in xid_list:
            conn = get_db()
            xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
            conn.close()
            xonaga_joylashtir(xid, xnomi, b["ism"], b["telefon"], b["kishi"], b["sana"], b["kunlar"], bid)
        conn = get_db()
        conn.execute("UPDATE bronlar SET holat='joylashgan' WHERE id=?", (bid,))
        conn.commit()
        conn.close()
        tugash = tugash_sanasi(b["sana"], b["kunlar"])
        bot.edit_message_text(
            f"✅ Joylashtirildi!\n\n{b['xona']} | {b['ism']}\n{b['sana']} - {tugash}",
            call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Joylashtirildi!")

    # ===== MIJOZ QIDIRISH =====

    @bot.message_handler(func=lambda m: m.text == "👤 Mijoz qidirish" and is_admin(m.from_user.id))
    def h_mijoz_qidir(msg):
        from handlers.astate import astate
        astate[msg.from_user.id] = {"step": "mijoz_qidir"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(msg.chat.id, "Telefon, bron ID yoki username kiriting:", reply_markup=kb)

    # ===== TEZKOR BRON =====

    @bot.message_handler(func=lambda m: m.text == "➕ Tezkor bron" and is_admin(m.from_user.id))
    def h_tezkor(msg):
        from handlers.astate import astate
        astate[msg.from_user.id] = {"step": "tb_kishi", "ab": {}}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
        for i in range(1, 11):
            kb.add(str(i))
        kb.add("🔙 Admin menyu")
        bot.send_message(msg.chat.id, "Tezkor bron\nNechta kishi?", reply_markup=kb)

    # ===== GALEREYA =====

    @bot.message_handler(func=lambda m: m.text == "📸 Galereya" and is_admin(m.from_user.id))
    def h_galereya(msg):
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("📸 Umumiy rasmlar", callback_data="GAL_RASM"),
            types.InlineKeyboardButton("🎥 Videolar", callback_data="GAL_VIDEO"),
            types.InlineKeyboardButton("🖼 Greeting rasmi", callback_data="GAL_GREETING"),
        )
        bot.send_message(msg.chat.id, "Galereya:", reply_markup=kb)

    # ===== HISOBOT =====

    @bot.message_handler(func=lambda m: m.text == "📄 Hisobot" and is_admin(m.from_user.id))
    def h_hisobot(msg):
        conn = get_db()
        bronlar = conn.execute("SELECT * FROM bronlar ORDER BY created_at DESC").fetchall()
        conn.close()
        if not bronlar:
            bot.send_message(msg.chat.id, "Bron yoq")
            return
        matn = f"BARCHA BRONLAR\n{'='*40}\n\n"
        for b in bronlar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            matn += (f"#{b['id']} | {b['holat'].upper()}\n"
                     f"Ism: {b['ism']} | Tel: {b['telefon']}\n"
                     f"Sana: {b['sana']}-{tugash} | {b['kunlar']} kun\n"
                     f"Xona: {b['xona']} | Kishi: {b['kishi']}\n"
                     f"Narx: {format_narx(b['narx'])} som\n" + "-"*30 + "\n")
        buf = BytesIO(matn.encode("utf-8"))
        buf.name = "bronlar.txt"
        bot.send_document(msg.chat.id, buf, caption=f"Jami: {len(bronlar)} ta")

    # ===== AI MALUMOT =====

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

    # ===== IJTIMOIY TARMOQLAR =====

    @bot.message_handler(func=lambda m: m.text == "🔗 Ijtimoiy tarmoqlar" and is_admin(m.from_user.id))
    def h_ijtimoiy(msg):
        from db import get_ijtimoiy
        ijt = get_ijtimoiy()
        matn = "🔗 Ijtimoiy tarmoqlar:\n\n"
        for kalit, info in ijt.items():
            matn += f"{info['nomi']}: {info['link'] or 'qoshilmagan'}\n"
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("📱 Telegram", callback_data="IJT_telegram"),
            types.InlineKeyboardButton("📸 Instagram", callback_data="IJT_instagram"),
            types.InlineKeyboardButton("🎬 YouTube", callback_data="IJT_youtube"),
        )
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("IJT_"))
    def cb_ijt(call):
        if not is_admin(call.from_user.id): return
        kalit = call.data.replace("IJT_", "")
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": f"ijt_{kalit}"}
        nomlar = {"telegram": "Telegram", "instagram": "Instagram", "youtube": "YouTube"}
        bot.send_message(call.message.chat.id,
            f"{nomlar[kalit]} linkini kiriting:\nMisol: https://t.me/togtagi_resort")
        bot.answer_callback_query(call.id)

    # ===== STATISTIKA =====

    @bot.message_handler(func=lambda m: m.text == "📊 Statistika" and is_director(m.from_user.id))
    def h_stat(msg):
        from db import kengaytirilgan_stat
        stat = kengaytirilgan_stat()
        bugun = datetime.now(TZ).strftime("%d.%m.%Y")
        matn = f"📊 STATISTIKA\n{'='*28}\n\n"
        matn += f"👥 Foydalanuvchilar:\n  Bugun: {stat['bugun']} | Hafta: {stat['hafta']} | Oy: {stat['oy']} | Jami: {stat['jami_mijozlar']}\n\n"
        matn += f"🎫 Bronlar: Jami {stat['jami_bronlar']} | Tasdiqlangan {stat['tasdiq_bronlar']}\n\n"
        matn += "📈 Top harakatlar:\n"
        for h in stat["harakatlar"][:8]:
            matn += f"  {h['harakat']}: {h['c']}\n"
        matn += "\n⏰ Faol vaqtlar:\n"
        for s in stat["soatlar"]:
            if s["soat"] and s["c"] > 2:
                bar = "█" * min(s["c"], 10)
                matn += f"  {s['soat']}:00 {bar} {s['c']}\n"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📄 TXT hisobot", callback_data="STAT_TXT"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "STAT_TXT")
    def cb_stat_txt(call):
        if not is_director(call.from_user.id): return
        from db import kengaytirilgan_stat
        stat = kengaytirilgan_stat()
        conn = get_db()
        bronlar = conn.execute("SELECT * FROM bronlar ORDER BY created_at DESC LIMIT 50").fetchall()
        mijozlar = conn.execute("SELECT * FROM mijozlar ORDER BY last_active DESC LIMIT 50").fetchall()
        conn.close()
        matn = f"STATISTIKA HISOBOTI\n{datetime.now().strftime('%d.%m.%Y %H:%M')}\n{'='*40}\n\n"
        matn += f"FOYDALANUVCHILAR: Bugun {stat['bugun']} | Hafta {stat['hafta']} | Oy {stat['oy']} | Jami {stat['jami_mijozlar']}\n"
        matn += f"BRONLAR: Jami {stat['jami_bronlar']} | Tasdiqlangan {stat['tasdiq_bronlar']}\n\n"
        matn += "TOP HARAKATLAR:\n"
        for h in stat["harakatlar"]:
            matn += f"  {h['harakat']}: {h['c']} marta\n"
        matn += "\nMIJOZLAR BAZASI:\n" + "="*40 + "\n"
        for m in mijozlar:
            tel = m["telefon"] or ""
            uname = m.get("username") or ""
            matn += f"{m['ism']} | {tel} | @{uname} | {m.get('last_active','')}\n"
        matn += "\nSO'NGGI BRONLAR:\n" + "="*40 + "\n"
        for b in bronlar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            matn += f"#{b['id']} | {b['ism']} | {b['telefon']} | {b['sana']}-{tugash} | {b['holat']}\n"
        buf = BytesIO(matn.encode("utf-8"))
        buf.name = f"hisobot_{datetime.now().strftime('%d%m%Y')}.txt"
        bot.send_document(call.message.chat.id, buf, caption="📄 To'liq hisobot")
        bot.answer_callback_query(call.id)

    # ===== ADMINLAR =====

    @bot.message_handler(func=lambda m: m.text == "👮 Adminlar" and is_director(m.from_user.id))
    def h_adminlar(msg):
        conn = get_db()
        adminlar = conn.execute("SELECT * FROM adminlar").fetchall()
        conn.close()
        matn = "Adminlar:\n\n"
        for a in adminlar:
            matn += f"ID: {a['user_id']} | {a['ism'] or 'Admin'}\n"
        matn += f"\nDirectorlar: {', '.join(str(d) for d in DIRECTOR_IDS)}"
        kb = types.InlineKeyboardMarkup(row_width=1)
        for a in adminlar:
            kb.add(types.InlineKeyboardButton(f"Del: {a['ism'] or a['user_id']}", callback_data=f"DEL_ADM_{a['user_id']}"))
        kb.add(types.InlineKeyboardButton("➕ Admin qoshish", callback_data="ADD_ADM"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    # ===== MENYU NAVIGATSIYA =====

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

    # ===== XONA CALLBACKLARI =====

    @bot.callback_query_handler(func=lambda c: c.data.startswith("BINO_"))
    def cb_bino(call):
        if not is_admin(call.from_user.id): return
        bino_id = int(call.data.replace("BINO_", ""))
        conn = get_db()
        bino = conn.execute("SELECT * FROM binolar WHERE id=?", (bino_id,)).fetchone()
        conn.close()
        kb = xonalar_admin_kb(bino_id)
        if is_director(call.from_user.id):
            kb.add(types.InlineKeyboardButton(f"➕ Yangi xona", callback_data=f"YANGI_XONA_{bino_id}"))
        try:
            bot.edit_message_text(f"🏢 {bino['nomi']}:", call.message.chat.id, call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, f"🏢 {bino['nomi']}:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AX_") and
        not any(c.data.startswith(p) for p in ["AXB_","AXBAND_","AXBOSH_","AXRASM_","AXVIDEO_","AXNARX_"]))
    def cb_ax(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AX_", ""))
        conn = get_db()
        x = conn.execute("SELECT x.*, COALESCE(b.nomi,'1-bino') as bino_nomi FROM xonalar x LEFT JOIN binolar b ON x.bino_id=b.id WHERE x.id=?", (xid,)).fetchone()
        rasmlar = conn.execute("SELECT COUNT(*) as c FROM xona_media WHERE xona_id=? AND tur='photo'", (xid,)).fetchone()["c"]
        conn.close()
        bugun = datetime.now(TZ).strftime("%d.%m.%Y")
        _hol = xona_kun_holati(xid, bugun)
        h = HOLAT_EMOJI[_hol] + " " + {"bosh":"Bosh","band":"Band","joylashgan":"Ichida","chiqish":"Chiqmoqda"}[_hol]
        yopiq = dict(x).get("yopiq", 0)
        yopiq_txt = " | 🔒 Yopiq" if yopiq else ""
        matn = (f"{x['nomi']} | {x['bino_nomi']}\n"
                f"Qavat: {x['qavat']} | Joy: {x['sigim']}👤\n"
                f"Narx: {format_narx(x['narx'])} som\n"
                f"Bugun: {h}{yopiq_txt} | 📸 {rasmlar}")
        try:
            bot.edit_message_text(matn, call.message.chat.id, call.message.message_id, reply_markup=xona_detail_kb(xid, x["bino_id"], yopiq))
        except:
            bot.send_message(call.message.chat.id, matn, reply_markup=xona_detail_kb(xid, x["bino_id"], yopiq))
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXB_"))
    def cb_axb(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AXB_", ""))
        conn = get_db()
        xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
        bids = conn.execute("SELECT DISTINCT bron_id FROM bron_xonalar WHERE xona_id=?", (xid,)).fetchall()
        bronlar = []
        for r in bids:
            b = conn.execute("SELECT * FROM bronlar WHERE id=? AND holat NOT IN ('bekor')", (r["bron_id"],)).fetchone()
            if b: bronlar.append(b)
        conn.close()
        matn = f"{xnomi} bronlari:\n\n"
        kb = types.InlineKeyboardMarkup(row_width=1)
        for b in bronlar[-8:]:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            h = {"tasdiqlangan": "✅", "kutilmoqda": "⏳", "joylashgan": "🏠"}.get(b["holat"], "❓")
            matn += f"{h} #{b['id']} | {b['sana']}-{tugash}\n{b['ism']} | {b['telefon']}\n\n"
            kb.add(types.InlineKeyboardButton(f"{h} #{b['id']} - {b['ism']}", callback_data=f"BDET_{b['id']}"))
        bugun = datetime.now(TZ).date()
        matn += "15 kunlik:\n"
        for i in range(15):
            kun = bugun + timedelta(days=i)
            h = "🔴" if xona_band_mi(xid, kun.strftime("%d.%m.%Y")) else "🟢"
            matn += f"{h}{kun.strftime('%d/%m')} "
            if (i+1) % 5 == 0: matn += "\n"
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
        holat_emoji = {"tasdiqlangan": "✅", "kutilmoqda": "⏳", "bekor": "❌", "joylashgan": "🏠"}.get(b["holat"], "❓")
        matn = (f"Bron #{b['id']} {holat_emoji}\n\n"
                f"👤 {b['ism']}\n📞 {b['telefon']}\n"
                f"🛏 {b['xona']}\n📅 {b['sana']} - {tugash}\n"
                f"🌙 {b['kunlar']} kun | 👥 {b['kishi']} kishi\n"
                f"💰 {format_narx(b['narx'])} som\n"
                f"Holat: {b['holat']}")
        kb = types.InlineKeyboardMarkup(row_width=2)
        if b["holat"] == "kutilmoqda":
            kb.add(
                types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ATASDIQ_ha_{bid}"),
                types.InlineKeyboardButton("❌ Rad etish", callback_data=f"ATASDIQ_yoq_{bid}"))
        if b["holat"] in ["kutilmoqda", "tasdiqlangan"]:
            kb.add(types.InlineKeyboardButton("🏠 Xonaga joylash", callback_data=f"BRON_JOYLA_{bid}"))
        if b["holat"] != "bekor":
            kb.add(
                types.InlineKeyboardButton("✏️ O'zgartirish", callback_data=f"BRON_OZGARTIR_{bid}"),
                types.InlineKeyboardButton("🗑 Bekor qilish", callback_data=f"ABEKOR_{bid}"))
        try:
            bot.edit_message_text(matn, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, matn, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("BRON_OZGARTIR_"))
    def cb_bron_ozgartir(call):
        if not is_admin(call.from_user.id): return
        bid = call.data.replace("BRON_OZGARTIR_", "")
        b = get_bron(bid)
        if not b: return
        # Eski bronni bekor qilamiz va tezkor bron jarayonini boshlaymiz
        bekor_qil_bron(bid)
        from handlers.astate import astate
        astate[call.from_user.id] = {
            "step": "tb_kishi",
            "ab": {
                "ism": b["ism"],
                "telefon": b["telefon"],
            }
        }
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
        for i in range(1, 11): kb.add(str(i))
        kb.add("🔙 Admin menyu")
        tugash = tugash_sanasi(b["sana"], b["kunlar"])
        matn_rebron = (f"Qayta bron qilish\n\n"
                       f"Eski bron #{bid} bekor qilindi.\n"
                       f"Ism: {b['ism']} | Tel: {b['telefon']}\n\n"
                       f"Nechta kishi? (avval {b['kishi']} kishi edi)")
        bot.send_message(call.message.chat.id, matn_rebron, reply_markup=kb)
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
                    bot.send_message(b["user_id"],
                        f"✅ Broningiz tasdiqlandi!\n\n🛏 {b['xona']}\n📅 {b['sana']} - {tugash}\n"
                        f"👥 {b['kishi']} kishi\n💰 {format_narx(b['narx'])} som\n\n"
                        f"Kelishingizni kutamiz! {TELEFON1}")
                except: pass
            bot.edit_message_text(f"✅ Bron #{bid} TASDIQLANDI", call.message.chat.id, call.message.message_id)
        else:
            bekor_qil_bron(bid)
            if b["user_id"]:
                try:
                    bot.send_message(b["user_id"], f"❌ Bron #{bid} rad etildi.\n{TELEFON1}")
                except: pass
            bot.edit_message_text(f"❌ Bron #{bid} RAD ETILDI", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ABEKOR_"))
    def cb_abekor(call):
        if not is_admin(call.from_user.id): return
        bid = call.data.replace("ABEKOR_", "")
        b = get_bron(bid)
        bekor_qil_bron(bid)
        if b and b["user_id"]:
            try:
                bot.send_message(b["user_id"], f"❌ Bron #{bid} bekor qilindi.\n{TELEFON1}")
            except: pass
        bot.edit_message_text(f"Bron #{bid} bekor qilindi", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXBAND_"))
    def cb_axband(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AXBAND_", ""))
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "band_sana", "xid": xid}
        bot.send_message(call.message.chat.id, "Sana tanlang:", reply_markup=sana_kb())
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXBOSH_"))
    def cb_axbosh(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AXBOSH_", ""))
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "bosh_sana", "xid": xid}
        bot.send_message(call.message.chat.id, "Sana tanlang:", reply_markup=sana_kb())
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
        bot.send_message(call.message.chat.id, f"{xnomi} rasmlari ({len(rasmlar)} ta):", reply_markup=kb)
        if rasmlar:
            try:
                media = [types.InputMediaPhoto(rasmlar[0]["file_id"])]
                for r in rasmlar[1:5]:
                    media.append(types.InputMediaPhoto(r["file_id"]))
                bot.send_media_group(call.message.chat.id, media)
            except: pass
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("XONA_YOPIQ_"))
    def cb_xona_yopiq(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("XONA_YOPIQ_", ""))
        conn = get_db()
        conn.execute("UPDATE xonalar SET yopiq=1 WHERE id=?", (xid,))
        xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, f"{xnomi} yopildi!")
        bot.send_message(call.message.chat.id, f"🔒 {xnomi} brondan yopildi.", reply_markup=admin_kb(call.from_user.id))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("XONA_OCHIQ_"))
    def cb_xona_ochiq(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("XONA_OCHIQ_", ""))
        conn = get_db()
        conn.execute("UPDATE xonalar SET yopiq=0 WHERE id=?", (xid,))
        xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, f"{xnomi} ochildi!")
        bot.send_message(call.message.chat.id, f"🔓 {xnomi} brondan ochildi.", reply_markup=admin_kb(call.from_user.id))

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
        bot.send_message(call.message.chat.id, "Format: nom,qavat,joy_soni,narx\nMisol: 11-xona,1,3,300000")
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
        try:
            bot.edit_message_text(f"Umumiy rasmlar ({len(rasmlar)} ta):", call.message.chat.id, call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, f"Umumiy rasmlar ({len(rasmlar)} ta):", reply_markup=kb)
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
        try:
            bot.edit_message_text(f"Videolar ({len(videolar)} ta):", call.message.chat.id, call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, f"Videolar ({len(videolar)} ta):", reply_markup=kb)
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
        try: bot.send_message(uid, "Admin huquqingiz bekor qilindi.")
        except: pass
        bot.answer_callback_query(call.id)

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

    @bot.callback_query_handler(func=lambda c: c.data.startswith("TBXT_") and not c.data.startswith("TBXT_QOSH_") and not c.data.startswith("TBXT_TASDIQ"))
    def cb_tbxt(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        xid = int(call.data.replace("TBXT_", ""))
        conn = get_db()
        x = conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()
        conn.close()
        st = astate.get(call.from_user.id, {})
        kunlar = st["ab"].get("kunlar", 1)
        kishi = st["ab"].get("kishi", 1)
        sana = st["ab"].get("sana", "")

        # Tanlangan xonalar ro'yxatini boshlash
        st["ab"]["xona_ids"] = [xid]
        st["ab"]["xona_nomi"] = x["nomi"]
        st["ab"]["narx"] = x["narx"] * kunlar
        jami_sigim = x["sigim"]
        astate[call.from_user.id] = st

        # Agar kishi soni xona sigimidan katta bo'lsa — yana xona qo'shish imkoni
        if jami_sigim < kishi:
            qolgan = kishi - jami_sigim
            matn = f"Tanlandi: {x['nomi']} ({x['sigim']}👤)\n"
            matn += f"Hali {qolgan} kishi uchun joy kerak.\n\nQo'shimcha xona tanlang yoki tasdiqlang:"
            # Bo'sh xonalarni ko'rsat
            from db import xona_kunlar_band
            kb = types.InlineKeyboardMarkup(row_width=1)
            for xb in get_xonalar():
                if xb["id"] == xid: continue
                if xona_kunlar_band(xb["id"], sana, kunlar): continue
                narx = format_narx(xb["narx"] * kunlar)
                kb.add(types.InlineKeyboardButton(
                    f"➕ {xb['nomi']} ({xb['sigim']}👤) — {narx}",
                    callback_data=f"TBXT_QOSH_{xb['id']}"))
            kb.add(types.InlineKeyboardButton(
                f"✅ Shu bilan davom etish ({jami_sigim}👤, +{kishi-jami_sigim} ortiqcha)",
                callback_data="TBXT_TASDIQ"))
            bot.edit_message_text(matn, call.message.chat.id, call.message.message_id, reply_markup=kb)
        else:
            st["step"] = "tb_ism"
            astate[call.from_user.id] = st
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("🔙 Admin menyu")
            bot.send_message(call.message.chat.id,
                f"Tanlandi: {x['nomi']}\n{sana} | {kunlar} kun\nNarx: {format_narx(st['ab']['narx'])} som\n\nMijoz ismi:",
                reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("TBXT_QOSH_"))
    def cb_tbxt_qosh(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        xid = int(call.data.replace("TBXT_QOSH_", ""))
        conn = get_db()
        x = conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()
        conn.close()
        st = astate.get(call.from_user.id, {})
        kunlar = st["ab"].get("kunlar", 1)
        kishi = st["ab"].get("kishi", 1)
        sana = st["ab"].get("sana", "")

        # Xonani qo'shish
        st["ab"]["xona_ids"].append(xid)
        st["ab"]["xona_nomi"] += " + " + x["nomi"]
        st["ab"]["narx"] += x["narx"] * kunlar
        jami_sigim = sum(
            conn2.execute("SELECT sigim FROM xonalar WHERE id=?", (xid2,)).fetchone()["sigim"]
            for xid2 in st["ab"]["xona_ids"]
            for conn2 in [get_db()]
        )
        astate[call.from_user.id] = st

        if jami_sigim < kishi:
            qolgan = kishi - jami_sigim
            matn = f"Tanlandi: {st['ab']['xona_nomi']}\nJami: {jami_sigim}👤\nHali {qolgan} kishi uchun joy kerak.\n\nQo'shimcha xona:"
            from db import xona_kunlar_band
            kb = types.InlineKeyboardMarkup(row_width=1)
            for xb in get_xonalar():
                if xb["id"] in st["ab"]["xona_ids"]: continue
                if xona_kunlar_band(xb["id"], sana, kunlar): continue
                narx = format_narx(xb["narx"] * kunlar)
                kb.add(types.InlineKeyboardButton(
                    f"➕ {xb['nomi']} ({xb['sigim']}👤) — {narx}",
                    callback_data=f"TBXT_QOSH_{xb['id']}"))
            kb.add(types.InlineKeyboardButton(
                f"✅ Davom etish ({jami_sigim}👤)",
                callback_data="TBXT_TASDIQ"))
            bot.edit_message_text(matn, call.message.chat.id, call.message.message_id, reply_markup=kb)
        else:
            # Yetarli
            st["step"] = "tb_ism"
            astate[call.from_user.id] = st
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("🔙 Admin menyu")
            bot.send_message(call.message.chat.id,
                f"Tanlandi: {st['ab']['xona_nomi']}\n{sana} | {kunlar} kun\nNarx: {format_narx(st['ab']['narx'])} som\n\nMijoz ismi:",
                reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "TBXT_TASDIQ")
    def cb_tbxt_tasdiq(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        st = astate.get(call.from_user.id, {})
        sana = st["ab"].get("sana", "")
        kunlar = st["ab"].get("kunlar", 1)
        st["step"] = "tb_ism"
        astate[call.from_user.id] = st
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(call.message.chat.id,
            f"Tanlandi: {st['ab']['xona_nomi']}\n{sana} | {kunlar} kun\nNarx: {format_narx(st['ab']['narx'])} som\n\nMijoz ismi:",
            reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "TB_BARCHASI")
    def cb_tb_barchasi(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        st = astate.get(call.from_user.id, {})
        sana = st["ab"].get("sana", "")
        kunlar = st["ab"].get("kunlar", 1)
        kb_orig = xonalar_kb(sana, kunlar)
        new_kb = types.InlineKeyboardMarkup(row_width=1)
        for row in kb_orig.keyboard:
            for btn in row:
                if btn.callback_data and btn.callback_data.startswith("XT_"):
                    xid = btn.callback_data.split("_")[1]
                    new_kb.add(types.InlineKeyboardButton(btn.text, callback_data=f"TBXT_{xid}"))
        bot.edit_message_text("Barcha bosh xonalar:", call.message.chat.id, call.message.message_id, reply_markup=new_kb)
        bot.answer_callback_query(call.id)

    # Media handlers
    @bot.message_handler(content_types=["photo"])
    def h_photo(msg):
        if not is_admin(msg.from_user.id): return
        from handlers.astate import astate
        st = astate.get(msg.from_user.id, {})
        step = st.get("step")
        file_id = msg.photo[-1].file_id
        conn = get_db()
        if step == "xona_rasm":
            conn.execute("INSERT INTO xona_media (xona_id,tur,file_id) VALUES (?,?,?)", (st["xid"], "photo", file_id))
            cnt = conn.execute("SELECT COUNT(*) as c FROM xona_media WHERE xona_id=? AND tur='photo'", (st["xid"],)).fetchone()["c"]
            conn.commit(); conn.close()
            bot.send_message(msg.chat.id, f"Saqlandi! Jami: {cnt} ta\n/done - tugallash")
        elif step == "umumiy_rasm":
            conn.execute("INSERT INTO umumiy_media (tur,file_id) VALUES (?,?)", ("photo", file_id))
            cnt = conn.execute("SELECT COUNT(*) as c FROM umumiy_media WHERE tur='photo'").fetchone()["c"]
            conn.commit(); conn.close()
            bot.send_message(msg.chat.id, f"Saqlandi! Jami: {cnt} ta\n/done - tugallash")
        elif step == "greeting":
            conn.execute("DELETE FROM greeting_media")
            conn.execute("INSERT INTO greeting_media (id,file_id,tur) VALUES (1,?,?)", (file_id, "photo"))
            conn.commit(); conn.close()
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
            conn.execute("INSERT INTO xona_media (xona_id,tur,file_id) VALUES (?,?,?)", (st["xid"], "video", file_id))
            cnt = conn.execute("SELECT COUNT(*) as c FROM xona_media WHERE xona_id=? AND tur='video'", (st["xid"],)).fetchone()["c"]
            conn.commit(); conn.close()
            bot.send_message(msg.chat.id, f"Video saqlandi! Jami: {cnt} ta\n/done - tugallash")
        elif step == "umumiy_video":
            conn.execute("INSERT INTO umumiy_media (tur,file_id) VALUES (?,?)", ("video", file_id))
            cnt = conn.execute("SELECT COUNT(*) as c FROM umumiy_media WHERE tur='video'").fetchone()["c"]
            conn.commit(); conn.close()
            bot.send_message(msg.chat.id, f"Video saqlandi! Jami: {cnt} ta\n/done - tugallash")
        else:
            conn.close()

    @bot.message_handler(commands=["done"])
    def cmd_done(msg):
        if not is_admin(msg.from_user.id): return
        from handlers.astate import astate
        astate.pop(msg.from_user.id, None)
        bot.send_message(msg.chat.id, "Saqlandi!", reply_markup=admin_kb(msg.from_user.id))


# ===== YORDAMCHI FUNKSIYALAR =====

def _joylash_menyusi(bot, cid, uid):
    bugun = datetime.now(TZ).strftime("%d.%m.%Y")
    keluvchilar = bugungi_keluvchilar()
    bosh_list = [x for x in get_xonalar() if not xona_band_mi(x["id"], bugun) and not dict(x).get("yopiq", 0)]
    hozirgilar = hozirgi_mehmonlar()

    matn = "🏠 XONAGA JOYLASH\n" + "─"*25 + "\n\n"

    if hozirgilar:
        matn += f"🏨 Hozir {len(hozirgilar)} ta xonada mehmon bor\n\n"

    kb = types.InlineKeyboardMarkup(row_width=1)

    if keluvchilar:
        matn += f"📋 Bugun keluvchi bronlar ({len(keluvchilar)} ta):\n\n"
        for b in keluvchilar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            matn += f"#{b['id']} | {b['xona']}\n👤 {b['ism']} | 👥 {b['kishi']} kishi\n📅 {b['sana']}-{tugash}\n\n"
            kb.add(types.InlineKeyboardButton(
                f"✅ #{b['id']} - {b['ism']} - Joylash",
                callback_data=f"JOYLA_BRON_{b['id']}"))

    if bosh_list:
        matn += f"\n🟢 Bo'sh xonalar ({len(bosh_list)} ta):\n"
        for x in bosh_list:
            q = "🏠" if x["qavat"] == 1 else "🏢"
            matn += f"  {q} {x['nomi']} ({x['sigim']}👤)\n"
            kb.add(types.InlineKeyboardButton(
                f"🟢 {x['nomi']} ({x['sigim']}👤) - Yangi joylash",
                callback_data=f"JOYLA_YANGI_{x['id']}"))
    else:
        matn += "\n❌ Hozir barcha xonalar band"

    bot.send_message(cid, matn, reply_markup=kb)


def _bugungi_qisqa(bot, cid, uid):
    bugun = datetime.now(TZ).strftime("%d.%m.%Y")
    mehmonlar = hozirgi_mehmonlar()
    keluvchilar = bugungi_keluvchilar()
    bosh_list = [x for x in get_xonalar() if not xona_band_mi(x["id"], bugun)]

    matn = f"📊 Bugun {bugun}:\n"
    matn += f"🏨 Mehmonlar: {len(mehmonlar)} xona\n"
    matn += f"📋 Bugun keluvchi: {len(keluvchilar)} bron\n"
    matn += f"🟢 Bo'sh xonalar: {len(bosh_list)} ta"
    bot.send_message(cid, matn)


def _bugungi_tolik(bot, cid, uid):
    bugun = datetime.now(TZ).strftime("%d.%m.%Y")
    matn = f"📊 BUGUNGI HOLAT — {bugun}\n{'─'*28}\n\n"
    conn = get_db()
    for b in get_binolar():
        matn += f"🏢 {b['nomi']}:\n"
        for x in get_xonalar(b["id"]):
            h = "🔴" if xona_band_mi(x["id"], bugun) else "🟢"
            info = ""
            if xona_band_mi(x["id"], bugun):
                brow = conn.execute("SELECT bron_id FROM band WHERE xona_id=? AND sana=?", (x["id"], bugun)).fetchone()
                if brow and brow["bron_id"] not in ("admin", None) and not brow["bron_id"].startswith("joylashgan"):
                    bron = conn.execute("SELECT * FROM bronlar WHERE id=?", (brow["bron_id"],)).fetchone()
                    if bron:
                        tugash = tugash_sanasi(bron["sana"], bron["kunlar"])
                        info = f" → {bron['ism']} ({bron['kishi']}👤) -{tugash}"
            yopiq = " 🔒" if dict(x).get("yopiq", 0) else ""
            matn += f"  {h} {x['nomi']}({x['sigim']}👤){yopiq}{info}\n"
        matn += "\n"
    conn.close()
    bot.send_message(cid, matn, reply_markup=admin_kb(uid))


def admin_matn_handler(bot, msg, uid, text, astate):
    st = astate.get(uid, {})
    step = st.get("step")
    cid = msg.chat.id

    if step == "joyla_kishi":
        try:
            n = int(text)
            st["joyla_kishi"] = n
            st["step"] = "joyla_kun"
            astate[uid] = st
            bot.send_message(cid, f"{n} kishi\nNecha kun turadi?", reply_markup=kunlar_kb())
        except:
            bot.send_message(cid, "Raqam kiriting")
        return

    if step == "joyla_tel":
        from db import xonaga_joylashtir as xj
        xid = st["joyla_xid"]
        xnomi = st["joyla_xnomi"]
        kishi = st.get("joyla_kishi", 1)
        sana = st.get("joyla_sana", datetime.now(TZ).strftime("%d.%m.%Y"))
        kunlar = st.get("joyla_kunlar", 1)
        xj(xid, xnomi, st["joyla_ism"], text, kishi, sana, kunlar)
        astate.pop(uid, None)
        tugash = tugash_sanasi(sana, kunlar)
        bot.send_message(cid,
            f"✅ Joylashtirildi!\n\n🛏 {xnomi}\n👤 {st['joyla_ism']} | 📞 {text}\n"
            f"👥 {kishi} kishi\n📅 {sana} - {tugash}",
            reply_markup=admin_kb(uid))
        return

    if step == "joyla_ism":
        st["joyla_ism"] = text
        st["step"] = "joyla_tel"
        astate[uid] = st
        bot.send_message(cid, "Telefon raqami:")
        return

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
        conn.execute("""INSERT INTO bronlar (id,ism,telefon,sana,kunlar,kishi,xona,narx,holat,user_id,username,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (bid, ab["ism"], text, ab["sana"], ab["kunlar"], ab["kishi"],
             ab["xona_nomi"], ab["narx"], "tasdiqlangan",
             DIRECTOR_IDS[0], "admin", datetime.now().strftime("%d.%m.%Y %H:%M")))
        for xid in ab["xona_ids"]:
            conn.execute("INSERT OR IGNORE INTO bron_xonalar VALUES (?,?)", (bid, xid))
        conn.commit(); conn.close()
        for xid in ab["xona_ids"]:
            band_qil(xid, ab["sana"], ab["kunlar"], bid)
        havola = f"t.me/togtagi_bot?start=bron_{bid}"
        bot.send_message(cid,
            f"✅ Bron #{bid} qoshildi!\n{ab['xona_nomi']} | {ab['sana']}-{tugash}\n"
            f"{format_narx(ab['narx'])} som\n\nMijozga yuboring:\n{havola}",
            reply_markup=admin_kb(uid))
        try:
            conn2 = get_db()
            all_m = conn2.execute("SELECT * FROM mijozlar").fetchall()
            conn2.close()
            for mm in all_m:
                if mm["telefon"] and str(mm["telefon"])[-9:] == text[-9:] and mm["user_id"]:
                    bot.send_message(mm["user_id"],
                        f"Broningiz tasdiqlandi! #{bid}\n{ab['xona_nomi']}\n{ab['sana']}-{tugash}\n{format_narx(ab['narx'])} som")
                    break
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
                matn = (f"👤 {mijoz['ism']}\n📞 {mijoz.get('telefon','')}\n"
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
                bot.send_message(cid, f"#{bron['id']} | {bron['xona']}\n{bron['sana']}-{tugash} | {bron['holat']}")
        else:
            bot.send_message(cid, f"'{text}' topilmadi")
        return

    if step == "ai_info":
        conn = get_db()
        conn.execute("INSERT INTO ai_info (matn,created_at) VALUES (?,?)",
                    (text, datetime.now().strftime("%d.%m.%Y %H:%M")))
        conn.commit(); conn.close()
        bot.send_message(cid, f"AI ga qoshildi:\n{text}")
        return

    if step == "narx":
        try:
            narx = int(text.replace(" ", "").replace(",", ""))
            conn = get_db()
            conn.execute("UPDATE xonalar SET narx=? WHERE id=?", (narx, st["xid"]))
            conn.commit(); conn.close()
            astate.pop(uid, None)
            bot.send_message(cid, f"Narx {format_narx(narx)} som ga ozgartirildi!", reply_markup=admin_kb(uid))
        except:
            bot.send_message(cid, "Raqam kiriting")
        return

    if step == "yangi_bino":
        conn = get_db()
        conn.execute("INSERT INTO binolar (nomi) VALUES (?)", (text,))
        conn.commit(); conn.close()
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
            conn.commit(); conn.close()
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
            conn.commit(); conn.close()
            astate.pop(uid, None)
            bot.send_message(cid, f"{new_id} admin qilindi!", reply_markup=admin_kb(uid))
            try: bot.send_message(new_id, "Siz admin qilindingiz! /admin bosing.")
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
                bot.send_message(cid, "Yuborib bolmadi")
        astate.pop(uid, None)
        return

    if step and step.startswith("ijt_"):
        from db import set_ijtimoiy
        set_ijtimoiy(step.replace("ijt_", ""), text)
        astate.pop(uid, None)
        bot.send_message(cid, f"✅ Link saqlandi:\n{text}", reply_markup=admin_kb(uid))
        return

    if step == "ozg_kishi":
        try:
            n = int(text)
            conn = get_db()
            conn.execute("UPDATE bronlar SET kishi=? WHERE id=?", (n, st["bron_id"]))
            conn.commit(); conn.close()
            astate.pop(uid, None)
            bot.send_message(cid, f"✅ Kishi soni {n} ga o'zgartirildi!", reply_markup=admin_kb(uid))
        except:
            bot.send_message(cid, "Raqam kiriting")
        return


def _qabulxona_yuborish(bot, cid, uid):
    """10 kunlik Qabulxona — chiroyli dizayn"""
    bugun = datetime.now(TZ).date()
    kunlar_list = [(bugun + timedelta(days=i)) for i in range(10)]
    mehmonlar = hozirgi_mehmonlar()
    keluvchilar = bugungi_keluvchilar()

    # Yuqori qism — bugungi holat
    matn = "🏨 QABULXONA\n"
    matn += "━" * 28 + "\n\n"

    # Bugungi mehmonlar
    matn += f"👥 Hozir: {len(mehmonlar)} xona band"
    if mehmonlar:
        ketuvchilar = [m for m in mehmonlar if m["tugash"] == bugun.strftime("%d.%m.%Y")]
        if ketuvchilar:
            matn += f" | {len(ketuvchilar)} ta bugun ketadi"
    matn += "\n"
    matn += f"📋 Bugun keluvchi: {len(keluvchilar)} bron\n\n"

    # 10 kunlik jadval
    matn += "📅 10 KUNLIK HOLAT\n"
    matn += "─" * 28 + "\n"

    # Sanalar qatori
    matn += "Xona  "
    for kun in kunlar_list:
        matn += kun.strftime("%d").rjust(2) + " "
    matn += "\n" + "─" * 28 + "\n"

    for x in get_xonalar():
        nom = x["nomi"].replace("-xona", "")
        satri = f"{nom:<5} "
        for kun in kunlar_list:
            h = xona_kun_holati(x["id"], kun.strftime("%d.%m.%Y"))
            satri += HOLAT_EMOJI[h] + " "
        matn += satri + "\n"

    matn += "─" * 28 + "\n"
    matn += "🟢 Bosh  🔴 Band  🔵 Ichida  🟡 Bugun chiqadi\n"
    matn += " ".join(k.strftime("%d/%m") for k in kunlar_list)

    # Tugmalar — xonalar 2 qatorda
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for x in get_xonalar():
        h = "🔴" if xona_band_mi(x["id"], bugun.strftime("%d.%m.%Y")) else "🟢"
        btns.append(types.InlineKeyboardButton(
            f"{h} {x['nomi']}",
            callback_data=f"AX_{x['id']}"))
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton("📅 30 kunlikni ko'rish", callback_data="QABUL_30KUN"))

    bot.send_message(cid, f"<pre>{matn}</pre>", parse_mode="HTML", reply_markup=kb)


def _qabulxona_30kun(bot, cid, uid):
    """30 kunlik holat"""
    bugun = datetime.now(TZ).date()
    kunlar_list = [(bugun + timedelta(days=i)) for i in range(30)]

    matn = "📅 30 KUNLIK XONALAR HOLATI\n"
    matn += "━" * 30 + "\n\n"

    # 10 kunlik bloklar
    for blok in range(3):
        bosh = blok * 10
        oxir = bosh + 10
        kunlar_blok = kunlar_list[bosh:oxir]

        matn += "Xona  " + " ".join(k.strftime("%d") for k in kunlar_blok) + "\n"
        matn += "─" * 28 + "\n"

        for x in get_xonalar():
            nom = x["nomi"].replace("-xona", "")
            satri = f"{nom:<5} "
            for kun in kunlar_blok:
                h = xona_kun_holati(x["id"], kun.strftime("%d.%m.%Y"))
                satri += HOLAT_EMOJI[h] + " "
            matn += satri + "\n"

        matn += "\n"

    matn += "🟢 Bosh  🔴 Band  🔵 Ichida  🟡 Bugun chiqadi"

    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for x in get_xonalar():
        h = "🔴" if xona_band_mi(x["id"], bugun.strftime("%d.%m.%Y")) else "🟢"
        btns.append(types.InlineKeyboardButton(
            f"{h} {x['nomi']}",
            callback_data=f"AX_{x['id']}"))
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton("🔙 10 kunlik", callback_data="QABUL_10KUN"))

    bot.send_message(cid, f"<pre>{matn}</pre>", parse_mode="HTML", reply_markup=kb)
