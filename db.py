import sqlite3
import os
from datetime import datetime, timedelta
import pytz

TZ = pytz.timezone('Asia/Tashkent')
import random
import string

DB_PATH = os.environ.get("DB_PATH", "/data/resort.db")
DIRECTOR_IDS = [8886176055, 7323184602]


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS binolar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nomi TEXT NOT NULL,
        aktiv INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS xonalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bino_id INTEGER DEFAULT 1,
        nomi TEXT NOT NULL,
        qavat INTEGER DEFAULT 1,
        sigim INTEGER NOT NULL,
        narx INTEGER NOT NULL,
        aktiv INTEGER DEFAULT 1,
        yopiq INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS xona_media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        xona_id INTEGER,
        tur TEXT,
        file_id TEXT
    );
    CREATE TABLE IF NOT EXISTS umumiy_media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tur TEXT,
        file_id TEXT
    );
    CREATE TABLE IF NOT EXISTS greeting_media (
        id INTEGER PRIMARY KEY,
        file_id TEXT,
        tur TEXT DEFAULT 'photo'
    );
    CREATE TABLE IF NOT EXISTS band (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        xona_id INTEGER NOT NULL,
        sana TEXT NOT NULL,
        bron_id TEXT,
        UNIQUE(xona_id, sana)
    );
    CREATE TABLE IF NOT EXISTS bronlar (
        id TEXT PRIMARY KEY,
        ism TEXT,
        telefon TEXT,
        sana TEXT,
        kunlar INTEGER,
        kishi INTEGER,
        xona TEXT,
        narx INTEGER,
        holat TEXT DEFAULT 'kutilmoqda',
        user_id INTEGER,
        username TEXT,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS bron_xonalar (
        bron_id TEXT,
        xona_id INTEGER,
        PRIMARY KEY (bron_id, xona_id)
    );
    CREATE TABLE IF NOT EXISTS mijozlar (
        user_id INTEGER PRIMARY KEY,
        ism TEXT,
        telefon TEXT,
        username TEXT,
        bloklangan INTEGER DEFAULT 0,
        created_at TEXT,
        last_active TEXT
    );
    CREATE TABLE IF NOT EXISTS adminlar (
        user_id INTEGER PRIMARY KEY,
        ism TEXT,
        qoshilgan TEXT
    );
    CREATE TABLE IF NOT EXISTS ai_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matn TEXT,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS til_jadval (
        user_id INTEGER PRIMARY KEY,
        til TEXT DEFAULT 'uz'
    );
    CREATE TABLE IF NOT EXISTS statistika (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        harakat TEXT,
        qoshimcha TEXT,
        vaqt TEXT
    );
    CREATE TABLE IF NOT EXISTS ijtimoiy (
        kalit TEXT PRIMARY KEY,
        link TEXT,
        nomi TEXT
    );
    CREATE TABLE IF NOT EXISTS joylashgan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        xona_id INTEGER,
        xona_nomi TEXT,
        ism TEXT,
        telefon TEXT,
        kishi INTEGER,
        sana TEXT,
        tugash TEXT,
        bron_id TEXT,
        holat TEXT DEFAULT 'joylashgan'
    );
    CREATE TABLE IF NOT EXISTS tolovlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bron_id TEXT,
        guruh_id TEXT,
        summa INTEGER,
        izoh TEXT,
        sana TEXT
    );
    CREATE TABLE IF NOT EXISTS sozlama (
        kalit TEXT PRIMARY KEY,
        qiymat TEXT
    );
    CREATE TABLE IF NOT EXISTS xarajatlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        summa INTEGER,
        izoh TEXT,
        sana TEXT,
        admin_id INTEGER
    );
    """)

    # Migrations
    for sql in [
        "ALTER TABLE joylashgan ADD COLUMN guruh_id TEXT",
        "ALTER TABLE xonalar ADD COLUMN bino_id INTEGER DEFAULT 1",
        "ALTER TABLE xonalar ADD COLUMN aktiv INTEGER DEFAULT 1",
        "ALTER TABLE xonalar ADD COLUMN yopiq INTEGER DEFAULT 0",
        "ALTER TABLE xonalar ADD COLUMN tozalik TEXT DEFAULT 'toza'",
        "ALTER TABLE bronlar ADD COLUMN holat TEXT DEFAULT 'kutilmoqda'",
        "ALTER TABLE bronlar ADD COLUMN guruh_id TEXT",
        "ALTER TABLE bronlar ADD COLUMN tolangan INTEGER DEFAULT 0",
        "ALTER TABLE bronlar ADD COLUMN checkin INTEGER DEFAULT 0",
        "ALTER TABLE mijozlar ADD COLUMN bloklangan INTEGER DEFAULT 0",
        "ALTER TABLE mijozlar ADD COLUMN created_at TEXT",
        "ALTER TABLE mijozlar ADD COLUMN last_active TEXT",
        "ALTER TABLE statistika ADD COLUMN qoshimcha TEXT",
        "ALTER TABLE joylashgan ADD COLUMN xona_nomi TEXT",
        "ALTER TABLE joylashgan ADD COLUMN tugash TEXT",
        "ALTER TABLE joylashgan ADD COLUMN holat TEXT DEFAULT 'joylashgan'",
        "ALTER TABLE joylashgan ADD COLUMN narx INTEGER DEFAULT 0",
        "ALTER TABLE joylashgan ADD COLUMN tolangan INTEGER DEFAULT 0",
    ]:
        try:
            conn.execute(sql)
        except:
            pass

    # Boshlang'ich ma'lumotlar
    if not conn.execute("SELECT id FROM binolar WHERE id=1").fetchone():
        conn.execute("INSERT INTO binolar (id,nomi) VALUES (1,'1-bino')")

    if not conn.execute("SELECT id FROM xonalar LIMIT 1").fetchone():
        xonalar = [
            (1,1,"1-xona",1,3,300000),(1,2,"2-xona",1,3,300000),
            (1,3,"3-xona",1,7,700000),(1,4,"4-xona",1,7,700000),
            (1,5,"5-xona",2,3,300000),(1,6,"6-xona",2,3,300000),
            (1,7,"7-xona",2,3,300000),(1,8,"8-xona",2,3,300000),
            (1,9,"9-xona",2,3,300000),(1,10,"10-xona",2,3,300000),
        ]
        conn.executemany("INSERT INTO xonalar (bino_id,id,nomi,qavat,sigim,narx) VALUES (?,?,?,?,?,?)", xonalar)

    conn.execute("UPDATE xonalar SET bino_id=1 WHERE bino_id IS NULL")

    # joylashgan jadval migration
    for sql in [
        "ALTER TABLE joylashgan ADD COLUMN xona_nomi TEXT",
        "ALTER TABLE joylashgan ADD COLUMN sana TEXT",
        "ALTER TABLE joylashgan ADD COLUMN tugash TEXT",
        "ALTER TABLE joylashgan ADD COLUMN holat TEXT DEFAULT 'joylashgan'",
    ]:
        try:
            conn.execute(sql)
        except: pass

    for kalit, nomi in [("telegram","Telegram"),("instagram","Instagram"),("youtube","YouTube")]:
        try:
            conn.execute("INSERT OR IGNORE INTO ijtimoiy (kalit,link,nomi) VALUES (?,?,?)", (kalit,"",nomi))
        except: pass

    conn.commit()
    conn.close()


# ===== TIL =====
def get_til(uid):
    conn = get_db()
    r = conn.execute("SELECT til FROM til_jadval WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return r["til"] if r else None

def set_til(uid, til):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO til_jadval VALUES (?,?)", (uid, til))
    conn.commit()
    conn.close()


# ===== XONALAR =====
def get_xonalar(bino_id=None):
    conn = get_db()
    try:
        if bino_id:
            rows = conn.execute(
                "SELECT x.*, COALESCE(b.nomi,'1-bino') as bino_nomi FROM xonalar x LEFT JOIN binolar b ON x.bino_id=b.id WHERE x.bino_id=? AND x.aktiv=1 ORDER BY x.id",
                (bino_id,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT x.*, COALESCE(b.nomi,'1-bino') as bino_nomi FROM xonalar x LEFT JOIN binolar b ON x.bino_id=b.id WHERE x.aktiv=1 ORDER BY x.id").fetchall()
    except:
        rows = conn.execute("SELECT *, '1-bino' as bino_nomi FROM xonalar WHERE aktiv=1 ORDER BY id").fetchall()
    conn.close()
    return rows

def get_binolar():
    conn = get_db()
    rows = conn.execute("SELECT * FROM binolar WHERE aktiv=1").fetchall()
    conn.close()
    return rows

def xona_band_mi(xid, sana):
    conn = get_db()
    r = conn.execute("SELECT id FROM band WHERE xona_id=? AND sana=?", (xid, sana)).fetchone()
    conn.close()
    return r is not None


def _sana_qosh(sana_str, kun):
    return (datetime.strptime(sana_str, "%d.%m.%Y") + timedelta(days=kun)).strftime("%d.%m.%Y")


def xona_bosh_mi_oraliq(xid, bosh_sana, kunlar, istisno_guruh=None):
    """Xona [bosh_sana, bosh_sana+kunlar) oralig'ida JOYLASHTIRISH/BRON uchun bo'shmi?

    MUHIM QOIDA:
    - Yangi mehmon kelgan kuni xona band bo'lsa -> band (qo'yib bo'lmaydi)
    - LEKIN avvalgi mehmonning CHIQISH (tugash) kunida yangi mehmon kela oladi
      (12:00 da bo'shaydi). Ya'ni band[sana] mavjud bo'lsa-yu, lekin o'sha band
      yozuvi avvalgi bronning oxirgi (tugash) kuni bo'lsa - bu to'siq emas.

    istisno_guruh: shu guruh/bron o'zining bandini hisobga olmaslik (o'zgartirishda)
    Qaytaradi: (bosh_mi: bool, ziddiyat_sana: str|None)
    """
    conn = get_db()
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    for i in range(kunlar):
        sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
        rows = conn.execute("SELECT bron_id FROM band WHERE xona_id=? AND sana=?", (xid, sana)).fetchall()
        for row in rows:
            bid = row["bron_id"]
            if istisno_guruh and bid == istisno_guruh:
                continue
            # Bu band yozuvi qaysidir bronning/guruhning CHIQISH kunimi?
            # Agar shu sana o'sha bandning oxirgi kuni bo'lsa - bu chiqish kuni, to'siq emas.
            if _band_chiqish_kunimi(conn, xid, sana, bid):
                continue
            conn.close()
            return False, sana
    conn.close()
    return True, None


def _band_chiqish_kunimi(conn, xid, sana, bid):
    """band[xid, sana, bid] yozuvi shu xonadagi shu bron/guruhning oxirgi (chiqish) kunimi?
    Ya'ni ertasi kuni shu xona+bron uchun band yo'q bo'lsa - bu chiqish kuni."""
    ertaga = _sana_qosh(sana, 1)
    keyingi = conn.execute(
        "SELECT 1 FROM band WHERE xona_id=? AND sana=? AND bron_id=?",
        (xid, ertaga, bid)).fetchone()
    # Agar ertaga shu bron uchun band bo'lmasa - bugun chiqish kuni
    return keyingi is None


