from telebot import types
from datetime import datetime, timedelta
from io import BytesIO
from db import (get_db, get_xonalar, get_binolar, xona_band_mi, band_qil,
                bosh_qil_sana, bosh_qil_bron, bekor_qil_bron, get_bron,
                get_bron_xonalar, tugash_sanasi, format_narx, is_admin,
                is_director, bron_id_gen, qidir_mijoz, bugungi_stat,
                log_stat, hozirgi_mehmonlar, bugungi_keluvchilar,
                xonaga_joylashtir, chiqish_qil, xona_kun_holati, HOLAT_EMOJI,
                joylash_guruh, guruh_chiqar, guruh_olish, mehmon_kochir,
                joylash_uzaytir, bron_yangila, mijoz_profil, barcha_mijozlar)
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
        # Guruhlash
        guruhlar = {}
        for m in mehmonlar:
            g = m["guruh_id"] or f"yolg'iz_{m['id']}"
            guruhlar.setdefault(g, []).append(m)

        jami_kishi = sum(m["kishi"] for m in mehmonlar)
        matn = f"🏨 HOZIRGI MEHMONLAR\n{'─'*25}\n\n"
        matn += f"Jami: {len(guruhlar)} guruh | {len(mehmonlar)} xona | {jami_kishi} kishi"
        bot.send_message(msg.chat.id, matn)

        for g, yozuvlar in guruhlar.items():
            asosiy = yozuvlar[0]
            xonalar_str = ", ".join(y["xona_nomi"] for y in yozuvlar)
            t = f"👤 {asosiy['ism']} | 📞 {asosiy['telefon']}\n"
            t += f"🛏 {xonalar_str}\n"
            t += f"👥 {asosiy['kishi']} kishi | 📅 {asosiy['sana']} - {asosiy['tugash']}"
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                types.InlineKeyboardButton("🚪 Chiqdi", callback_data=f"CHIQISH_{asosiy['id']}"),
                types.InlineKeyboardButton("➕ Kun qo'shish", callback_data=f"UZAYT_{asosiy['id']}"),
            )
            kb.add(
                types.InlineKeyboardButton("🔄 Boshqa xonaga", callback_data=f"KOCHIR_{asosiy['id']}"),
                types.InlineKeyboardButton("👤 Profil", callback_data=f"MPROFIL_{asosiy['telefon']}"),
            )
            bot.send_message(msg.chat.id, t, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("CHIQISH_"))
    def cb_chiqish(call):
        if not is_admin(call.from_user.id): return
        jid = int(call.data.replace("CHIQISH_", ""))
        # Tasdiq so'rash (adashib bosmaslik uchun)
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("✅ Ha, chiqdi", callback_data=f"CHIQTASDIQ_{jid}"),
            types.InlineKeyboardButton("❌ Yo'q", callback_data="CHIQBEKOR"),
        )
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id, "Tasdiqlang")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("CHIQTASDIQ_"))
    def cb_chiqtasdiq(call):
        if not is_admin(call.from_user.id): return
        jid = int(call.data.replace("CHIQTASDIQ_", ""))
        from db import erta_ketish_hisobi
        erta = erta_ketish_hisobi(jid)
        if erta:
            # Erta ketmoqda - yangi narxni ko'rsatib tasdiqlatish
            from handlers.astate import astate
            astate[call.from_user.id] = {"step": "erta_ketish", "erta": erta, "jid": jid}
            kb = types.InlineKeyboardMarkup(row_width=1)
            kb.add(
                types.InlineKeyboardButton(
                    f"✅ Yangi narx: {format_narx(erta['yangi_narx'])} so'm", callback_data="ERTA_YANGI"),
                types.InlineKeyboardButton(
                    f"💯 To'liq narx: {format_narx(erta['eski_narx'])} so'm", callback_data="ERTA_TOLIQ"),
            )
            bot.edit_message_text(
                f"⏰ ERTA KETISH\n\n"
                f"Rejada: {erta['rejal_kun']} kun\n"
                f"Haqiqiy: {erta['haqiqiy_kun']} kun turdi\n\n"
                f"To'liq narx: {format_narx(erta['eski_narx'])} so'm\n"
                f"Qayta hisob: {format_narx(erta['yangi_narx'])} so'm\n\n"
                f"Qaysi summani olamiz? (yoki boshqa summa yozing)",
                call.message.chat.id, call.message.message_id, reply_markup=kb)
            bot.answer_callback_query(call.id)
            return
        # Oddiy chiqish
        chiqish_qil(jid)
        bot.edit_message_text("✅ Chiqish qayd qilindi! Barcha xonalar bo'shatildi.",
                              call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Chiqdi!")

    @bot.callback_query_handler(func=lambda c: c.data == "ERTA_YANGI")
    def cb_erta_yangi(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        from db import chiqish_narx_yangila
        st = astate.get(call.from_user.id, {})
        erta = st.get("erta")
        if erta:
            if erta["guruh_id"]:
                chiqish_narx_yangila(erta["guruh_id"], erta["yangi_narx"])
            chiqish_qil(erta["joylashgan_id"])
            bot.edit_message_text(
                f"✅ Chiqdi! Qayta hisoblangan narx: {format_narx(erta['yangi_narx'])} so'm\n"
                f"({erta['haqiqiy_kun']} kun turdi)",
                call.message.chat.id, call.message.message_id)
        astate.pop(call.from_user.id, None)
        bot.answer_callback_query(call.id, "Chiqdi!")

    @bot.callback_query_handler(func=lambda c: c.data == "ERTA_TOLIQ")
    def cb_erta_toliq(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        st = astate.get(call.from_user.id, {})
        erta = st.get("erta")
        if erta:
            chiqish_qil(erta["joylashgan_id"])
            bot.edit_message_text(
                f"✅ Chiqdi! To'liq narx saqlandi: {format_narx(erta['eski_narx'])} so'm",
                call.message.chat.id, call.message.message_id)
        astate.pop(call.from_user.id, None)
        bot.answer_callback_query(call.id, "Chiqdi!")

    @bot.callback_query_handler(func=lambda c: c.data == "CHIQBEKOR")
    def cb_chiqbekor(call):
        bot.edit_message_text("Bekor qilindi", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("UZAYT_"))
    def cb_uzayt(call):
        if not is_admin(call.from_user.id): return
        jid = int(call.data.replace("UZAYT_", ""))
        kb = types.InlineKeyboardMarkup(row_width=4)
        btns = [types.InlineKeyboardButton(str(i), callback_data=f"UZAYTKUN_{jid}_{i}") for i in range(1, 8)]
        kb.add(*btns)
        bot.send_message(call.message.chat.id, "Necha kun qo'shamiz?", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("UZAYTKUN_"))
    def cb_uzaytkun(call):
        if not is_admin(call.from_user.id): return
        parts = call.data.replace("UZAYTKUN_", "").split("_")
        jid, kun = int(parts[0]), int(parts[1])
        ok, xabar = joylash_uzaytir(jid, kun)
        if ok:
            bot.edit_message_text(f"✅ {xabar}", call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text(f"⚠️ {xabar}", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("KOCHIR_"))
    def cb_kochir(call):
        if not is_admin(call.from_user.id): return
        jid = int(call.data.replace("KOCHIR_", ""))
        conn = get_db()
        j = conn.execute("SELECT * FROM joylashgan WHERE id=?", (jid,)).fetchone()
        conn.close()
        if not j:
            bot.answer_callback_query(call.id, "Topilmadi")
            return
        # Ko'chirish uchun shu mehmon sanalarida BO'SH xonalar
        guruh_id = j["guruh_id"] or j["bron_id"]
        conn = get_db()
        band = conn.execute("SELECT sana FROM band WHERE xona_id=? AND bron_id=?",
                            (j["xona_id"], guruh_id)).fetchall()
        sanalar = [b["sana"] for b in band]
        conn.close()
        if not sanalar:
            try:
                bosh = datetime.strptime(j["sana"], "%d.%m.%Y").date()
                oxir = datetime.strptime(j["tugash"], "%d.%m.%Y").date()
                sanalar = [(bosh + timedelta(days=i)).strftime("%d.%m.%Y")
                           for i in range((oxir - bosh).days)]
            except:
                sanalar = []

        from db import get_xonalar
        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = []
        for x in get_xonalar():
            if x["id"] == j["xona_id"]: continue
            if dict(x).get("yopiq", 0): continue
            # Shu sanalarda bo'shmi?
            bosh_mi = True
            conn = get_db()
            for s in sanalar:
                bb = conn.execute("SELECT 1 FROM band WHERE xona_id=? AND sana=? AND bron_id!=?",
                                 (x["id"], s, guruh_id)).fetchone()
                if bb:
                    bosh_mi = False
                    break
            conn.close()
            if bosh_mi:
                btns.append(types.InlineKeyboardButton(
                    f"🟢 {x['nomi']} ({x['sigim']}👤)", callback_data=f"KOCHIRX_{jid}_{x['id']}"))
        if btns:
            kb.add(*btns)
            bot.send_message(call.message.chat.id, "🔄 Bo'sh xonaga ko'chirish:", reply_markup=kb)
        else:
            bot.send_message(call.message.chat.id, "⚠️ Bu sanalar uchun bo'sh xona yo'q")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("KOCHIRX_"))
    def cb_kochirx(call):
        if not is_admin(call.from_user.id): return
        parts = call.data.replace("KOCHIRX_", "").split("_")
        jid, yangi_xid = int(parts[0]), int(parts[1])
        from db import get_xonalar
        xona = next((x for x in get_xonalar() if x["id"] == yangi_xid), None)
        if xona:
            ok, xabar = mehmon_kochir(jid, yangi_xid, xona["nomi"])
            belgi = "✅" if ok else "⚠️"
            bot.edit_message_text(f"{belgi} {xabar}",
                                  call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

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
        # Xonalarni joylashtirildi deb belgilash - BITTA guruh
        xid_list = get_bron_xonalar(bid)
        xona_royxat = []
        for xid in xid_list:
            conn = get_db()
            xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
            conn.close()
            xona_royxat.append((xid, xnomi))
        if xona_royxat:
            joylash_guruh(xona_royxat, b["ism"], b["telefon"], b["kishi"], b["sana"], b["kunlar"], bid)
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
        # Inline keyboard - raqamlarni bosish orqali (1-20 + qo'lda)
        kb = types.InlineKeyboardMarkup(row_width=5)
        btns = [types.InlineKeyboardButton(str(i), callback_data=f"JOYLA_KISHI_{xid}_{i}") for i in range(1, 21)]
        kb.add(*btns)
        kb.add(types.InlineKeyboardButton("✏️ Qo'lda kiritish (20+)", callback_data=f"JOYLA_KISHIQOL_{xid}"))
        xnomi_str = x["nomi"]
        joyla_matn = "Xona: " + xnomi_str + " | Bugun: " + bugun + "\n\nNechta kishi?"
        bot.send_message(call.message.chat.id, joyla_matn, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("JOYLA_KISHIQOL_"))
    def cb_joyla_kishiqol(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        xid = int(call.data.replace("JOYLA_KISHIQOL_", ""))
        bugun = datetime.now(TZ).strftime("%d.%m.%Y")
        conn = get_db()
        x = conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()
        conn.close()
        astate[call.from_user.id] = {
            "step": "joyla_kishi_qol", "joyla_xid": xid, "joyla_xnomi": x["nomi"],
            "joyla_xona_ids": [xid], "joyla_sana": bugun, "joyla_sigim": x["sigim"]
        }
        bot.send_message(call.message.chat.id, "✏️ Nechta kishi? (son kiriting, masalan 25)")
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
        if n > x["sigim"]:
            qolgan = n - x["sigim"]
            matn = f"Xona: {x['nomi']} ({x['sigim']}👤)\n⚠️ {n} kishi, {qolgan} kishi qo'shimcha joy kerak (keyin qo'shimcha xona tanlaysiz).\n\nNecha kun turadi?"
        else:
            matn = f"Xona: {x['nomi']} | {n} kishi\nNecha kun turadi?"
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
        st["joyla_kunlar"] = kunlar
        sana = st.get("joyla_sana", datetime.now(TZ).strftime("%d.%m.%Y"))
        kishi = st.get("joyla_kishi", 1)
        sigim = st.get("joyla_sigim", 1)
        astate[call.from_user.id] = st

        # Agar kishi > sig'im bo'lsa - qo'shimcha xona tanlash imkoni
        if kishi > sigim:
            st["step"] = "joyla_qosh"
            astate[call.from_user.id] = st
            _joyla_qosh_xona(bot, call.message.chat.id, call.from_user.id)
        else:
            st["step"] = "joyla_ism"
            astate[call.from_user.id] = st
            tugash = tugash_sanasi(sana, kunlar)
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("🔙 Admin menyu")
            bot.send_message(call.message.chat.id,
                f"📅 {sana} - {tugash} | {kunlar} kun\n\nMijoz ismi:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("JOYLA_QOSH_") and c.data != "JOYLA_QOSH_TASDIQ")
    def cb_joyla_qosh(call):
        """Joylashda qo'shimcha xona toggle"""
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        xid = int(call.data.replace("JOYLA_QOSH_", ""))
        st = astate.get(call.from_user.id, {})
        ids = st.get("joyla_xona_ids", [])
        if xid in ids:
            if len(ids) > 1:  # kamida 1 ta qolsin
                ids.remove(xid)
        else:
            ids.append(xid)
        st["joyla_xona_ids"] = ids
        astate[call.from_user.id] = st
        _joyla_qosh_xona(bot, call.message.chat.id, call.from_user.id, edit_msg=call.message.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "AXBRON_NARX_AVTO")
    def cb_axbron_narx_avto(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        st = astate.get(call.from_user.id, {})
        narx = st.get("axbron_avto_narx", 0)
        try:
            bot.edit_message_text(f"✅ Narx: {format_narx(narx)} so'm",
                                  call.message.chat.id, call.message.message_id)
        except: pass
        _axbron_yakunla(bot, call.message.chat.id, call.from_user.id, st, narx)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "TB_NARX_AVTO")
    def cb_tb_narx_avto(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        st = astate.get(call.from_user.id, {})
        try:
            bot.edit_message_text(f"✅ Avtomatik narx: {format_narx(st['ab']['narx'])} so'm",
                                  call.message.chat.id, call.message.message_id)
        except: pass
        _tb_yakunla(bot, call.message.chat.id, call.from_user.id, st)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "JOYLA_NARX_AVTO")
    def cb_joyla_narx_avto(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        st = astate.get(call.from_user.id, {})
        narx = st.get("joyla_avto_narx", 0)
        try:
            bot.edit_message_text(f"✅ Avtomatik narx: {format_narx(narx)} so'm",
                                  call.message.chat.id, call.message.message_id)
        except: pass
        _joyla_yakunla(bot, call.message.chat.id, call.from_user.id, st, narx)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "JOYLA_QOSH_TASDIQ")
    def cb_joyla_qosh_tasdiq(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        from db import get_xonalar
        st = astate.get(call.from_user.id, {})
        xona_ids = st.get("joyla_xona_ids", [])
        kishi = st.get("joyla_kishi", 1)
        barcha_x = {x["id"]: x for x in get_xonalar()}
        jami_sigim = sum(barcha_x[i]["sigim"] for i in xona_ids if i in barcha_x)

        # Agar 2+ xona va sig'im kishiga teng/ortiq bo'lsa - taqsimot usulini so'rash
        if len(xona_ids) >= 2 and jami_sigim >= kishi:
            kb = types.InlineKeyboardMarkup(row_width=1)
            kb.add(
                types.InlineKeyboardButton("📊 Sig'im bo'yicha taqsimla", callback_data="JOYLA_TAQSIM_avto"),
                types.InlineKeyboardButton("🏠 Har xonaga o'zim belgilayman", callback_data="JOYLA_TAQSIM_qol"),
            )
            nomlar = ", ".join(barcha_x[i]["nomi"] for i in xona_ids if i in barcha_x)
            bot.send_message(call.message.chat.id,
                f"👥 {kishi} kishi → {nomlar}\n\nKishilarni qanday joylaymiz?",
                reply_markup=kb)
            bot.answer_callback_query(call.id)
            return

        # Bitta xona yoki ortiqcha - to'g'ridan ismga
        st["step"] = "joyla_ism"
        astate[call.from_user.id] = st
        sana = st.get("joyla_sana", "")
        kunlar = st.get("joyla_kunlar", 1)
        tugash = tugash_sanasi(sana, kunlar)
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(call.message.chat.id,
            f"📅 {sana} - {tugash} | {kunlar} kun\n\nMijoz ismi:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "JOYLA_TAQSIM_avto")
    def cb_joyla_taqsim_avto(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        st = astate.get(call.from_user.id, {})
        st["joyla_taqsim"] = "avto"  # sig'im bo'yicha
        st["step"] = "joyla_ism"
        astate[call.from_user.id] = st
        sana = st.get("joyla_sana", "")
        kunlar = st.get("joyla_kunlar", 1)
        tugash = tugash_sanasi(sana, kunlar)
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(call.message.chat.id,
            f"📊 Sig'im bo'yicha taqsimlanadi\n📅 {sana} - {tugash}\n\nMijoz ismi:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "JOYLA_TAQSIM_qol")
    def cb_joyla_taqsim_qol(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        st = astate.get(call.from_user.id, {})
        st["joyla_taqsim"] = "qol"
        st["joyla_xona_kishi"] = {}  # har xona uchun kishi
        st["joyla_taqsim_idx"] = 0
        astate[call.from_user.id] = st
        _joyla_xona_kishi_sora(bot, call.message.chat.id, call.from_user.id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("JOYLA_XKISHI_"))
    def cb_joyla_xkishi(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        n = int(call.data.replace("JOYLA_XKISHI_", ""))
        st = astate.get(call.from_user.id, {})
        idx = st.get("joyla_taqsim_idx", 0)
        xona_ids = st.get("joyla_xona_ids", [])
        if idx < len(xona_ids):
            st["joyla_xona_kishi"][xona_ids[idx]] = n
            st["joyla_taqsim_idx"] = idx + 1
        astate[call.from_user.id] = st
        # Keyingi xona yoki ismga o'tish
        if st["joyla_taqsim_idx"] < len(xona_ids):
            _joyla_xona_kishi_sora(bot, call.message.chat.id, call.from_user.id, call.message.message_id)
        else:
            st["step"] = "joyla_ism"
            astate[call.from_user.id] = st
            sana = st.get("joyla_sana", "")
            kunlar = st.get("joyla_kunlar", 1)
            tugash = tugash_sanasi(sana, kunlar)
            # Taqsimot xulosasi
            from db import get_xonalar
            barcha_x = {x["id"]: x for x in get_xonalar()}
            xulosa = ", ".join(f"{barcha_x[i]['nomi']}: {st['joyla_xona_kishi'][i]}👤"
                               for i in xona_ids if i in barcha_x)
            try:
                bot.edit_message_text(f"✅ {xulosa}", call.message.chat.id, call.message.message_id)
            except: pass
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("🔙 Admin menyu")
            bot.send_message(call.message.chat.id,
                f"📅 {sana} - {tugash} | {kunlar} kun\n\nMijoz ismi:", reply_markup=kb)
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
        xona_royxat = []
        for xid in xid_list:
            conn = get_db()
            xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
            conn.close()
            xona_royxat.append((xid, xnomi))
        if xona_royxat:
            joylash_guruh(xona_royxat, b["ism"], b["telefon"], b["kishi"], b["sana"], b["kunlar"], bid)
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
        row = []
        for i in range(1, 21):
            row.append(str(i))
        kb.add(*row)
        kb.add("🔙 Admin menyu")
        bot.send_message(msg.chat.id,
            "Tezkor bron\nNechta kishi? (tugmadan tanlang yoki istalgan sonni yozing)",
            reply_markup=kb)

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

    @bot.message_handler(func=lambda m: m.text == "⚙️ Sozlamalar" and is_admin(m.from_user.id))
    def h_sozlamalar(msg):
        from handlers.astate import astate
        astate.pop(msg.from_user.id, None)
        from keyboards import sozlamalar_kb
        bot.send_message(msg.chat.id,
            "⚙️ Sozlamalar va qo'shimcha bo'limlar:",
            reply_markup=sozlamalar_kb(msg.from_user.id))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("MPROFIL_"))
    def cb_mprofil(call):
        if not is_admin(call.from_user.id): return
        tel = call.data.replace("MPROFIL_", "")
        _mijoz_profil_korsat(bot, call.message.chat.id, tel)
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=lambda m: m.text == "👥 Mijozlar ro'yxati" and is_admin(m.from_user.id))
    def h_mijozlar_royxat(msg):
        mijozlar = barcha_mijozlar(50)
        if not mijozlar:
            bot.send_message(msg.chat.id, "Hali mijozlar yo'q")
            return
        matn = f"👥 MIJOZLAR RO'YXATI\n{'━'*22}\n\n"
        matn += f"Jami: {len(mijozlar)} ta mijoz\n\n"
        kb = types.InlineKeyboardMarkup(row_width=1)
        for m in mijozlar[:30]:
            ism = m["ism"] or "Noma'lum"
            matn += f"👤 {ism} | 📞 {m['telefon']}\n   {m['bron_soni']} bron | {format_narx(m['jami'] or 0)} so'm\n"
            kb.add(types.InlineKeyboardButton(
                f"👤 {ism} ({m['bron_soni']} bron)",
                callback_data=f"MPROFIL_{m['telefon']}"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    # ===== NARX REJIMI =====
    @bot.message_handler(func=lambda m: m.text == "💵 Narx rejimi" and is_admin(m.from_user.id))
    def h_narx_rejim(msg):
        from db import sozlama_ol
        joriy = sozlama_ol("narx_rejim", "xona")
        joriy_txt = "🏠 Xona narxi (xona × kun)" if joriy == "xona" else "👤 Kishi narxi (narx × kishi × kun)"
        matn = (f"💵 NARX HISOBI REJIMI\n{'━'*22}\n\n"
                f"Joriy: {joriy_txt}\n\n"
                "🏠 Xona rejimi: har xona uchun belgilangan narx × kun\n\n"
                "👤 Kishi rejimi: 1 kishi narxi × kishi soni × kun")
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("🏠 Xona narxi rejimi", callback_data="NREJIM_xona"),
            types.InlineKeyboardButton("👤 Kishi narxi rejimi", callback_data="NREJIM_kishi"),
        )
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("NREJIM_"))
    def cb_nrejim(call):
        if not is_admin(call.from_user.id): return
        from db import sozlama_saqla
        rejim = call.data.replace("NREJIM_", "")
        sozlama_saqla("narx_rejim", rejim)
        txt = "🏠 Xona narxi" if rejim == "xona" else "👤 Kishi narxi"
        bot.edit_message_text(f"✅ Narx rejimi: {txt}\n\nEndi narxlar shu bo'yicha hisoblanadi.",
                              call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Saqlandi!")

    # ===== DAROMAD =====
    @bot.message_handler(func=lambda m: m.text == "💰 Daromad" and is_admin(m.from_user.id))
    def h_daromad(msg):
        from db import kunlik_daromad, daromad_hisobot, xarajat_hisobot
        bugun = datetime.now(TZ)
        bugun_s = bugun.strftime("%d.%m.%Y")
        oy_bosh = bugun.replace(day=1).strftime("%d.%m.%Y")
        hafta_bosh = (bugun - timedelta(days=6)).strftime("%d.%m.%Y")
        d_bugun = kunlik_daromad(bugun_s)
        d_hafta = daromad_hisobot(hafta_bosh, bugun_s)
        d_oy = daromad_hisobot(oy_bosh, bugun_s)
        d_jami = daromad_hisobot()
        x_oy = xarajat_hisobot(oy_bosh, bugun_s)
        x_jami = xarajat_hisobot()
        matn = (f"💰 MOLIYA HISOBOTI\n{'━'*22}\n\n"
                f"📈 DAROMAD:\n"
                f"   📅 Bugun: {format_narx(d_bugun)} so'm\n"
                f"   📆 Hafta: {format_narx(d_hafta)} so'm\n"
                f"   🗓 Oy: {format_narx(d_oy)} so'm\n"
                f"   💎 Jami: {format_narx(d_jami)} so'm\n\n"
                f"📉 XARAJAT:\n"
                f"   🗓 Oy: {format_narx(x_oy)} so'm\n"
                f"   💸 Jami: {format_narx(x_jami)} so'm\n\n"
                f"💵 SOF FOYDA (oy): {format_narx(d_oy - x_oy)} so'm\n"
                f"💵 SOF FOYDA (jami): {format_narx(d_jami - x_jami)} so'm")
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("➕ Xarajat qo'shish", callback_data="XARAJAT_QOSH"),
            types.InlineKeyboardButton("📋 Xarajatlar", callback_data="XARAJAT_ROYXAT"),
        )
        kb.add(
            types.InlineKeyboardButton("📅 Davr bo'yicha", callback_data="DAROMAD_DAVR"),
            types.InlineKeyboardButton("🗑 Tozalash", callback_data="DAROMAD_TOZALASH"),
        )
        # Qarzdorlar
        conn = get_db()
        qarzlar = conn.execute(
            "SELECT id, ism, narx, COALESCE(tolangan,0) as tol FROM bronlar WHERE holat IN ('tasdiqlangan','joylashgan') AND narx > COALESCE(tolangan,0)"
        ).fetchall()
        conn.close()
        if qarzlar:
            matn += f"\n\n⚠️ Qarzdorlar ({len(qarzlar)}):\n"
            for q in qarzlar[:8]:
                matn += f"   #{q['id']} {q['ism']}: {format_narx(q['narx']-q['tol'])} so'm\n"
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "XARAJAT_QOSH")
    def cb_xarajat_qosh(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "xarajat_izoh"}
        bot.send_message(call.message.chat.id,
            "📝 Xarajat nimaga? (masalan: Oziq-ovqat, Tozalash, Ish haqi)")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "XARAJAT_ROYXAT")
    def cb_xarajat_royxat(call):
        if not is_admin(call.from_user.id): return
        from db import xarajat_royxat
        rows = xarajat_royxat(20)
        if not rows:
            bot.answer_callback_query(call.id, "Xarajatlar yo'q")
            return
        matn = f"📉 XARAJATLAR\n{'━'*22}\n\n"
        for r in rows:
            matn += f"💸 {format_narx(r['summa'])} — {r['izoh']}\n   {r['sana']}\n"
        bot.send_message(call.message.chat.id, matn)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "DAROMAD_DAVR")
    def cb_daromad_davr(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "daromad_davr_bosh"}
        bot.send_message(call.message.chat.id,
            "📅 Boshlanish sanasini kiriting (kun.oy.yil):\nMasalan: 01.06.2026")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "DAROMAD_TOZALASH")
    def cb_daromad_tozalash(call):
        if not is_admin(call.from_user.id): return
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("🗑 Daromadlarni tozalash", callback_data="TOZA_DAROMAD_HA"),
            types.InlineKeyboardButton("🗑 Xarajatlarni tozalash", callback_data="TOZA_XARAJAT_HA"),
            types.InlineKeyboardButton("❌ Bekor", callback_data="TOZA_BEKOR"),
        )
        bot.send_message(call.message.chat.id,
            "⚠️ Diqqat! Tozalash qaytarib bo'lmaydi.\nNimani tozalaymiz?", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "TOZA_DAROMAD_HA")
    def cb_toza_daromad_ha(call):
        if not is_admin(call.from_user.id): return
        from db import daromad_tozalash
        daromad_tozalash()
        bot.edit_message_text("✅ Daromad yozuvlari tozalandi. Hisob noldan boshlanadi.",
                              call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Tozalandi")

    @bot.callback_query_handler(func=lambda c: c.data == "TOZA_XARAJAT_HA")
    def cb_toza_xarajat_ha(call):
        if not is_admin(call.from_user.id): return
        from db import xarajat_tozalash
        xarajat_tozalash()
        bot.edit_message_text("✅ Xarajat yozuvlari tozalandi.",
                              call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Tozalandi")

    @bot.callback_query_handler(func=lambda c: c.data == "TOZA_BEKOR")
    def cb_toza_bekor(call):
        bot.edit_message_text("Bekor qilindi", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    # ===== TOZALASH =====
    @bot.message_handler(func=lambda m: m.text == "🧹 Tozalash" and is_admin(m.from_user.id))
    def h_tozalash(msg):
        from db import get_xonalar, xona_tozalik_ol
        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = []
        for x in get_xonalar():
            tz = xona_tozalik_ol(x["id"])
            emoji = "🧹" if tz == "toza" else "🧴"
            btns.append(types.InlineKeyboardButton(f"{emoji} {x['nomi']}", callback_data=f"TOZA_{x['id']}"))
        kb.add(*btns)
        bot.send_message(msg.chat.id,
            f"🧹 XONALAR TOZALIGI\n{'━'*22}\n\n🧹 Toza | 🧴 Iflos\n\nO'zgartirish uchun bosing:",
            reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("TOZA_") and c.data not in ("TOZA_DAROMAD_HA","TOZA_XARAJAT_HA","TOZA_BEKOR"))
    def cb_toza(call):
        if not is_admin(call.from_user.id): return
        from db import get_xonalar, xona_tozalik_ol, xona_tozalik_belgila
        xid = int(call.data.replace("TOZA_", ""))
        joriy = xona_tozalik_ol(xid)
        xona_tozalik_belgila(xid, "iflos" if joriy == "toza" else "toza")
        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = []
        for x in get_xonalar():
            tz = xona_tozalik_ol(x["id"])
            emoji = "🧹" if tz == "toza" else "🧴"
            btns.append(types.InlineKeyboardButton(f"{emoji} {x['nomi']}", callback_data=f"TOZA_{x['id']}"))
        kb.add(*btns)
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb)
        except: pass
        bot.answer_callback_query(call.id, "O'zgartirildi")

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
        not any(c.data.startswith(p) for p in ["AXB_","AXBAND_","AXBOSH_","AXJOY_","AXRASM_","AXVIDEO_","AXNARX_"]))
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
        tozalik = dict(x).get("tozalik", "toza") or "toza"
        tozalik_txt = "🧹 Toza" if tozalik == "toza" else "🧴 Iflos"
        matn = (f"{x['nomi']} | {x['bino_nomi']}\n"
                f"Qavat: {x['qavat']} | Joy: {x['sigim']}👤\n"
                f"Narx: {format_narx(x['narx'])} som\n"
                f"Bugun: {h}{yopiq_txt}\n"
                f"Tozalik: {tozalik_txt} | 📸 {rasmlar}")
        # Hozir kim band qilgan?
        from db import xona_kim_band
        kim = xona_kim_band(xid, bugun)
        if kim:
            if kim["tur"] == "joylashgan":
                matn += f"\n\n🔵 Hozir: {kim['ism']} | {kim['telefon']}\n   📅 {kim['sana']}-{kim['tugash']}"
            else:
                matn += f"\n\n🔴 Bron: {kim['ism']} | {kim['telefon']}\n   #{kim['bron_id']}"
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
        # Joylashganlar
        joylar = conn.execute(
            "SELECT * FROM joylashgan WHERE xona_id=? AND holat='joylashgan' ORDER BY id DESC",
            (xid,)).fetchall()
        # Bronlar
        bids = conn.execute("SELECT DISTINCT bron_id FROM bron_xonalar WHERE xona_id=?", (xid,)).fetchall()
        bronlar = []
        for r in bids:
            b = conn.execute("SELECT * FROM bronlar WHERE id=? AND holat NOT IN ('bekor','chiqgan')",
                            (r["bron_id"],)).fetchone()
            if b: bronlar.append(b)
        conn.close()

        matn = f"📋 {xnomi} - HOLAT\n{'─'*22}\n\n"

        # 15 kunlik jadval (rang bilan)
        bugun = datetime.now(TZ).date()
        matn += "📅 15 kunlik:\n"
        for i in range(15):
            kun = bugun + timedelta(days=i)
            hol = xona_kun_holati(xid, kun.strftime("%d.%m.%Y"))
            matn += f"{HOLAT_EMOJI[hol]}{kun.strftime('%d')} "
            if (i+1) % 5 == 0: matn += "\n"
        matn += "\n🟢bo'sh 🔴band 🔵ichida 🟡chiqish\n\n"

        kb = types.InlineKeyboardMarkup(row_width=1)

        # Joylashganlar
        if joylar:
            matn += "🔵 Hozir joylashgan:\n"
            for j in joylar:
                matn += f"  • {j['ism']} | {j['telefon']}\n    {j['sana']}-{j['tugash']}\n"
                kb.add(types.InlineKeyboardButton(
                    f"🔵 {j['ism']} (joylashgan) - boshqarish",
                    callback_data=f"JDET_{j['id']}"))
            matn += "\n"

        # Bronlar
        if bronlar:
            matn += "📋 Bronlar:\n"
            for b in bronlar[-8:]:
                tugash = tugash_sanasi(b["sana"], b["kunlar"])
                h = {"tasdiqlangan": "✅", "kutilmoqda": "⏳", "joylashgan": "🏠"}.get(b["holat"], "❓")
                matn += f"  {h} #{b['id']} {b['ism']} ({b['sana']}-{tugash})\n"
                kb.add(types.InlineKeyboardButton(
                    f"{h} #{b['id']} {b['ism']} - boshqarish",
                    callback_data=f"BDET_{b['id']}"))

        if not joylar and not bronlar:
            matn += "✅ Bo'sh - hech qanday bron/mehmon yo'q"

        kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"AX_{xid}"))
        try:
            bot.edit_message_text(matn, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, matn, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("JDET_"))
    def cb_jdet(call):
        """Joylashgan mehmonni boshqarish (xona detaildan)"""
        if not is_admin(call.from_user.id): return
        jid = int(call.data.replace("JDET_", ""))
        conn = get_db()
        j = conn.execute("SELECT * FROM joylashgan WHERE id=?", (jid,)).fetchone()
        conn.close()
        if not j:
            bot.answer_callback_query(call.id, "Topilmadi")
            return
        matn = (f"🔵 JOYLASHGAN MEHMON\n{'─'*20}\n\n"
                f"👤 {j['ism']}\n📞 {j['telefon']}\n"
                f"🛏 {j['xona_nomi']}\n👥 {j['kishi']} kishi\n"
                f"📅 {j['sana']} - {j['tugash']}")
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("🚪 Chiqdi", callback_data=f"CHIQISH_{jid}"),
            types.InlineKeyboardButton("➕ Kun qo'shish", callback_data=f"UZAYT_{jid}"),
        )
        kb.add(
            types.InlineKeyboardButton("🔄 Boshqa xonaga", callback_data=f"KOCHIR_{jid}"),
            types.InlineKeyboardButton("👤 Profil", callback_data=f"MPROFIL_{j['telefon']}"),
        )
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

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXJOY_"))
    def cb_axjoy(call):
        """Qabulxonadan joylash - xuddi Xonaga joylash kabi (kishi, kun, qo'shimcha xona)"""
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AXJOY_", ""))
        from handlers.astate import astate
        conn = get_db()
        x = conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()
        conn.close()
        bugun = datetime.now(TZ).strftime("%d.%m.%Y")
        astate[call.from_user.id] = {
            "step": "joyla_kishi", "joyla_xid": xid,
            "joyla_xnomi": x["nomi"], "joyla_sana": bugun
        }
        kb = types.InlineKeyboardMarkup(row_width=5)
        btns = [types.InlineKeyboardButton(str(i), callback_data=f"JOYLA_KISHI_{xid}_{i}") for i in range(1, 11)]
        kb.add(*btns)
        bot.send_message(call.message.chat.id,
            f"🏠 JOYLASH\nXona: {x['nomi']} | Bugun: {bugun}\n\nNechta kishi?", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXBAND_"))
    def cb_axband(call):
        """Qabulxonadan bron qilish - to'liq (sana, kishi, kun, qo'shimcha xona, ism, tel)"""
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AXBAND_", ""))
        from handlers.astate import astate
        conn = get_db()
        x = conn.execute("SELECT * FROM xonalar WHERE id=?", (xid,)).fetchone()
        conn.close()
        astate[call.from_user.id] = {
            "step": "axbron", "axbron_xid": xid, "axbron_xnomi": x["nomi"],
            "axbron_sigim": x["sigim"], "axbron_xona_ids": [xid]
        }
        # Sana tugmalari (bugundan 14 kun)
        kb = types.InlineKeyboardMarkup(row_width=3)
        bugun = datetime.now(TZ)
        btns = []
        for i in range(14):
            kun = bugun + timedelta(days=i)
            label = "Bugun" if i == 0 else ("Ertaga" if i == 1 else kun.strftime("%d.%m"))
            btns.append(types.InlineKeyboardButton(label, callback_data=f"AXBSANA_{kun.strftime('%d.%m.%Y')}"))
        kb.add(*btns)
        bot.send_message(call.message.chat.id,
            f"🔴 BRON QILISH\nXona: {x['nomi']}\n\nKelish sanasini tanlang:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXBSANA_"))
    def cb_axbsana(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        sana = call.data.replace("AXBSANA_", "")
        st = astate.get(call.from_user.id, {})
        st["axbron_sana"] = sana
        astate[call.from_user.id] = st
        kb = types.InlineKeyboardMarkup(row_width=5)
        btns = [types.InlineKeyboardButton(str(i), callback_data=f"AXBKISHI_{i}") for i in range(1, 21)]
        kb.add(*btns)
        kb.add(types.InlineKeyboardButton("✏️ Qo'lda kiritish (20+)", callback_data="AXBKISHIQOL"))
        bot.edit_message_text(f"🔴 Bron | {st['axbron_xnomi']} | {sana}\n\nNechta kishi?",
                              call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "AXBKISHIQOL")
    def cb_axbkishiqol(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        st = astate.get(call.from_user.id, {})
        st["step"] = "axbron_kishi_qol"
        astate[call.from_user.id] = st
        bot.send_message(call.message.chat.id, "✏️ Nechta kishi? (son kiriting, masalan 25)")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXBKISHI_"))
    def cb_axbkishi(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        n = int(call.data.replace("AXBKISHI_", ""))
        st = astate.get(call.from_user.id, {})
        st["axbron_kishi"] = n
        astate[call.from_user.id] = st
        kb = types.InlineKeyboardMarkup(row_width=5)
        btns = [types.InlineKeyboardButton(str(i), callback_data=f"AXBKUN_{i}") for i in range(1, 16)]
        kb.add(*btns)
        sigim = st.get("axbron_sigim", 1)
        ogoh = f"\n⚠️ {n} kishi, xona {sigim}👤 - keyin qo'shimcha xona tanlaysiz" if n > sigim else ""
        bot.edit_message_text(f"🔴 Bron | {st['axbron_xnomi']} | {n} kishi{ogoh}\n\nNecha kun?",
                              call.message.chat.id, call.message.message_id, reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXBKUN_"))
    def cb_axbkun(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        kunlar = int(call.data.replace("AXBKUN_", ""))
        st = astate.get(call.from_user.id, {})
        st["axbron_kunlar"] = kunlar
        kishi = st.get("axbron_kishi", 1)
        sigim = st.get("axbron_sigim", 1)
        astate[call.from_user.id] = st
        # Kishi sig'maydigan bo'lsa qo'shimcha xona
        if kishi > sigim:
            st["step"] = "axbron_qosh"
            astate[call.from_user.id] = st
            _axbron_qosh_xona(bot, call.message.chat.id, call.from_user.id, call.message.message_id)
        else:
            st["step"] = "axbron_ism"
            astate[call.from_user.id] = st
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("🔙 Admin menyu")
            bot.send_message(call.message.chat.id, "👤 Mijoz ismi:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXBQOSH_") and c.data != "AXBQOSH_TASDIQ")
    def cb_axbqosh(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        xid = int(call.data.replace("AXBQOSH_", ""))
        st = astate.get(call.from_user.id, {})
        ids = st.get("axbron_xona_ids", [])
        if xid in ids:
            if len(ids) > 1: ids.remove(xid)
        else:
            ids.append(xid)
        st["axbron_xona_ids"] = ids
        astate[call.from_user.id] = st
        _axbron_qosh_xona(bot, call.message.chat.id, call.from_user.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "AXBQOSH_TASDIQ")
    def cb_axbqosh_tasdiq(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        st = astate.get(call.from_user.id, {})
        st["step"] = "axbron_ism"
        astate[call.from_user.id] = st
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(call.message.chat.id, "👤 Mijoz ismi:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AXBOSH_"))
    def cb_axbosh(call):
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("AXBOSH_", ""))
        _xona_boshatish_royxat(bot, call.message.chat.id, xid, call.message.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("BOSHJOY_"))
    def cb_boshjoy(call):
        """Joylashgan mehmonni bo'shatish (guruh bilan)"""
        if not is_admin(call.from_user.id): return
        parts = call.data.replace("BOSHJOY_", "").split("_")
        jid = int(parts[0]); xid = int(parts[1])
        from db import chiqish_qil
        chiqish_qil(jid)
        bot.answer_callback_query(call.id, "Bo'shatildi!")
        _xona_boshatish_royxat(bot, call.message.chat.id, xid, call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("BOSHBRON_"))
    def cb_boshbron(call):
        """Bronni bekor qilish (xona bo'shatishdan)"""
        if not is_admin(call.from_user.id): return
        parts = call.data.replace("BOSHBRON_", "").split("_")
        bid = parts[0]; xid = int(parts[1])
        b = get_bron(bid)
        bekor_qil_bron(bid)
        if b and b["user_id"]:
            try:
                bot.send_message(b["user_id"], f"❌ Bron #{bid} bekor qilindi.\n{TELEFON1}")
            except: pass
        bot.answer_callback_query(call.id, "Bron bekor qilindi!")
        _xona_boshatish_royxat(bot, call.message.chat.id, xid, call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("XONATOZA_"))
    def cb_xonatoza(call):
        """Xonani butunlay tozalash (orphan band ham)"""
        if not is_admin(call.from_user.id): return
        xid = int(call.data.replace("XONATOZA_", ""))
        from db import xona_toliq_tozala
        xona_toliq_tozala(xid)
        bot.answer_callback_query(call.id, "Xona butunlay tozalandi!")
        _xona_boshatish_royxat(bot, call.message.chat.id, xid, call.message.message_id)

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
        # /admin buyrug'ini olib tashlash (faqat /start qoladi)
        try:
            from telebot import types as _t
            bot.set_my_commands([_t.BotCommand("start", "Bosh menyu")],
                                scope=_t.BotCommandScopeChat(uid))
        except: pass
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

    @bot.callback_query_handler(func=lambda c: c.data.startswith("TBKOMB_"))
    def cb_tbkomb(call):
        """Tayyor variant (bitta yoki kombinatsiya) tanlandi"""
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        from db import get_xonalar, guruh_narx_hisobla
        xid_str = call.data.replace("TBKOMB_", "")
        xids = [int(x) for x in xid_str.split("-")]
        st = astate.get(call.from_user.id, {})
        kunlar = st["ab"].get("kunlar", 1)
        kishi = st["ab"].get("kishi", 1)
        sana = st["ab"].get("sana", "")
        barcha_x = {x["id"]: x for x in get_xonalar()}
        xona_obj = [barcha_x[i] for i in xids if i in barcha_x]
        st["ab"]["xona_ids"] = xids
        st["ab"]["xona_nomi"] = " + ".join(x["nomi"] for x in xona_obj)
        st["ab"]["narx"] = guruh_narx_hisobla(xona_obj, kishi, kunlar)
        st["step"] = "tb_ism"
        astate[call.from_user.id] = st
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(call.message.chat.id,
            f"✅ Tanlandi: {st['ab']['xona_nomi']}\n{sana} | {kunlar} kun\n"
            f"💰 {format_narx(st['ab']['narx'])} so'm\n\nMijoz ismi:",
            reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "TB_BARCHASI")
    def cb_tb_barchasi(call):
        """Qo'lda xona tanlash - barcha bo'sh xonalar (qo'shib tanlash mumkin)"""
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        from db import bosh_xonalar_royxat
        st = astate.get(call.from_user.id, {})
        sana = st["ab"].get("sana", "")
        kunlar = st["ab"].get("kunlar", 1)
        st["ab"]["xona_ids"] = []
        st["ab"]["xona_nomi"] = ""
        astate[call.from_user.id] = st
        _tb_xona_tanlash(bot, call.message.chat.id, call.from_user.id, edit_msg=call.message.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("TBQOSH_") and c.data != "TBQOSH_TASDIQ")
    def cb_tbqosh(call):
        """Qo'lda tanlashda xona qo'shish/olib tashlash (toggle)"""
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        xid = int(call.data.replace("TBQOSH_", ""))
        st = astate.get(call.from_user.id, {})
        ids = st["ab"].get("xona_ids", [])
        if xid in ids:
            ids.remove(xid)
        else:
            ids.append(xid)
        st["ab"]["xona_ids"] = ids
        astate[call.from_user.id] = st
        _tb_xona_tanlash(bot, call.message.chat.id, call.from_user.id, edit_msg=call.message.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "TBQOSH_TASDIQ")
    def cb_tbqosh_tasdiq(call):
        if not is_admin(call.from_user.id): return
        from handlers.astate import astate
        from db import get_xonalar, guruh_narx_hisobla
        st = astate.get(call.from_user.id, {})
        ids = st["ab"].get("xona_ids", [])
        if not ids:
            bot.answer_callback_query(call.id, "Avval xona tanlang")
            return
        kunlar = st["ab"].get("kunlar", 1)
        kishi = st["ab"].get("kishi", 1)
        sana = st["ab"].get("sana", "")
        barcha_x = {x["id"]: x for x in get_xonalar()}
        xona_obj = [barcha_x[i] for i in ids if i in barcha_x]
        st["ab"]["xona_nomi"] = " + ".join(x["nomi"] for x in xona_obj)
        st["ab"]["narx"] = guruh_narx_hisobla(xona_obj, kishi, kunlar)
        st["step"] = "tb_ism"
        astate[call.from_user.id] = st
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(call.message.chat.id,
            f"✅ Tanlandi: {st['ab']['xona_nomi']}\n{sana} | {kunlar} kun\n"
            f"💰 {format_narx(st['ab']['narx'])} so'm\n\nMijoz ismi:",
            reply_markup=kb)
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

def _tb_yakunla(bot, cid, uid, st):
    """Tezkor bronni narx bilan yakunlash"""
    from handlers.astate import astate
    from db import get_db, bron_id_gen, tugash_sanasi, band_qil, format_narx as fn
    ab = st["ab"]
    bid = bron_id_gen()
    tugash = tugash_sanasi(ab["sana"], ab["kunlar"])
    conn = get_db()
    conn.execute("""INSERT INTO bronlar (id,ism,telefon,sana,kunlar,kishi,xona,narx,holat,user_id,username,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (bid, ab["ism"], ab.get("telefon", ""), ab["sana"], ab["kunlar"], ab["kishi"],
         ab["xona_nomi"], ab["narx"], "tasdiqlangan",
         DIRECTOR_IDS[0], "admin", datetime.now(TZ).strftime("%d.%m.%Y %H:%M")))
    for xid in ab["xona_ids"]:
        conn.execute("INSERT OR IGNORE INTO bron_xonalar VALUES (?,?)", (bid, xid))
    conn.commit(); conn.close()
    for xid in ab["xona_ids"]:
        band_qil(xid, ab["sana"], ab["kunlar"], bid)
    havola = f"t.me/togtagi_bot?start=bron_{bid}"
    bot.send_message(cid,
        f"✅ Bron #{bid} qo'shildi!\n{ab['xona_nomi']} | {ab['sana']}-{tugash}\n"
        f"👥 {ab['kishi']} kishi | 💰 {fn(ab['narx'])} so'm\n\nMijozga yuboring:\n{havola}",
        reply_markup=admin_kb(uid))
    tel = ab.get("telefon", "")
    try:
        conn2 = get_db()
        all_m = conn2.execute("SELECT * FROM mijozlar").fetchall()
        conn2.close()
        for mm in all_m:
            if mm["telefon"] and str(mm["telefon"])[-9:] == tel[-9:] and mm["user_id"]:
                bot.send_message(mm["user_id"],
                    f"Broningiz tasdiqlandi! #{bid}\n{ab['xona_nomi']}\n{ab['sana']}-{tugash}\n{fn(ab['narx'])} so'm")
                break
    except: pass
    astate.pop(uid, None)


def _joyla_xona_kishi_sora(bot, cid, uid, edit_msg=None):
    """Har bir xona uchun necha kishi degan savol"""
    from telebot import types
    from handlers.astate import astate
    from db import get_xonalar
    st = astate.get(uid, {})
    xona_ids = st.get("joyla_xona_ids", [])
    idx = st.get("joyla_taqsim_idx", 0)
    kishi = st.get("joyla_kishi", 1)
    if idx >= len(xona_ids):
        return
    barcha_x = {x["id"]: x for x in get_xonalar()}
    xid = xona_ids[idx]
    xona = barcha_x.get(xid)
    if not xona:
        return
    # Allaqachon taqsimlangan
    taqsimlangan = sum(st.get("joyla_xona_kishi", {}).values())
    qolgan = kishi - taqsimlangan
    # Tugmalar: 1 dan (qolgan + biroz ortiqcha) gacha
    maks = max(qolgan + 2, xona["sigim"] + 2)
    kb = types.InlineKeyboardMarkup(row_width=5)
    btns = [types.InlineKeyboardButton(str(i), callback_data=f"JOYLA_XKISHI_{i}")
            for i in range(1, min(maks, 15) + 1)]
    kb.add(*btns)
    matn = (f"👥 {xona['nomi']} ({xona['sigim']}👤 sig'im)\n"
            f"Jami {kishi} kishi, {qolgan} kishi qoldi.\n\n"
            f"Bu xonaga necha kishi?")
    if edit_msg:
        try:
            bot.edit_message_text(matn, cid, edit_msg, reply_markup=kb)
            return
        except: pass
    bot.send_message(cid, matn, reply_markup=kb)


def _joyla_yakunla(bot, cid, uid, st, narx):
    """Joylashni narx bilan yakunlash. Taqsimotni hisobga oladi."""
    from handlers.astate import astate
    from db import get_xonalar, joylash_guruh, get_db, tugash_sanasi, format_narx as fn, narx_hisobla
    kishi = st.get("joyla_kishi", 1)
    sana = st.get("joyla_sana", datetime.now(TZ).strftime("%d.%m.%Y"))
    kunlar = st.get("joyla_kunlar", 1)
    tel = st.get("joyla_tel", "")
    ism = st.get("joyla_ism", "")
    xona_ids = st.get("joyla_xona_ids", [st.get("joyla_xid")])
    taqsim = st.get("joyla_taqsim", "avto")
    xona_kishi = st.get("joyla_xona_kishi", {})
    barcha_x = {x["id"]: x for x in get_xonalar()}

    # xona_royxat tuzish - qo'lda taqsim bo'lsa har xonaga kishi qo'shamiz
    if taqsim == "qol" and xona_kishi:
        xona_royxat = [(xid, barcha_x[xid]["nomi"], xona_kishi.get(xid, 0))
                       for xid in xona_ids if xid in barcha_x]
    else:
        xona_royxat = [(xid, barcha_x[xid]["nomi"]) for xid in xona_ids if xid in barcha_x]

    gid = joylash_guruh(xona_royxat, ism, tel, kishi, sana, kunlar)

    # Narxni har xonaga taqsimlash (har xona kishi soniga qarab)
    conn = get_db()
    joylar = conn.execute("SELECT id, xona_id, kishi FROM joylashgan WHERE guruh_id=?", (gid,)).fetchall()
    # Agar admin yagona narx kiritgan bo'lsa - oxirgi xonaga to'liq, qolganlarga 0?
    # Yaxshisi: har xona narxini alohida hisoblab, ularning yig'indisi = umumiy.
    # Lekin admin qo'lda narx kiritgan - uni guruhga umumiy yozamiz (1-yozuvga to'liq, qolgan 0)
    # Hisobot uchun: guruh narxi = admin kiritgan narx. Har yozuvga proporsional.
    avto_jami = sum(narx_hisobla(barcha_x[j["xona_id"]], j["kishi"], kunlar) for j in joylar) or 1
    for j in joylar:
        xona_avto = narx_hisobla(barcha_x[j["xona_id"]], j["kishi"], kunlar)
        ulush = int(round(narx * xona_avto / avto_jami))
        conn.execute("UPDATE joylashgan SET narx=? WHERE id=?", (ulush, j["id"]))
    conn.commit()
    conn.close()

    astate.pop(uid, None)
    tugash = tugash_sanasi(sana, kunlar)
    # Xulosa
    xulosa = ", ".join(f"{barcha_x[j['xona_id']]['nomi']}({j['kishi']}👤)" for j in joylar)
    bot.send_message(cid,
        f"✅ Joylashtirildi!\n\n🛏 {xulosa}\n👤 {ism} | 📞 {tel}\n"
        f"👥 {kishi} kishi\n📅 {sana} - {tugash}\n💰 {fn(narx)} so'm",
        reply_markup=admin_kb(uid))


def _axbron_qosh_xona(bot, cid, uid, edit_msg=None):
    """Qabulxona broni uchun qo'shimcha xona tanlash"""
    from telebot import types
    from handlers.astate import astate
    from db import bosh_xonalar_royxat, get_xonalar
    st = astate.get(uid, {})
    sana = st.get("axbron_sana", "")
    kunlar = st.get("axbron_kunlar", 1)
    kishi = st.get("axbron_kishi", 1)
    tanlangan = st.get("axbron_xona_ids", [])
    barcha_x = {x["id"]: x for x in get_xonalar()}
    bosh = bosh_xonalar_royxat(sana, kunlar)
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for x in bosh:
        belgi = "✅" if x["id"] in tanlangan else "➕"
        btns.append(types.InlineKeyboardButton(f"{belgi} {x['nomi']} ({x['sigim']}👤)",
                    callback_data=f"AXBQOSH_{x['id']}"))
    kb.add(*btns)
    jami_sigim = sum(barcha_x[i]["sigim"] for i in tanlangan if i in barcha_x)
    kb.add(types.InlineKeyboardButton(f"✅ Tasdiqlash ({jami_sigim}👤)", callback_data="AXBQOSH_TASDIQ"))
    nomlar = ", ".join(barcha_x[i]["nomi"] for i in tanlangan if i in barcha_x)
    farq = jami_sigim - kishi
    holat = "✅ yetarli" if farq >= 0 else f"⚠️ yana {-farq} kishi"
    matn = f"👥 {kishi} kishi | Tanlangan: {nomlar} = {jami_sigim}👤 {holat}\n\nQo'shimcha xona:"
    if edit_msg:
        try:
            bot.edit_message_text(matn, cid, edit_msg, reply_markup=kb); return
        except: pass
    bot.send_message(cid, matn, reply_markup=kb)


def _axbron_yakunla(bot, cid, uid, st, narx):
    """Qabulxona bronini yakunlash"""
    from handlers.astate import astate
    from db import get_db, bron_id_gen, tugash_sanasi, band_qil, get_xonalar, format_narx as fn
    sana = st.get("axbron_sana", "")
    kunlar = st.get("axbron_kunlar", 1)
    kishi = st.get("axbron_kishi", 1)
    ism = st.get("axbron_ism", "")
    tel = st.get("axbron_tel", "")
    xona_ids = st.get("axbron_xona_ids", [])
    barcha_x = {x["id"]: x for x in get_xonalar()}
    xona_nomi = " + ".join(barcha_x[i]["nomi"] for i in xona_ids if i in barcha_x)
    bid = bron_id_gen()
    tugash = tugash_sanasi(sana, kunlar)
    conn = get_db()
    conn.execute("""INSERT INTO bronlar (id,ism,telefon,sana,kunlar,kishi,xona,narx,holat,user_id,username,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (bid, ism, tel, sana, kunlar, kishi, xona_nomi, narx, "tasdiqlangan",
         DIRECTOR_IDS[0], "admin", datetime.now(TZ).strftime("%d.%m.%Y %H:%M")))
    for xid in xona_ids:
        conn.execute("INSERT OR IGNORE INTO bron_xonalar VALUES (?,?)", (bid, xid))
    conn.commit(); conn.close()
    for xid in xona_ids:
        band_qil(xid, sana, kunlar, bid)
    astate.pop(uid, None)
    bot.send_message(cid,
        f"✅ Bron #{bid} qo'shildi!\n🛏 {xona_nomi}\n👤 {ism} | 📞 {tel}\n"
        f"👥 {kishi} kishi | 📅 {sana}-{tugash}\n💰 {fn(narx)} so'm",
        reply_markup=admin_kb(uid))


def _xona_boshatish_royxat(bot, cid, xid, edit_msg=None):
    """Xonadagi joylashgan + bronlarni tugma qilib ko'rsatadi - bosilganda bo'shatadi.
    Orphan band (egasiz band) ham aniqlanadi - to'liq tozalash imkoni bilan."""
    from telebot import types
    from db import get_db, tugash_sanasi
    conn = get_db()
    xnomi = conn.execute("SELECT nomi FROM xonalar WHERE id=?", (xid,)).fetchone()["nomi"]
    # Hozir joylashganlar
    joylar = conn.execute(
        "SELECT * FROM joylashgan WHERE xona_id=? AND holat='joylashgan' ORDER BY id DESC",
        (xid,)).fetchall()
    # Bronlar (bekor bo'lmagan, joylashmagan)
    bids = conn.execute("SELECT DISTINCT bron_id FROM bron_xonalar WHERE xona_id=?", (xid,)).fetchall()
    bronlar = []
    for r in bids:
        b = conn.execute(
            "SELECT * FROM bronlar WHERE id=? AND holat IN ('kutilmoqda','tasdiqlangan')",
            (r["bron_id"],)).fetchone()
        if b:
            bronlar.append(b)
    # Band yozuvlar soni (orphan tekshirish uchun)
    band_soni = conn.execute("SELECT COUNT(*) FROM band WHERE xona_id=?", (xid,)).fetchone()[0]
    conn.close()

    matn = f"🔓 {xnomi} - BO'SHATISH\n{'─'*22}\n\n"
    kb = types.InlineKeyboardMarkup(row_width=1)

    if joylar:
        matn += "🔵 Hozir joylashgan:\n"
        for j in joylar:
            matn += f"  • {j['ism']} ({j['sana']}-{j['tugash']})\n"
            kb.add(types.InlineKeyboardButton(
                f"🚪 Bo'shatish: {j['ism']} (joylashgan)",
                callback_data=f"BOSHJOY_{j['id']}_{xid}"))
        matn += "\n"

    if bronlar:
        matn += "🔴 Bronlar:\n"
        for b in bronlar:
            tugash = tugash_sanasi(b["sana"], b["kunlar"])
            h = "✅" if b["holat"] == "tasdiqlangan" else "⏳"
            matn += f"  {h} #{b['id']} {b['ism']} ({b['sana']}-{tugash})\n"
            kb.add(types.InlineKeyboardButton(
                f"🗑 Bekor: #{b['id']} {b['ism']} (bron)",
                callback_data=f"BOSHBRON_{b['id']}_{xid}"))
        matn += "\n"

    # Orphan band: band bor, lekin joylashgan/bron ko'rinmaydi
    korinadigan = len(joylar) + len(bronlar)
    if band_soni > 0 and korinadigan == 0:
        matn += ("⚠️ Bu xonada egasi aniqlanmagan band yozuvlari bor "
                 "(eski yoki bekor qilingan). Pastdagi tugma bilan tozalang.\n\n")

    if not joylar and not bronlar and band_soni == 0:
        matn += "✅ Bu xona allaqachon bo'sh."

    # To'liq tozalash - har doim mavjud (orphan band ni ham tozalaydi)
    if band_soni > 0 or joylar or bronlar:
        kb.add(types.InlineKeyboardButton(
            "🧹 Xonani BUTUNLAY tozalash", callback_data=f"XONATOZA_{xid}"))

    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=f"AX_{xid}"))

    if edit_msg:
        try:
            bot.edit_message_text(matn, cid, edit_msg, reply_markup=kb)
            return
        except: pass
    bot.send_message(cid, matn, reply_markup=kb)


def _joyla_qosh_xona(bot, cid, uid, edit_msg=None):
    """Joylashda qo'shimcha xona tanlash (kishi sig'maganda)"""
    from telebot import types
    from handlers.astate import astate
    from db import bosh_xonalar_royxat, get_xonalar
    st = astate.get(uid, {})
    sana = st.get("joyla_sana", "")
    kunlar = st.get("joyla_kunlar", 1)
    kishi = st.get("joyla_kishi", 1)
    tanlangan = st.get("joyla_xona_ids", [])
    barcha_x = {x["id"]: x for x in get_xonalar()}
    bosh = bosh_xonalar_royxat(sana, kunlar)

    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for x in bosh:
        belgi = "✅" if x["id"] in tanlangan else "➕"
        btns.append(types.InlineKeyboardButton(
            f"{belgi} {x['nomi']} ({x['sigim']}👤)",
            callback_data=f"JOYLA_QOSH_{x['id']}"))
    kb.add(*btns)

    jami_sigim = sum(barcha_x[i]["sigim"] for i in tanlangan if i in barcha_x)
    kb.add(types.InlineKeyboardButton(
        f"✅ Tasdiqlash ({jami_sigim}👤)", callback_data="JOYLA_QOSH_TASDIQ"))

    nomlar = ", ".join(barcha_x[i]["nomi"] for i in tanlangan if i in barcha_x)
    farq = jami_sigim - kishi
    if farq >= 0:
        holat = "✅ yetarli" + (f" (+{farq} ortiqcha)" if farq > 0 else "")
    else:
        holat = f"⚠️ yana {-farq} kishi sig'maydi"
    matn = (f"👥 {kishi} kishi uchun joy\n"
            f"Tanlangan: {nomlar} = {jami_sigim}👤 {holat}\n\n"
            f"Qo'shimcha xona belgilang (qayta bossangiz bekor):")
    if edit_msg:
        try:
            bot.edit_message_text(matn, cid, edit_msg, reply_markup=kb)
            return
        except: pass
    bot.send_message(cid, matn, reply_markup=kb)


def _tb_xona_tanlash(bot, cid, uid, edit_msg=None):
    """Tezkor bron - qo'lda xona tanlash (bo'sh xonalar, toggle bilan)"""
    from telebot import types
    from handlers.astate import astate
    from db import bosh_xonalar_royxat, get_xonalar, guruh_narx_hisobla, format_narx as fn
    st = astate.get(uid, {})
    sana = st["ab"].get("sana", "")
    kunlar = st["ab"].get("kunlar", 1)
    kishi = st["ab"].get("kishi", 1)
    tanlangan = st["ab"].get("xona_ids", [])
    bosh = bosh_xonalar_royxat(sana, kunlar)
    barcha_x = {x["id"]: x for x in get_xonalar()}

    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for x in bosh:
        belgi = "✅" if x["id"] in tanlangan else "🟢"
        btns.append(types.InlineKeyboardButton(
            f"{belgi} {x['nomi']} ({x['sigim']}👤)",
            callback_data=f"TBQOSH_{x['id']}"))
    kb.add(*btns)

    jami_sigim = sum(barcha_x[i]["sigim"] for i in tanlangan if i in barcha_x)
    xona_obj = [barcha_x[i] for i in tanlangan if i in barcha_x]
    narx = guruh_narx_hisobla(xona_obj, kishi, kunlar) if xona_obj else 0
    if tanlangan:
        kb.add(types.InlineKeyboardButton(
            f"✅ Tasdiqlash ({jami_sigim}👤 | {fn(narx)})", callback_data="TBQOSH_TASDIQ"))

    matn = f"👥 {kishi} kishi | {kunlar} kun\n"
    if tanlangan:
        nomlar = ", ".join(barcha_x[i]["nomi"] for i in tanlangan if i in barcha_x)
        farq = jami_sigim - kishi
        holat = f"+{farq} ortiqcha joy" if farq > 0 else (f"{-farq} kishi sig'maydi" if farq < 0 else "to'liq mos")
        matn += f"Tanlandi: {nomlar} = {jami_sigim}👤 ({holat})\n"
    matn += "\nXona(lar)ni belgilang (qayta bossangiz bekor bo'ladi):"

    if edit_msg:
        try:
            bot.edit_message_text(matn, cid, edit_msg, reply_markup=kb)
            return
        except: pass
    bot.send_message(cid, matn, reply_markup=kb)


def _joylash_menyusi(bot, cid, uid):
    bugun = datetime.now(TZ).strftime("%d.%m.%Y")
    keluvchilar = bugungi_keluvchilar()
    # Bugun joylash uchun bo'sh: holat 'bosh' yoki 'chiqish' (chiqadigan xona 12:00 da bo'shaydi)
    bosh_list = []
    for x in get_xonalar():
        if dict(x).get("yopiq", 0):
            continue
        hol = xona_kun_holati(x["id"], bugun)
        if hol in ("bosh", "chiqish"):
            bosh_list.append((x, hol))
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
        for x, hol in bosh_list:
            q = "🏠" if x["qavat"] == 1 else "🏢"
            belgi = "🟡" if hol == "chiqish" else "🟢"
            qosh = " (12:00 da bo'shaydi)" if hol == "chiqish" else ""
            matn += f"  {belgi}{q} {x['nomi']} ({x['sigim']}👤){qosh}\n"
            kb.add(types.InlineKeyboardButton(
                f"{belgi} {x['nomi']} ({x['sigim']}👤) - Yangi joylash",
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
        from db import get_xonalar, guruh_narx_hisobla
        kishi = st.get("joyla_kishi", 1)
        kunlar = st.get("joyla_kunlar", 1)
        xona_ids = st.get("joyla_xona_ids", [st["joyla_xid"]])
        barcha_x = {x["id"]: x for x in get_xonalar()}
        xona_obj = [barcha_x[xid] for xid in xona_ids if xid in barcha_x]
        avto_narx = guruh_narx_hisobla(xona_obj, kishi, kunlar)
        st["joyla_tel"] = text
        st["joyla_avto_narx"] = avto_narx
        st["step"] = "joyla_narx"
        astate[uid] = st
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(f"✅ Avtomatik: {format_narx(avto_narx)} so'm", callback_data="JOYLA_NARX_AVTO"))
        bot.send_message(cid,
            f"💰 Avtomatik hisoblangan narx: {format_narx(avto_narx)} so'm\n\n"
            f"Shu narxni tasdiqlang yoki boshqa summani yozing:",
            reply_markup=kb)
        return

    if step == "joyla_narx":
        # Admin boshqa narx kiritdi
        try:
            narx = int(text.replace(" ", "").replace(",", "").replace("so'm", "").replace("som", "").strip())
        except:
            bot.send_message(cid, "⚠️ Faqat raqam kiriting yoki avtomatik tugmani bosing")
            return
        _joyla_yakunla(bot, cid, uid, st, narx)
        return

    if step == "joyla_ism":
        st["joyla_ism"] = text
        st["step"] = "joyla_tel"
        astate[uid] = st
        bot.send_message(cid, "Telefon raqami:")
        return

    # ===== XARAJAT matn steplari =====
    if step == "xarajat_izoh":
        st["xarajat_izoh"] = text
        st["step"] = "xarajat_summa"
        astate[uid] = st
        bot.send_message(cid, f"💸 '{text}' uchun qancha xarajat? (so'mda, masalan 150000)")
        return

    if step == "xarajat_summa":
        try:
            summa = int(text.replace(" ", "").replace(",", "").strip())
        except:
            bot.send_message(cid, "⚠️ Faqat raqam kiriting")
            return
        from db import xarajat_qosh
        xarajat_qosh(summa, st.get("xarajat_izoh", ""), uid)
        astate.pop(uid, None)
        bot.send_message(cid,
            f"✅ Xarajat qo'shildi:\n💸 {format_narx(summa)} so'm — {st.get('xarajat_izoh','')}",
            reply_markup=admin_kb(uid))
        return

    if step == "daromad_davr_bosh":
        st["davr_bosh"] = text.strip()
        st["step"] = "daromad_davr_oxir"
        astate[uid] = st
        bot.send_message(cid, "📅 Tugash sanasini kiriting (kun.oy.yil):")
        return

    if step == "daromad_davr_oxir":
        from db import daromad_hisobot, xarajat_hisobot
        bosh = st.get("davr_bosh", "")
        oxir = text.strip()
        try:
            datetime.strptime(bosh, "%d.%m.%Y")
            datetime.strptime(oxir, "%d.%m.%Y")
        except:
            bot.send_message(cid, "⚠️ Sana formati noto'g'ri. Masalan: 01.06.2026")
            return
        d = daromad_hisobot(bosh, oxir)
        x = xarajat_hisobot(bosh, oxir)
        astate.pop(uid, None)
        bot.send_message(cid,
            f"📊 {bosh} — {oxir}\n{'━'*22}\n"
            f"📈 Daromad: {format_narx(d)} so'm\n"
            f"📉 Xarajat: {format_narx(x)} so'm\n"
            f"💵 Sof foyda: {format_narx(d - x)} so'm",
            reply_markup=admin_kb(uid))
        return

    # ===== QABULXONA BRON (axbron) matn steplari =====
    if step == "erta_ketish":
        from db import chiqish_narx_yangila
        try:
            narx = int(text.replace(" ", "").replace(",", "").replace("so'm", "").replace("som", "").strip())
        except:
            bot.send_message(cid, "⚠️ Tugmani bosing yoki son kiriting")
            return
        erta = st.get("erta")
        if erta:
            if erta["guruh_id"]:
                chiqish_narx_yangila(erta["guruh_id"], narx)
            from db import chiqish_qil as cq
            cq(erta["joylashgan_id"])
            bot.send_message(cid,
                f"✅ Chiqdi! Narx: {format_narx(narx)} so'm ({erta['haqiqiy_kun']} kun)",
                reply_markup=admin_kb(uid))
        astate.pop(uid, None)
        return

    if step == "joyla_kishi_qol":
        try:
            n = int(text.replace(" ", "").strip())
            if n < 1 or n > 200: raise ValueError
        except:
            bot.send_message(cid, "⚠️ 1 dan 200 gacha son kiriting")
            return
        st["joyla_kishi"] = n
        st["step"] = "joyla_kun"
        astate[uid] = st
        xnomi = st.get("joyla_xnomi", "")
        sigim = st.get("joyla_sigim", 1)
        kb = types.InlineKeyboardMarkup(row_width=5)
        xid = st.get("joyla_xid")
        btns = [types.InlineKeyboardButton(str(i), callback_data=f"JOYLA_KUN_{xid}_{i}") for i in range(1, 16)]
        kb.add(*btns)
        if n > sigim:
            matn = f"Xona: {xnomi} ({sigim}👤)\n⚠️ {n} kishi - keyin qo'shimcha xona tanlaysiz.\n\nNecha kun?"
        else:
            matn = f"Xona: {xnomi} | {n} kishi\nNecha kun?"
        bot.send_message(cid, matn, reply_markup=kb)
        return

    if step == "axbron_kishi_qol":
        try:
            n = int(text.replace(" ", "").strip())
            if n < 1 or n > 200: raise ValueError
        except:
            bot.send_message(cid, "⚠️ 1 dan 200 gacha son kiriting")
            return
        st["axbron_kishi"] = n
        st["step"] = "axbron"
        astate[uid] = st
        kb = types.InlineKeyboardMarkup(row_width=5)
        btns = [types.InlineKeyboardButton(str(i), callback_data=f"AXBKUN_{i}") for i in range(1, 16)]
        kb.add(*btns)
        sigim = st.get("axbron_sigim", 1)
        ogoh = f"\n⚠️ {n} kishi - keyin qo'shimcha xona" if n > sigim else ""
        bot.send_message(cid, f"🔴 Bron | {n} kishi{ogoh}\n\nNecha kun?", reply_markup=kb)
        return

    if step == "tb_kishi_qol":
        try:
            n = int(text.replace(" ", "").strip())
            if n < 1 or n > 200: raise ValueError
        except:
            bot.send_message(cid, "⚠️ 1 dan 200 gacha son kiriting")
            return
        st["ab"]["kishi"] = n
        st["step"] = "tb_sana"
        astate[uid] = st
        bot.send_message(cid, f"👥 {n} kishi\n\nKelish sanasini tanlang:", reply_markup=sana_kb())
        return

    if step == "axbron_ism":
        st["axbron_ism"] = text
        st["step"] = "axbron_tel"
        astate[uid] = st
        bot.send_message(cid, "📞 Telefon raqami:")
        return

    if step == "axbron_tel":
        from db import get_xonalar, guruh_narx_hisobla
        st["axbron_tel"] = text
        kishi = st.get("axbron_kishi", 1)
        kunlar = st.get("axbron_kunlar", 1)
        xona_ids = st.get("axbron_xona_ids", [])
        barcha_x = {x["id"]: x for x in get_xonalar()}
        xona_obj = [barcha_x[i] for i in xona_ids if i in barcha_x]
        avto = guruh_narx_hisobla(xona_obj, kishi, kunlar)
        st["axbron_avto_narx"] = avto
        st["step"] = "axbron_narx"
        astate[uid] = st
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(f"✅ Avtomatik: {format_narx(avto)} so'm", callback_data="AXBRON_NARX_AVTO"))
        bot.send_message(cid,
            f"💰 Avtomatik narx: {format_narx(avto)} so'm\n\nTasdiqlang yoki boshqa summa yozing:",
            reply_markup=kb)
        return

    if step == "axbron_narx":
        try:
            narx = int(text.replace(" ", "").replace(",", "").replace("so'm", "").replace("som", "").strip())
        except:
            bot.send_message(cid, "⚠️ Faqat raqam kiriting yoki avtomatik tugmani bosing")
            return
        _axbron_yakunla(bot, cid, uid, st, narx)
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
        ab["telefon"] = text
        st["ab"] = ab
        st["step"] = "tb_narx"
        astate[uid] = st
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(f"✅ Avtomatik: {format_narx(ab['narx'])} so'm", callback_data="TB_NARX_AVTO"))
        bot.send_message(cid,
            f"💰 Avtomatik narx: {format_narx(ab['narx'])} so'm\n\n"
            f"Shu narxni tasdiqlang yoki boshqa summani yozing:",
            reply_markup=kb)
        return

    if step == "tb_narx":
        try:
            narx = int(text.replace(" ", "").replace(",", "").replace("so'm", "").replace("som", "").strip())
        except:
            bot.send_message(cid, "⚠️ Faqat raqam kiriting yoki avtomatik tugmani bosing")
            return
        st["ab"]["narx"] = narx
        astate[uid] = st
        _tb_yakunla(bot, cid, uid, st)
        return

    if step == "mijoz_qidir":
        _mijoz_profil_korsat(bot, cid, text)
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
            # Yangi adminga /admin buyrug'ini ko'rsatish
            try:
                from telebot import types as _t
                bot.set_my_commands([
                    _t.BotCommand("start", "Bosh menyu"),
                    _t.BotCommand("admin", "Admin panel"),
                ], scope=_t.BotCommandScopeChat(new_id))
            except: pass
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


# ===== MIJOZ PROFILI (yordamchi) =====
def _mijoz_profil_korsat(bot, cid, qidiruv):
    from telebot import types
    from db import mijoz_profil, tugash_sanasi, format_narx
    p = mijoz_profil(qidiruv)
    if not p:
        bot.send_message(cid, f"'{qidiruv}' bo'yicha hech narsa topilmadi.\n\nBron ID, telefon yoki ism bilan qidiring.")
        return

    matn = f"👤 MIJOZ PROFILI\n{'━'*22}\n\n"
    matn += f"📛 {p['ism']}\n📞 {p['telefon']}\n\n"
    matn += f"📊 Statistika:\n"
    matn += f"   • Jami bron: {p['jami_bron']} ta\n"
    matn += f"   • Joylashishlar: {p['jami_joylash']} marta\n"
    matn += f"   • Jami xarajat: {format_narx(p['jami_xarajat'])} so'm\n\n"

    if p["hozir_ichida"]:
        matn += f"🟢 HOZIR ICHIDA:\n"
        for j in p["hozir_ichida"]:
            matn += f"   🛏 {j['xona_nomi']} ({j['sana']}-{j['tugash']})\n"
        matn += "\n"

    if p["faol_bron"]:
        matn += f"📋 Faol bronlar:\n"
        for b in p["faol_bron"]:
            t = tugash_sanasi(b["sana"], b["kunlar"])
            h = "✅" if b["holat"] == "tasdiqlangan" else "⏳"
            matn += f"   {h} #{b['id']} | {b['xona']} | {b['sana']}-{t}\n"
        matn += "\n"

    bot.send_message(cid, matn)

    # Tarix (oxirgi bronlar)
    if p["bronlar"]:
        tarix = "📜 Bronlar tarixi:\n" + "─"*22 + "\n"
        for b in p["bronlar"][:10]:
            t = tugash_sanasi(b["sana"], b["kunlar"])
            holat_emoji = {"tasdiqlangan":"✅","joylashgan":"🏠","bekor":"❌","kutilmoqda":"⏳"}.get(b["holat"],"•")
            tarix += f"{holat_emoji} #{b['id']} | {b['xona']}\n   📅 {b['sana']}-{t} | {format_narx(b['narx'] or 0)} so'm\n"
        bot.send_message(cid, tarix)
