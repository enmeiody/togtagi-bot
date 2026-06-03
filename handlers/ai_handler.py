import os
import json
import urllib.request
import logging
import re

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM = """Sen Tog Tagi Resort ning yordamchi botisan.

Resort:
- Manzil: Shohimardon, Fargona viloyati, Kolqubondan 300 metr pastda
- Tel: +998993342035, +998704902025
- Instagram: @togtagi

Xonalar (1-bino, 10 ta):
- 1,2-xona: 3 kishilik, 300,000 som/kecha (1-qavat)
- 3,4-xona: 7 kishilik, 700,000 som/kecha (1-qavat)
- 5-10-xona: 3 kishilik, 300,000 som/kecha (2-qavat)
- Check-out: ertasi 12:00

Xizmatlar: Soy, Sharshara, Oshxona (ozingiz pishirasiz), Mangal, Shashlik, WiFi, TV, Tapchanlar, Parking

QOIDALAR:
1. Faqat Resort haqida javob ber
2. Boshqa mavzu: "Bu haqida malumotim yoq. +998993342035"
3. Javoblar 2-3 jumladan oshmasin
4. Markdown belgiler ishlatma
5. Foydalanuvchi tilida javob ber
"""


def get_extra():
    try:
        from db import get_db
        conn = get_db()
        rows = conn.execute("SELECT matn FROM ai_info ORDER BY id DESC LIMIT 10").fetchall()
        conn.close()
        return "\n".join(r["matn"] for r in rows)
    except:
        return ""


def tozala(matn):
    matn = re.sub(r'\*\*(.+?)\*\*', r'\1', matn)
    matn = re.sub(r'\*(.+?)\*', r'\1', matn)
    matn = re.sub(r'#{1,6}\s', '', matn)
    matn = re.sub(r'`(.+?)`', r'\1', matn)
    return matn.strip()


def ai_javob(savol, til="uz"):
    if not ANTHROPIC_API_KEY:
        return None
    try:
        til_map = {
            "uz": "Uzbek lotinda javob ber.",
            "uz_kril": "Uzbek kirilida javob ber.",
            "ru": "Otvet na russkom."
        }
        extra = get_extra()
        system = SYSTEM
        if extra:
            system += f"\n\nQoshimcha: {extra}"
        system += f" {til_map.get(til, '')}"

        data = json.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 200,
            "system": system,
            "messages": [{"role": "user", "content": savol}]
        }).encode()

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
            return tozala(result["content"][0]["text"])
    except Exception as e:
        logging.error(f"AI: {e}")
        return None