def xona_kunlar_band(xid, bosh_sana, kunlar):
    """Eski moslik uchun - oddiy band tekshiruvi (chiqish kuni hisobga olinmaydi)"""
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    for i in range(kunlar):
        sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
        if xona_band_mi(xid, sana):
            return True
    return False


def xona_kun_holati(xid, sana):
    """Xonaning berilgan kundagi holati:
    'bosh'      -> 🟢
    'band'      -> 🔴 (bron bor, hali kelmagan)
    'joylashgan'-> 🔵 (hozir ichida)
    'chiqish'   -> 🟡 (bugun tugash/chiqish sanasi - 12:00 da bo'shaydi)
    """
    conn = get_db()

    # Joylashgan (hozir ichida)?
    joy = conn.execute(
        "SELECT * FROM joylashgan WHERE xona_id=? AND sana<=? AND tugash>=? AND holat='joylashgan'",
        (xid, sana, sana)).fetchone()
    if joy:
        if joy["tugash"] == sana:
            conn.close()
            return "chiqish"
        conn.close()
        return "joylashgan"

    # Band (bron bor)?
    row = conn.execute("SELECT bron_id FROM band WHERE xona_id=? AND sana=?", (xid, sana)).fetchone()
    if row and row["bron_id"]:
        bid = row["bron_id"]
        # Shu bandning chiqish kunimi?
        if _band_chiqish_kunimi(conn, xid, sana, bid):
            conn.close()
            return "chiqish"
        conn.close()
        return "band"

    conn.close()
    return "bosh"


HOLAT_EMOJI = {
    "bosh":       "🟢",
    "band":       "🔴",
    "joylashgan": "🔵",
    "chiqish":    "🟡",
}


def xona_kim_band(xid, sana):
    """Shu xonani shu kuni kim band qilgan - bron/joylashish ma'lumoti (tugma uchun)"""
    conn = get_db()
    # Joylashgan
    joy = conn.execute(
        "SELECT * FROM joylashgan WHERE xona_id=? AND sana<=? AND tugash>=? AND holat='joylashgan'",
        (xid, sana, sana)).fetchone()
    if joy:
        conn.close()
        return {"tur": "joylashgan", "ism": joy["ism"], "telefon": joy["telefon"],
                "sana": joy["sana"], "tugash": joy["tugash"], "guruh_id": joy["guruh_id"],
                "id": joy["id"], "bron_id": joy["bron_id"]}
    # Band -> bron
    row = conn.execute("SELECT bron_id FROM band WHERE xona_id=? AND sana=?", (xid, sana)).fetchone()
    if row and row["bron_id"]:
        b = conn.execute("SELECT * FROM bronlar WHERE id=?", (row["bron_id"],)).fetchone()
        conn.close()
        if b:
            return {"tur": "bron", "ism": b["ism"], "telefon": b["telefon"],
                    "sana": b["sana"], "kunlar": b["kunlar"], "bron_id": b["id"],
                    "holat": b["holat"]}
        return None
    conn.close()
    return None


