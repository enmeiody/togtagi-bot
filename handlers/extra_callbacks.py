from db import get_db, is_admin, is_director
from telebot import types


def register(bot):

    @bot.callback_query_handler(func=lambda c: c.data.startswith("BLK_"))
    def cb_blk(call):
        if not is_admin(call.from_user.id): return
        uid = int(call.data.replace("BLK_", ""))
        conn = get_db()
        conn.execute("UPDATE mijozlar SET bloklangan=1 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        bot.edit_message_text(f"{uid} bloklandi", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Bloklandi!")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("UNBLK_"))
    def cb_unblk(call):
        if not is_admin(call.from_user.id): return
        uid = int(call.data.replace("UNBLK_", ""))
        conn = get_db()
        conn.execute("UPDATE mijozlar SET bloklangan=0 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        bot.edit_message_text(f"{uid} blokdan chiqarildi", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Blok ochildi!")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("XBYR_"))
    def cb_xbyr(call):
        if not is_admin(call.from_user.id): return
        target = int(call.data.replace("XBYR_", ""))
        from handlers.astate import astate
        astate[call.from_user.id] = {"step": "xabar_yuborish", "xabar_uid": target}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔙 Admin menyu")
        bot.send_message(call.message.chat.id, "Mijozga xabar yozing:", reply_markup=kb)
        bot.answer_callback_query(call.id)
