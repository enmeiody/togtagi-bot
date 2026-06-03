import os
import json
import urllib.request
import logging
from database import db
from utils import tozala_markdown

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

RESORT_INFO = """Sen Tog' Tagi Resort ning yordamchi botisan.

Resort haqida:
- Manzil: Shohimardon, Farg'ona viloyati, Ko'lqubondan 300 metr pastda
- Telefon: +998993342035, +998704902025
- Instagram: @togtagi

Xonalar (10 ta, 1-bino):
- 1,2-xona: 3 kishilik, 300,000 so'm/kecha (1-qavat)
- 3,4-xona: 7 kishilik, 700,000 so'm/kecha (1-qavat)
- 5-10-xona: 3 kishilik, 300,000 so'm/kecha (2-qavat)
- Check-out: ertasi kuni soat 12:00 gacha

Xizmatlar: Soy bo'yi, Sharshara, Oshxona (o'zingiz pishirasiz),
Mangal, Shashlik, WiFi, Televizor, Tapchanlar, Bepul parking, Yashil tabiat

QOIDALAR:
1. FAQAT Resort haqidagi savollarga javob ber
2. Boshqa mavzularda: "Bu haqida ma'lumotim yo'q. Bog'laning: +998993342035"
3. Bron so'rasa: "Bron qilish uchun tugmani bosing"
4. Javoblar 2-3 jumladan oshmasin
5. Markdown belgilar ishlatma (* ** # va h.k)
6. Foydalanuvchi tilida javob ber
"""


def get_ai_info():
    try:
        with db() as conn:
            rows = conn.execute("SELECT matn FROM ai_info ORDER BY id DESC LIMIT 10").fetchall()
            return "\n".join([r["matn"] for r in rows])
    except:
        return ""


def ai_javob(savol, til="uz"):
    if not ANTHROPIC_API_KEY:
        return None
    try:
        til_map = {
            "uz": "O'zbek tilida javob ber.",
            "uz_kril": "Uzbek kiril yozuvida javob ber.",
            "ru": "Otvet na russkom yazyke."
        }
        qo_info = get_ai_info()
        extra = ("\n\nQo'shimcha ma'lumotlar:\n" + qo_info) if qo_info else ""
        system_txt = RESORT_INFO + extra + " " + til_map.get(til, "")

        data = json.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 200,
            "system": system_txt,
            "messages": [{"role": "user", "content": savol}]
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=data,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return tozala_markdown(result["content"][0]["text"])
    except Exception as e:
        logging.error(f"AI xato: {e}")
        return None