def xona_bugun_boshadimi(xid, sana):
    """Xona shu sanada band, lekin avvalgi bron tugash sanasi = shu sana bo'lsa True"""
    conn = get_db()
    row = conn.execute("SELECT bron_id FROM band WHERE xona_id=? AND sana=?", (xid, sana)).fetchone()
    if not row:
        conn.close()
        return False
    bid = row["bron_id"]
    if not bid or bid == "admin":
        conn.close()
        return False
    b = conn.execute("SELECT * FROM bronlar WHERE id=?", (bid,)).fetchone()
    conn.close()
    if not b:
        return False
    bosh = datetime.strptime(b["sana"], "%d.%m.%Y")
    tugash = (bosh + timedelta(days=b["kunlar"])).strftime("%d.%m.%Y")
    return tugash == sana  # Bu sana tugash sanasi = bugun bo'sh bo'ladi

def band_qil(xid, bosh_sana, kunlar, bron_id):
    """Xonani band qilish. Tugash kunini ham qo'shadi (chiqish kuni belgisi).
    04.06 dan 2 kun -> band 04,05,06 (06 chiqish kuni, boshqa kela oladi)."""
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    conn = get_db()
    for i in range(kunlar + 1):
        sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
        try:
            conn.execute("INSERT OR IGNORE INTO band (xona_id,sana,bron_id) VALUES (?,?,?)", (xid, sana, bron_id))
        except: pass
    conn.commit()
    conn.close()

def bosh_qil_bron(bron_id):
    conn = get_db()
    conn.execute("DELETE FROM band WHERE bron_id=?", (bron_id,))
    conn.commit()
    conn.close()

def bosh_qil_sana(xid, bosh_sana, kunlar):
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    conn = get_db()
    for i in range(kunlar):
        sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
        conn.execute("DELETE FROM band WHERE xona_id=? AND sana=?", (xid, sana))
    conn.commit()
    conn.close()


# ===== BRONLAR =====
def bron_id_gen():
    conn = get_db()
    while True:
        bid = random.choice(string.ascii_uppercase) + str(random.randint(100, 999))
        if not conn.execute("SELECT id FROM bronlar WHERE id=?", (bid,)).fetchone():
            conn.close()
            return bid

def get_bron(bron_id):
    conn = get_db()
    r = conn.execute("SELECT * FROM bronlar WHERE id=?", (bron_id,)).fetchone()
    conn.close()
    return r

def get_bron_xonalar(bron_id):
    conn = get_db()
    rows = conn.execute("SELECT xona_id FROM bron_xonalar WHERE bron_id=?", (bron_id,)).fetchall()
    conn.close()
    return [r["xona_id"] for r in rows]

def bekor_qil_bron(bron_id):
    conn = get_db()
    conn.execute("UPDATE bronlar SET holat='bekor' WHERE id=?", (bron_id,))
    conn.execute("DELETE FROM band WHERE bron_id=?", (bron_id,))
    conn.commit()
    conn.close()

def tugash_sanasi(bosh_sana, kunlar):
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y")
    return (bosh + timedelta(days=kunlar)).strftime("%d.%m.%Y")


# ===== JOYLASHGAN MEHMONLAR =====
def guruh_id_yarat():
    """Yangi joylash guruhi uchun noyob ID"""
    import random
    return "G" + datetime.now(TZ).strftime("%y%m%d%H%M%S") + str(random.randint(10, 99))


def xonaga_joylashtir(xona_id, xona_nomi, ism, telefon, kishi, sana, kunlar, bron_id="", guruh_id=None):
    """Bitta xonani joylashtirish. guruh_id berilsa - shu guruhga qo'shadi.
    band jadvaliga TUGASH KUNINI HAM yozadi (chiqish kuni belgisi uchun).
    Masalan 04.06 dan 2 kun: band = 04, 05, 06 (06 chiqish kuni)."""
    tugash = tugash_sanasi(sana, kunlar)
    if not guruh_id:
        guruh_id = guruh_id_yarat()
    conn = get_db()
    conn.execute(
        "INSERT INTO joylashgan (xona_id,xona_nomi,ism,telefon,kishi,sana,tugash,bron_id,holat,guruh_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (xona_id, xona_nomi, ism, telefon, kishi, sana, tugash, bron_id, "joylashgan", guruh_id))
    # band: sana dan tugash kunigacha (tugash ham kiradi - chiqish kuni)
    for i in range(kunlar + 1):
        sana_i = (datetime.strptime(sana, "%d.%m.%Y") + timedelta(days=i)).strftime("%d.%m.%Y")
        try:
            conn.execute("INSERT OR REPLACE INTO band (xona_id,sana,bron_id) VALUES (?,?,?)",
                        (xona_id, sana_i, guruh_id))
        except: pass
    conn.commit()
    conn.close()
    return guruh_id


def joylash_guruh(xona_royxat, ism, telefon, kishi, sana, kunlar, bron_id=""):
    """Bir nechta xonani BITTA guruh sifatida joylashtirish.
    xona_royxat = [(xona_id, xona_nomi), ...] yoki [(xona_id, xona_nomi, kishi), ...]
    Agar uchinchi element (kishi) berilsa - har xonaga o'sha kishi soni yoziladi.
    Aks holda umumiy kishi sig'imga qarab taqsimlanadi.
    Hammasi bitta guruh_id oladi - birga chiqadi/o'zgaradi."""
    guruh_id = guruh_id_yarat()
    # Har xona uchun kishi sonini aniqlash
    if xona_royxat and len(xona_royxat[0]) >= 3:
        # Har xona uchun kishi berilgan
        for item in xona_royxat:
            xid, xnomi, xkishi = item[0], item[1], item[2]
            xonaga_joylashtir(xid, xnomi, ism, telefon, xkishi, sana, kunlar, bron_id, guruh_id)
    else:
        # Umumiy kishini sig'imga qarab taqsimlash
        taqsim = _kishi_taqsimla(xona_royxat, kishi)
        for (xid, xnomi), xkishi in zip(xona_royxat, taqsim):
            xonaga_joylashtir(xid, xnomi, ism, telefon, xkishi, sana, kunlar, bron_id, guruh_id)
    return guruh_id


def _kishi_taqsimla(xona_royxat, jami_kishi):
    """Umumiy kishini xonalar sig'imiga qarab taqsimlaydi.
    Avval har xonani sig'imigacha to'ldiradi, ortiqchasini oxirgi xonaga qo'shadi."""
    conn = get_db()
    sigimlar = []
    for item in xona_royxat:
        xid = item[0]
        r = conn.execute("SELECT sigim FROM xonalar WHERE id=?", (xid,)).fetchone()
        sigimlar.append(r["sigim"] if r else 1)
    conn.close()
    taqsim = [0] * len(xona_royxat)
    qolgan = jami_kishi
    # Avval sig'imgacha to'ldirish
    for i, s in enumerate(sigimlar):
        olinadi = min(s, qolgan)
        taqsim[i] = olinadi
        qolgan -= olinadi
    # Ortiqcha qolsa - oxirgi xonaga qo'shish
    if qolgan > 0 and taqsim:
        taqsim[-1] += qolgan
    return taqsim


def chiqish_qil(joylashgan_id):
    """Bitta yozuvni chiqarish - guruhdagi BARCHA xonalarni birga chiqaradi.
    band jadvalini xona_id bo'yicha to'liq tozalaydi (bron orqali kelgan bo'lsa ham)."""
    conn = get_db()
    j = conn.execute("SELECT * FROM joylashgan WHERE id=?", (joylashgan_id,)).fetchone()
    if not j:
        conn.close()
        return None
    guruh_id = j["guruh_id"]
    if guruh_id:
        guruh_yozuvlar = conn.execute(
            "SELECT * FROM joylashgan WHERE guruh_id=? AND holat='joylashgan'",
            (guruh_id,)).fetchall()
    else:
        guruh_yozuvlar = [j]

    bron_idlar = set()
    for gy in guruh_yozuvlar:
        conn.execute("UPDATE joylashgan SET holat='chiqdi' WHERE id=?", (gy["id"],))
        # band ni shu xonaning shu mehmon sanalarida tozalash
        # Eng ishonchli: xona + sana oralig'i bo'yicha
        try:
            bosh = datetime.strptime(gy["sana"], "%d.%m.%Y").date()
            oxir = datetime.strptime(gy["tugash"], "%d.%m.%Y").date()
            kun = (oxir - bosh).days + 1
            for i in range(kun + 1):
                sana_i = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
                conn.execute("DELETE FROM band WHERE xona_id=? AND sana=?", (gy["xona_id"], sana_i))
        except:
            pass
        # guruh_id va bron_id bo'yicha ham tozalash
        if guruh_id:
            conn.execute("DELETE FROM band WHERE bron_id=? AND xona_id=?", (guruh_id, gy["xona_id"]))
        if gy["bron_id"]:
            bron_idlar.add(gy["bron_id"])
            conn.execute("DELETE FROM band WHERE bron_id=? AND xona_id=?", (gy["bron_id"], gy["xona_id"]))
    if guruh_id:
        conn.execute("DELETE FROM band WHERE bron_id=?", (guruh_id,))
    # Tegishli bronlarni 'chiqgan' qilish
    for bid in bron_idlar:
        if bid:
            conn.execute("UPDATE bronlar SET holat='chiqgan' WHERE id=?", (bid,))
    conn.commit()
    conn.close()
    return guruh_id


def guruh_chiqar(guruh_id):
    """Guruh ID bo'yicha to'g'ridan-to'g'ri chiqarish"""
    conn = get_db()
    yozuvlar = conn.execute(
        "SELECT * FROM joylashgan WHERE guruh_id=? AND holat='joylashgan'",
        (guruh_id,)).fetchall()
    for y in yozuvlar:
        conn.execute("UPDATE joylashgan SET holat='chiqdi' WHERE id=?", (y["id"],))
    conn.execute("DELETE FROM band WHERE bron_id=?", (guruh_id,))
    conn.commit()
    conn.close()


def guruh_olish(guruh_id):
    """Guruhdagi barcha joylashgan yozuvlar"""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM joylashgan WHERE guruh_id=? AND holat='joylashgan'",
        (guruh_id,)).fetchall()
    conn.close()
    return rows


def mehmon_kochir(joylashgan_id, yangi_xona_id, yangi_xona_nomi):
    """Mehmonni boshqa xonaga ko'chirish. Guruh_id saqlanadi (guruh buzilmaydi).
    Eski xona band'i sana oralig'i bo'yicha TO'LIQ tozalanadi (bron_id ga qaramay).
    Qaytaradi: (ok: bool, xabar: str)"""
    conn = get_db()
    j = conn.execute("SELECT * FROM joylashgan WHERE id=?", (joylashgan_id,)).fetchone()
    if not j:
        conn.close()
        return False, "Mehmon topilmadi"
    eski_xona = j["xona_id"]
    if eski_xona == yangi_xona_id:
        conn.close()
        return False, "Bu allaqachon shu xona"
    guruh_id = j["guruh_id"] or j["bron_id"] or f"joylashgan_{eski_xona}"

    # Mehmonning sana oralig'i (sana ... tugash, tugash kuni ham)
    try:
        bosh = datetime.strptime(j["sana"], "%d.%m.%Y").date()
        oxir = datetime.strptime(j["tugash"], "%d.%m.%Y").date()
        kun = (oxir - bosh).days
        sanalar = [(bosh + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(kun + 1)]
    except:
        # Zaxira: band dan
        eski_band = conn.execute("SELECT sana FROM band WHERE xona_id=? AND bron_id=?",
                                 (eski_xona, guruh_id)).fetchall()
        sanalar = [b["sana"] for b in eski_band]

    # Yangi xona shu sanalarda bo'shmi (o'zinikidan tashqari) — chiqish kuni qoidasi bilan
    for s in sanalar:
        row = conn.execute("SELECT bron_id FROM band WHERE xona_id=? AND sana=?",
                           (yangi_xona_id, s)).fetchone()
        if row and row["bron_id"] and row["bron_id"] != guruh_id:
            bid = row["bron_id"]
            # Chiqish kuni bo'lsa to'siq emas
            ertaga = (datetime.strptime(s, "%d.%m.%Y") + timedelta(days=1)).strftime("%d.%m.%Y")
            keyingi = conn.execute("SELECT 1 FROM band WHERE xona_id=? AND sana=? AND bron_id=?",
                                   (yangi_xona_id, ertaga, bid)).fetchone()
            if keyingi:  # ertaga ham band - haqiqiy to'siq
                conn.close()
                return False, f"{yangi_xona_nomi} {s} sanada band — ko'chirib bo'lmaydi"

    # 1. joylashgan yozuvni yangilash (guruh_id O'ZGARMAYDI - guruh saqlanadi)
    conn.execute("UPDATE joylashgan SET xona_id=?, xona_nomi=? WHERE id=?",
                 (yangi_xona_id, yangi_xona_nomi, joylashgan_id))

    # 2. Eski xonadan shu sanalardagi band'ni TO'LIQ o'chirish (bron_id ga qaramay)
    #    (bir xona bir vaqtda bitta mehmonники, shuning uchun xavfsiz)
    for s in sanalar:
        conn.execute("DELETE FROM band WHERE xona_id=? AND sana=?", (eski_xona, s))

    # 3. Yangi xonaga band qo'shish (guruh_id bilan)
    for s in sanalar:
        conn.execute("INSERT OR REPLACE INTO band (xona_id,sana,bron_id) VALUES (?,?,?)",
                    (yangi_xona_id, s, guruh_id))

    # 4. Eski xonani iflos belgilash
    conn.execute("UPDATE xonalar SET tozalik='iflos' WHERE id=?", (eski_xona,))
    conn.commit()
    conn.close()
    return True, f"{yangi_xona_nomi} ga ko'chirildi"


def hozirgi_mehmonlar():
    """Hozir joylashgan mehmonlar - guruh bo'yicha guruhlangan"""
    bugun = datetime.now(TZ).strftime("%d.%m.%Y")
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM joylashgan WHERE holat='joylashgan' AND tugash >= ? ORDER BY guruh_id, xona_id",
        (bugun,)).fetchall()
    conn.close()
    return rows

def bugungi_keluvchilar():
    bugun = datetime.now(TZ).strftime("%d.%m.%Y")
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM bronlar WHERE sana=? AND holat='tasdiqlangan'",
        (bugun,)).fetchall()
    conn.close()
    return rows


# ===== MIJOZLAR =====
def saqlash_mijoz(user_id, ism=None, username=None):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    conn = get_db()
    m = conn.execute("SELECT user_id FROM mijozlar WHERE user_id=?", (user_id,)).fetchone()
    if not m:
        try:
            conn.execute(
                "INSERT INTO mijozlar (user_id,ism,username,created_at,last_active) VALUES (?,?,?,?,?)",
                (user_id, ism or "", username or "", now, now))
        except:
            try:
                conn.execute("INSERT INTO mijozlar (user_id,ism,username) VALUES (?,?,?)",
                             (user_id, ism or "", username or ""))
            except: pass
    else:
        try:
            conn.execute("UPDATE mijozlar SET last_active=? WHERE user_id=?", (now, user_id))
        except: pass
    conn.commit()
    conn.close()

def qidir_mijoz(qidiruv):
    conn = get_db()
    q = qidiruv.strip()
    b = conn.execute("SELECT * FROM bronlar WHERE id=?", (q.upper(),)).fetchone()
    if b:
        m = conn.execute("SELECT * FROM mijozlar WHERE user_id=?", (b["user_id"],)).fetchone()
        conn.close()
        return {"bron": dict(b), "mijoz": dict(m) if m else None}
    for tel in [q, "+998"+q.lstrip("+0"), "998"+q.lstrip("+")]:
        m = conn.execute("SELECT * FROM mijozlar WHERE telefon=?", (tel,)).fetchone()
        if m:
            conn.close()
            return {"mijoz": dict(m), "bron": None}
    if len(q) >= 9:
        all_m = conn.execute("SELECT * FROM mijozlar").fetchall()
        for m in all_m:
            if m["telefon"] and str(m["telefon"])[-9:] == q[-9:]:
                conn.close()
                return {"mijoz": dict(m), "bron": None}
    m = conn.execute("SELECT * FROM mijozlar WHERE username=?", (q.lstrip("@"),)).fetchone()
    if m:
        conn.close()
        return {"mijoz": dict(m), "bron": None}
    conn.close()
    return None


# ===== ADMIN =====
def is_director(uid):
    return uid in DIRECTOR_IDS

def is_admin(uid):
    if uid in DIRECTOR_IDS:
        return True
    conn = get_db()
    r = conn.execute("SELECT user_id FROM adminlar WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return r is not None

def format_narx(n):
    return f"{n:,}".replace(",", " ")


# ===== IJTIMOIY =====
def get_ijtimoiy():
    conn = get_db()
    rows = conn.execute("SELECT * FROM ijtimoiy").fetchall()
    conn.close()
    return {r["kalit"]: {"link": r["link"], "nomi": r["nomi"]} for r in rows}

def set_ijtimoiy(kalit, link):
    conn = get_db()
    conn.execute("UPDATE ijtimoiy SET link=? WHERE kalit=?", (link, kalit))
    conn.commit()
    conn.close()


# ===== STATISTIKA =====
def log_stat(user_id, harakat, qoshimcha=""):
    try:
        conn = get_db()
        conn.execute("INSERT INTO statistika (user_id,harakat,qoshimcha,vaqt) VALUES (?,?,?,?)",
                     (user_id, harakat, qoshimcha, datetime.now().strftime("%d.%m.%Y %H:%M")))
        conn.commit()
        conn.close()
    except: pass

def bugungi_stat():
    bugun = datetime.now(TZ).strftime("%d.%m.%Y")
    conn = get_db()
    f = conn.execute("SELECT COUNT(DISTINCT user_id) as c FROM statistika WHERE vaqt LIKE ?", (f"{bugun}%",)).fetchone()["c"]
    h = conn.execute("SELECT harakat, COUNT(*) as c FROM statistika WHERE vaqt LIKE ? GROUP BY harakat ORDER BY c DESC LIMIT 8", (f"{bugun}%",)).fetchall()
    b = conn.execute("SELECT COUNT(*) as c FROM bronlar WHERE created_at LIKE ?", (f"{bugun}%",)).fetchone()["c"]
    conn.close()
    return {"foydalanuvchilar": f, "harakatlar": h, "bronlar": b}

def kengaytirilgan_stat():
    bugun = datetime.now(TZ).strftime("%d.%m.%Y")
    hafta = (datetime.now() - timedelta(days=7)).strftime("%d.%m.%Y")
    oy = datetime.now().strftime("%d.%m.")
    conn = get_db()
    bugun_f = conn.execute("SELECT COUNT(DISTINCT user_id) as c FROM statistika WHERE vaqt LIKE ?", (f"{bugun}%",)).fetchone()["c"]
    hafta_f = conn.execute("SELECT COUNT(DISTINCT user_id) as c FROM statistika WHERE vaqt >= ?", (hafta,)).fetchone()["c"]
    oy_f = conn.execute("SELECT COUNT(DISTINCT user_id) as c FROM statistika WHERE vaqt LIKE ?", (f"%{oy}%",)).fetchone()["c"]
    harakatlar = conn.execute("SELECT harakat, COUNT(*) as c FROM statistika GROUP BY harakat ORDER BY c DESC LIMIT 10").fetchall()
    soatlar = conn.execute("SELECT substr(vaqt, 12, 2) as soat, COUNT(*) as c FROM statistika GROUP BY soat ORDER BY soat").fetchall()
    jami_bronlar = conn.execute("SELECT COUNT(*) as c FROM bronlar").fetchone()["c"]
    tasdiq_bronlar = conn.execute("SELECT COUNT(*) as c FROM bronlar WHERE holat='tasdiqlangan'").fetchone()["c"]
    jami_mijozlar = conn.execute("SELECT COUNT(*) as c FROM mijozlar").fetchone()["c"]
    conn.close()
    return {"bugun": bugun_f, "hafta": hafta_f, "oy": oy_f,
            "harakatlar": harakatlar, "soatlar": soatlar,
            "jami_bronlar": jami_bronlar, "tasdiq_bronlar": tasdiq_bronlar,
            "jami_mijozlar": jami_mijozlar}


# ===== KOMBINATSIYA =====
def barcha_variantlar(kishi, guruh, sana, kunlar=1, max_ortiqcha=None):
    """Berilgan kishi soni uchun xona variantlari.
    Chiqish-kuni mantig'i bilan (xona_bosh_mi_oraliq).
    max_ortiqcha: bitta xonaga sig'imdan ortiq joylashning maksimal soni.
       None = cheksiz (admin). Mijoz uchun 2 beriladi.
    Variantlar: bitta to'liq mos, kombinatsiyalar, va ortiqcha (1 xonaga ko'p kishi)."""
    xonalar = get_xonalar()
    bosh = []
    for x in xonalar:
        xd = dict(x)
        if xd.get("yopiq", 0):
            continue
        ok, _ = xona_bosh_mi_oraliq(xd["id"], sana, kunlar)
        if ok:
            bosh.append(xd)
    if not bosh:
        return []

    afzal_qavat = 1 if guruh == "oila" else 2
    variantlar = []
    korilgan = set()  # takror oldini olish (xona id lar to'plami)

    def kalit(xlist):
        return tuple(sorted(x["id"] for x in xlist))

    # 1. Bitta xona - to'liq mos (eng kichik mosi)
    for x in sorted(bosh, key=lambda a: a["sigim"]):
        if x["sigim"] >= kishi:
            k = kalit([x])
            if k not in korilgan:
                korilgan.add(k)
                variantlar.append({"xonalar": [x], "tur": "bitta",
                                   "jami_sigim": x["sigim"], "ortiqcha": x["sigim"] - kishi})
            break

    # 1b. Ortiqcha joylash - bitta xonaga sig'imdan ko'p kishi
    # (masalan 5 kishi 3 kishilik xonada). Eng katta xonadan boshlab.
    for x in sorted(bosh, key=lambda a: a["sigim"], reverse=True):
        if x["sigim"] < kishi:
            ortiqcha = kishi - x["sigim"]
            if max_ortiqcha is not None and ortiqcha > max_ortiqcha:
                continue
            k = kalit([x])
            if k not in korilgan:
                korilgan.add(k)
                variantlar.append({"xonalar": [x], "tur": "ortiqcha",
                                   "jami_sigim": x["sigim"], "ortiqcha": -ortiqcha})
            break

    # 2. Kombinatsiyalar (2-3 xona) - turli yondashuvlar
    def topish(kishi_qolgan, mavjud, tanlangan):
        if kishi_qolgan <= 0:
            return tanlangan
        if not mavjud:
            return None
        for x in mavjud:
            if x["sigim"] >= kishi_qolgan:
                return tanlangan + [x]
        x = mavjud[0]
        natija = topish(kishi_qolgan - x["sigim"], mavjud[1:], tanlangan + [x])
        if natija:
            return natija
        return topish(kishi_qolgan, mavjud[1:], tanlangan)

    afzal = sorted([x for x in bosh if x["qavat"] == afzal_qavat], key=lambda a: a["sigim"], reverse=True)
    boshqa = sorted([x for x in bosh if x["qavat"] != afzal_qavat], key=lambda a: a["sigim"], reverse=True)
    kichikdan = sorted(bosh, key=lambda a: a["sigim"])  # kichik xonalardan yig'ish

    # Kichik xonalardan kombinatsiya (masalan 4 kishi -> 3+3)
    def topish_kichik(kishi_qolgan, mavjud, tanlangan):
        if kishi_qolgan <= 0:
            return tanlangan
        if not mavjud:
            return None
        x = mavjud[0]
        n = topish_kichik(kishi_qolgan - x["sigim"], mavjud[1:], tanlangan + [x])
        if n:
            return n
        return topish_kichik(kishi_qolgan, mavjud[1:], tanlangan)

    for tartib, fn in [(afzal + boshqa, topish), (boshqa + afzal, topish),
                       (kichikdan, topish_kichik)]:
        kom = fn(kishi, tartib, [])
        if kom and len(kom) > 1:
            k = kalit(kom)
            if k not in korilgan:
                korilgan.add(k)
                jami = sum(x["sigim"] for x in kom)
                variantlar.append({"xonalar": kom, "tur": "kombinatsiya",
                                   "jami_sigim": jami, "ortiqcha": jami - kishi})

    # Tartiblash: sig'adigan variantlar birinchi, ortiqcha (sig'maydigan) oxirida
    def tartib_kalit(v):
        ortiqcha_joylash = 1 if v["tur"] == "ortiqcha" else 0
        return (ortiqcha_joylash, len(v["xonalar"]), abs(v["ortiqcha"]))
    variantlar.sort(key=tartib_kalit)
    return variantlar[:6]


def bosh_xonalar_royxat(sana, kunlar=1):
    """Berilgan oraliqda bo'sh (yoki chiqadigan) barcha xonalar - admin qo'lda tanlashi uchun"""
    xonalar = get_xonalar()
    natija = []
    for x in xonalar:
        xd = dict(x)
        if xd.get("yopiq", 0):
            continue
        ok, _ = xona_bosh_mi_oraliq(xd["id"], sana, kunlar)
        if ok:
            natija.append(xd)
    return natija


def mos_kombinatsiya(kishi, guruh, sana, kunlar=1):
    v = barcha_variantlar(kishi, guruh, sana, kunlar)
    return v[0:1] if v else []



# ===== MIJOZ PROFILI =====
def mijoz_profil(qidiruv):
    """Mijozning to'liq profili: ma'lumot + bronlar + joylashishlar + statistika.
    qidiruv: telefon, ism, bron ID yoki user_id"""
    conn = get_db()
    q = qidiruv.strip()

    # Mijozni topish (telefon yoki ism orqali)
    mijoz = None
    bronlar = []

    # Bron ID orqali
    b = conn.execute("SELECT * FROM bronlar WHERE id=?", (q.upper(),)).fetchone()
    if b:
        tel = b["telefon"]
        ism = b["ism"]
    else:
        # Telefon orqali
        tel = None
        ism = None
        # Telefon variantlari
        for t in [q, "+998" + q.lstrip("+0"), "998" + q.lstrip("+")]:
            bb = conn.execute("SELECT * FROM bronlar WHERE telefon=? LIMIT 1", (t,)).fetchone()
            if bb:
                tel = bb["telefon"]
                ism = bb["ism"]
                break
        # Oxirgi 9 raqam
        if not tel and len(q) >= 9:
            allb = conn.execute("SELECT * FROM bronlar").fetchall()
            for bb in allb:
                if bb["telefon"] and str(bb["telefon"])[-9:] == q[-9:]:
                    tel = bb["telefon"]
                    ism = bb["ism"]
                    break
        # Ism orqali
        if not tel:
            bb = conn.execute("SELECT * FROM bronlar WHERE ism LIKE ? LIMIT 1", (f"%{q}%",)).fetchone()
            if bb:
                tel = bb["telefon"]
                ism = bb["ism"]

        # Bronlarda topilmadi - joylashgan jadvaldan qidirish
        if not tel:
            for t in [q, "+998" + q.lstrip("+0"), "998" + q.lstrip("+")]:
                jj = conn.execute("SELECT * FROM joylashgan WHERE telefon=? LIMIT 1", (t,)).fetchone()
                if jj:
                    tel = jj["telefon"]
                    ism = jj["ism"]
                    break
        if not tel and len(q) >= 9:
            allj = conn.execute("SELECT * FROM joylashgan").fetchall()
            for jj in allj:
                if jj["telefon"] and str(jj["telefon"])[-9:] == q[-9:]:
                    tel = jj["telefon"]
                    ism = jj["ism"]
                    break
        if not tel:
            jj = conn.execute("SELECT * FROM joylashgan WHERE ism LIKE ? LIMIT 1", (f"%{q}%",)).fetchone()
            if jj:
                tel = jj["telefon"]
                ism = jj["ism"]

    if not tel:
        conn.close()
        return None

    # Shu telefon bo'yicha barcha bronlar
    bronlar = conn.execute(
        "SELECT * FROM bronlar WHERE telefon=? ORDER BY created_at DESC", (tel,)).fetchall()
    # Shu telefon bo'yicha barcha joylashishlar
    joylashishlar = conn.execute(
        "SELECT * FROM joylashgan WHERE telefon=? ORDER BY id DESC", (tel,)).fetchall()
    # Mijoz yozuvi
    mijoz = conn.execute("SELECT * FROM mijozlar WHERE telefon=?", (tel,)).fetchone()

    conn.close()

    # Statistika
    jami_bron = len(bronlar)
    jami_joylash = len([j for j in joylashishlar])
    jami_xarajat = sum(b["narx"] or 0 for b in bronlar if b["holat"] in ("tasdiqlangan", "joylashgan"))
    faol_bron = [b for b in bronlar if b["holat"] in ("kutilmoqda", "tasdiqlangan")]
    hozir_ichida = [j for j in joylashishlar if j["holat"] == "joylashgan"]

    return {
        "ism": ism,
        "telefon": tel,
        "mijoz": dict(mijoz) if mijoz else None,
        "bronlar": [dict(b) for b in bronlar],
        "joylashishlar": [dict(j) for j in joylashishlar],
        "jami_bron": jami_bron,
        "jami_joylash": jami_joylash,
        "jami_xarajat": jami_xarajat,
        "faol_bron": [dict(b) for b in faol_bron],
        "hozir_ichida": [dict(j) for j in hozir_ichida],
    }


def barcha_mijozlar(limit=50):
    """Barcha mijozlar ro'yxati (bronlar asosida, takrorlanmas telefon)"""
    conn = get_db()
    rows = conn.execute("""
        SELECT telefon, ism, COUNT(*) as bron_soni, MAX(created_at) as oxirgi,
               SUM(CASE WHEN holat IN ('tasdiqlangan','joylashgan') THEN narx ELSE 0 END) as jami
        FROM bronlar
        WHERE telefon IS NOT NULL AND telefon != ''
        GROUP BY telefon
        ORDER BY oxirgi DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


# ===== BRON O'ZGARTIRISH (xavfsiz) =====
def bron_yangila(bron_id, yangi_sana=None, yangi_kunlar=None, yangi_kishi=None):
    """Bronni o'zgartirish + band jadvalini qayta hisoblash (ustiga bron bo'lmasligi uchun)"""
    conn = get_db()
    b = conn.execute("SELECT * FROM bronlar WHERE id=?", (bron_id,)).fetchone()
    if not b:
        conn.close()
        return False, "Bron topilmadi"

    sana = yangi_sana or b["sana"]
    kunlar = yangi_kunlar or b["kunlar"]
    kishi = yangi_kishi if yangi_kishi is not None else b["kishi"]

    # Shu bronning xonalari
    xonalar = conn.execute("SELECT xona_id FROM bron_xonalar WHERE bron_id=?", (bron_id,)).fetchall()
    xona_ids = [x["xona_id"] for x in xonalar]

    # Yangi sanalarda ziddiyat (boshqa bron) bormi tekshirish
    from datetime import datetime as dt, timedelta as td
    bosh = dt.strptime(sana, "%d.%m.%Y")
    ziddiyat = []
    for xid in xona_ids:
        for i in range(kunlar):
            sana_i = (bosh + td(days=i)).strftime("%d.%m.%Y")
            band = conn.execute(
                "SELECT bron_id FROM band WHERE xona_id=? AND sana=? AND bron_id!=?",
                (xid, sana_i, bron_id)).fetchone()
            if band:
                ziddiyat.append((xid, sana_i, band["bron_id"]))

    if ziddiyat:
        conn.close()
        kunlar_str = ", ".join(f"{z[1]}" for z in ziddiyat[:3])
        return False, f"Ziddiyat: {kunlar_str} sanalarida boshqa bron bor"

    # Eski band yozuvlarni o'chir
    conn.execute("DELETE FROM band WHERE bron_id=?", (bron_id,))
    # Yangi band yozuvlar
    for xid in xona_ids:
        for i in range(kunlar):
            sana_i = (bosh + td(days=i)).strftime("%d.%m.%Y")
            try:
                conn.execute("INSERT OR REPLACE INTO band (xona_id,sana,bron_id) VALUES (?,?,?)",
                            (xid, sana_i, bron_id))
            except: pass

    # Bronni yangilash
    conn.execute("UPDATE bronlar SET sana=?, kunlar=?, kishi=? WHERE id=?",
                 (sana, kunlar, kishi, bron_id))
    conn.commit()
    conn.close()
    return True, "Yangilandi"


def joylash_uzaytir(joylashgan_id, qoshimcha_kun):
    """Joylashgan mehmonning turishini uzaytirish - guruhdagi hammasini birga"""
    conn = get_db()
    j = conn.execute("SELECT * FROM joylashgan WHERE id=?", (joylashgan_id,)).fetchone()
    if not j:
        conn.close()
        return False, "Topilmadi"
    guruh_id = j["guruh_id"]
    from datetime import datetime as dt, timedelta as td

    # Guruhdagi barcha xonalar
    if guruh_id:
        yozuvlar = conn.execute(
            "SELECT * FROM joylashgan WHERE guruh_id=? AND holat='joylashgan'",
            (guruh_id,)).fetchall()
    else:
        yozuvlar = [j]
        guruh_id = j["bron_id"] or f"joylashgan_{j['xona_id']}"

    # Ziddiyat tekshirish
    for y in yozuvlar:
        eski_tugash = dt.strptime(y["tugash"], "%d.%m.%Y")
        for i in range(qoshimcha_kun):
            sana_i = (eski_tugash + td(days=i)).strftime("%d.%m.%Y")
            band = conn.execute(
                "SELECT bron_id FROM band WHERE xona_id=? AND sana=? AND bron_id!=?",
                (y["xona_id"], sana_i, guruh_id)).fetchone()
            if band:
                conn.close()
                return False, f"{sana_i} da {y['xona_nomi']} band"

    # Uzaytirish
    for y in yozuvlar:
        eski_tugash = dt.strptime(y["tugash"], "%d.%m.%Y")
        yangi_tugash = (eski_tugash + td(days=qoshimcha_kun)).strftime("%d.%m.%Y")
        conn.execute("UPDATE joylashgan SET tugash=? WHERE id=?", (yangi_tugash, y["id"]))
        for i in range(qoshimcha_kun):
            sana_i = (eski_tugash + td(days=i)).strftime("%d.%m.%Y")
            try:
                conn.execute("INSERT OR REPLACE INTO band (xona_id,sana,bron_id) VALUES (?,?,?)",
                            (y["xona_id"], sana_i, guruh_id))
            except: pass
    conn.commit()
    conn.close()
    return True, f"{qoshimcha_kun} kun uzaytirildi"


# ===== SOZLAMA =====
def sozlama_ol(kalit, default=None):
    conn = get_db()
    r = conn.execute("SELECT qiymat FROM sozlama WHERE kalit=?", (kalit,)).fetchone()
    conn.close()
    return r["qiymat"] if r else default


def sozlama_saqla(kalit, qiymat):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO sozlama (kalit, qiymat) VALUES (?,?)", (kalit, str(qiymat)))
    conn.commit()
    conn.close()


# ===== NARX HISOBI =====
def narx_hisobla(xona, kishi, kunlar):
    """Narx hisobi.
    rejim 'xona': xona narxi * kunlar (kishi soniga qaramaydi)
    rejim 'kishi': sig'imgacha xona narxi, sig'imdan ortig'iga per-person qo'shimcha
       per_person = xona_narxi / sigim
       narx = max(xona_narxi, kishi * per_person) * kunlar
       Misol: 3 kishilik 300k -> 2 kishi=300k, 4 kishi=400k, 5 kishi=500k
    """
    narx = xona["narx"] or 0
    sigim = xona["sigim"] or 1
    kishi = kishi or 1
    rejim = sozlama_ol("narx_rejim", "xona")
    if rejim == "kishi":
        per = narx / sigim if sigim else narx
        bir_kun = max(narx, kishi * per)
        return int(round(bir_kun)) * kunlar
    return narx * kunlar


def guruh_narx_hisobla(xona_royxat_obj, kishi, kunlar):
    """Bir yoki bir nechta xona uchun jami narx.
    rejim 'xona': xona narxlari yig'indisi * kunlar
    rejim 'kishi': sig'imgacha xonalar narxi, ortig'iga o'rtacha per-person qo'shimcha
    """
    if not xona_royxat_obj:
        return 0
    kishi = kishi or 1
    jami_narx = sum((x["narx"] or 0) for x in xona_royxat_obj)
    jami_sigim = sum((x["sigim"] or 0) for x in xona_royxat_obj) or 1
    rejim = sozlama_ol("narx_rejim", "xona")
    if rejim == "kishi":
        per = jami_narx / jami_sigim if jami_sigim else jami_narx
        bir_kun = max(jami_narx, kishi * per)
        return int(round(bir_kun)) * kunlar
    return jami_narx * kunlar


# ===== TO'LOV =====
def tolov_qosh(bron_id, summa, izoh=None, guruh_id=None):
    conn = get_db()
    conn.execute("INSERT INTO tolovlar (bron_id, guruh_id, summa, izoh, sana) VALUES (?,?,?,?,?)",
                 (bron_id, guruh_id, summa, izoh, datetime.now(TZ).strftime("%d.%m.%Y %H:%M")))
    # bronlar.tolangan ni yangilash
    if bron_id:
        b = conn.execute("SELECT tolangan FROM bronlar WHERE id=?", (bron_id,)).fetchone()
        if b:
            yangi = (b["tolangan"] or 0) + summa
            conn.execute("UPDATE bronlar SET tolangan=? WHERE id=?", (yangi, bron_id))
    conn.commit()
    conn.close()


def tolov_holati(bron_id):
    """Bron to'lov holati: {jami, tolangan, qarz, holat}"""
    conn = get_db()
    b = conn.execute("SELECT narx, tolangan FROM bronlar WHERE id=?", (bron_id,)).fetchone()
    conn.close()
    if not b:
        return None
    jami = b["narx"] or 0
    tolangan = b["tolangan"] or 0
    qarz = jami - tolangan
    if tolangan == 0:
        holat = "tolanmagan"
    elif qarz <= 0:
        holat = "tolangan"
    else:
        holat = "qisman"
    return {"jami": jami, "tolangan": tolangan, "qarz": qarz, "holat": holat}


# ===== TOZALASH HOLATI =====
def xona_tozalik_ol(xid):
    conn = get_db()
    r = conn.execute("SELECT tozalik FROM xonalar WHERE id=?", (xid,)).fetchone()
    conn.close()
    return (dict(r).get("tozalik") if r else "toza") or "toza"


def xona_tozalik_belgila(xid, holat):
    """holat: 'toza' yoki 'iflos'"""
    conn = get_db()
    conn.execute("UPDATE xonalar SET tozalik=? WHERE id=?", (holat, xid))
    conn.commit()
    conn.close()


# ===== CHECK-IN =====
def checkin_belgila(bron_id):
    conn = get_db()
    conn.execute("UPDATE bronlar SET checkin=1 WHERE id=?", (bron_id,))
    conn.commit()
    conn.close()


# ===== DAROMAD HISOBOTI =====
def daromad_hisobot(bosh_sana=None, oxir_sana=None):
    """Davr bo'yicha daromad. To'lovlar asosida."""
    conn = get_db()
    if bosh_sana and oxir_sana:
        rows = conn.execute("SELECT summa, sana FROM tolovlar").fetchall()
        jami = 0
        for r in rows:
            try:
                d = datetime.strptime(r["sana"].split()[0], "%d.%m.%Y").date()
                b = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
                o = datetime.strptime(oxir_sana, "%d.%m.%Y").date()
                if b <= d <= o:
                    jami += r["summa"] or 0
            except:
                pass
        conn.close()
        return jami
    else:
        r = conn.execute("SELECT COALESCE(SUM(summa),0) as j FROM tolovlar").fetchone()
        conn.close()
        return r["j"]


def kunlik_daromad(sana):
    conn = get_db()
    rows = conn.execute("SELECT summa, sana FROM tolovlar").fetchall()
    conn.close()
    jami = 0
    for r in rows:
        if r["sana"] and r["sana"].split()[0] == sana:
            jami += r["summa"] or 0
    return jami


# ===== XARAJAT (RASXOD) =====
def xarajat_qosh(summa, izoh, admin_id=None):
    conn = get_db()
    conn.execute("INSERT INTO xarajatlar (summa, izoh, sana, admin_id) VALUES (?,?,?,?)",
                 (summa, izoh, datetime.now(TZ).strftime("%d.%m.%Y %H:%M"), admin_id))
    conn.commit()
    conn.close()


def xarajat_hisobot(bosh_sana=None, oxir_sana=None):
    """Davr bo'yicha jami xarajat"""
    conn = get_db()
    rows = conn.execute("SELECT summa, sana FROM xarajatlar").fetchall()
    conn.close()
    if not (bosh_sana and oxir_sana):
        return sum(r["summa"] or 0 for r in rows)
    jami = 0
    b = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    o = datetime.strptime(oxir_sana, "%d.%m.%Y").date()
    for r in rows:
        try:
            d = datetime.strptime(r["sana"].split()[0], "%d.%m.%Y").date()
            if b <= d <= o:
                jami += r["summa"] or 0
        except:
            pass
    return jami


def xarajat_royxat(limit=20):
    conn = get_db()
    rows = conn.execute("SELECT * FROM xarajatlar ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return rows


def daromad_tozalash():
    """Barcha to'lov yozuvlarini o'chirish (daromad hisobini noldan boshlash)"""
    conn = get_db()
    conn.execute("DELETE FROM tolovlar")
    conn.commit()
    conn.close()


def xarajat_tozalash():
    conn = get_db()
    conn.execute("DELETE FROM xarajatlar")
    conn.commit()
    conn.close()


def xona_toliq_tozala(xid):
    """Xonadagi BARCHA narsani tozalaydi: band, faol joylashganlar, va shu xonaga
    bog'liq tasdiqlanmagan/kutilayotgan bronlar. Orphan band uchun ishonchli yechim."""
    conn = get_db()
    # Faol joylashganlarni chiqdi qilish
    conn.execute("UPDATE joylashgan SET holat='chiqdi' WHERE xona_id=? AND holat='joylashgan'", (xid,))
    # Shu xonaga bog'liq bronlarni topib, agar boshqa xonasi bo'lmasa bekor qilish
    bids = conn.execute("SELECT DISTINCT bron_id FROM bron_xonalar WHERE xona_id=?", (xid,)).fetchall()
    for r in bids:
        bid = r["bron_id"]
        b = conn.execute("SELECT holat FROM bronlar WHERE id=?", (bid,)).fetchone()
        if b and b["holat"] in ("kutilmoqda", "tasdiqlangan"):
            # Shu bronning boshqa xonalari bormi
            boshqa = conn.execute(
                "SELECT COUNT(*) FROM bron_xonalar WHERE bron_id=? AND xona_id!=?", (bid, xid)).fetchone()[0]
            if boshqa == 0:
                conn.execute("UPDATE bronlar SET holat='bekor' WHERE id=?", (bid,))
            conn.execute("DELETE FROM bron_xonalar WHERE bron_id=? AND xona_id=?", (bid, xid))
    # Barcha band yozuvlarini o'chirish (orphan ham)
    conn.execute("DELETE FROM band WHERE xona_id=?", (xid,))
    conn.commit()
    conn.close()
