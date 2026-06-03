import sqlite3
import os
from datetime import datetime, timedelta
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
        aktiv INTEGER DEFAULT 1
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
        ism TEXT,
        telefon TEXT,
        kishi INTEGER,
        boshlanish TEXT,
        tugash TEXT,
        bron_id TEXT
    );
    """)

    # Migrations
    for sql in [
        "ALTER TABLE xonalar ADD COLUMN bino_id INTEGER DEFAULT 1",
        "ALTER TABLE xonalar ADD COLUMN aktiv INTEGER DEFAULT 1",
        "ALTER TABLE xonalar ADD COLUMN yopiq INTEGER DEFAULT 0",
        "ALTER TABLE bronlar ADD COLUMN holat TEXT DEFAULT 'kutilmoqda'",
        "ALTER TABLE mijozlar ADD COLUMN bloklangan INTEGER DEFAULT 0",
        "ALTER TABLE mijozlar ADD COLUMN created_at TEXT",
        "ALTER TABLE mijozlar ADD COLUMN last_active TEXT",
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
    
    # Ijtimoiy tarmoqlar boshlang'ich
    for kalit, nomi in [("telegram", "Telegram"), ("instagram", "Instagram"), ("youtube", "YouTube")]:
        try:
            conn.execute("INSERT OR IGNORE INTO ijtimoiy (kalit,link,nomi) VALUES (?,?,?)", (kalit, "", nomi))
        except: pass
    
    # Statistika migration
    try:
        conn.execute("ALTER TABLE statistika ADD COLUMN qoshimcha TEXT")
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


def xona_kunlar_band(xid, bosh_sana, kunlar):
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    for i in range(kunlar):
        sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
        if xona_band_mi(xid, sana):
            return True
    return False


def band_qil(xid, bosh_sana, kunlar, bron_id):
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    conn = get_db()
    for i in range(kunlar):
        sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
        try:
            conn.execute("INSERT OR IGNORE INTO band (xona_id,sana,bron_id) VALUES (?,?,?)", (xid, sana, bron_id))
        except:
            pass
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
        except Exception as e:
            try:
                conn.execute("INSERT INTO mijozlar (user_id,ism,username) VALUES (?,?,?)",
                             (user_id, ism or "", username or ""))
            except:
                pass
    else:
        try:
            conn.execute("UPDATE mijozlar SET last_active=? WHERE user_id=?", (now, user_id))
        except:
            pass
    conn.commit()
    conn.close()


def qidir_mijoz(qidiruv):
    conn = get_db()
    q = qidiruv.strip()

    # Bron ID
    b = conn.execute("SELECT * FROM bronlar WHERE id=?", (q.upper(),)).fetchone()
    if b:
        m = conn.execute("SELECT * FROM mijozlar WHERE user_id=?", (b["user_id"],)).fetchone()
        conn.close()
        return {"bron": dict(b), "mijoz": dict(m) if m else None}

    # Telefon
    for tel in [q, "+998"+q.lstrip("+0"), "998"+q.lstrip("+")]:
        m = conn.execute("SELECT * FROM mijozlar WHERE telefon=?", (tel,)).fetchone()
        if m:
            conn.close()
            return {"mijoz": dict(m), "bron": None}

    # Oxirgi 9 raqam
    if len(q) >= 9:
        all_m = conn.execute("SELECT * FROM mijozlar").fetchall()
        for m in all_m:
            if m["telefon"] and str(m["telefon"])[-9:] == q[-9:]:
                conn.close()
                return {"mijoz": dict(m), "bron": None}

    # Username
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


# ===== STATISTIKA =====

def log_stat(user_id, harakat, qoshimcha=""):
    try:
        conn = get_db()
        conn.execute("INSERT INTO statistika (user_id,harakat,qoshimcha,vaqt) VALUES (?,?,?,?)",
                     (user_id, harakat, qoshimcha, datetime.now().strftime("%d.%m.%Y %H:%M")))
        conn.commit()
        conn.close()
    except:
        pass


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


def get_mijoz_profil(user_id):
    conn = get_db()
    m = conn.execute("SELECT * FROM mijozlar WHERE user_id=?", (user_id,)).fetchone()
    if m:
        bronlar = conn.execute(
            "SELECT COUNT(*) as c FROM bronlar WHERE user_id=?", (user_id,)).fetchone()["c"]
        conn.close()
        return dict(m) | {"bronlar_soni": bronlar}
    conn.close()
    return None


def xonaga_joylashtir(xona_id, ism, telefon, kishi, bron_id=None):
    from datetime import datetime, timedelta
    boshlanish = datetime.now().strftime("%d.%m.%Y")
    tugash = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
    conn = get_db()
    conn.execute(
        "INSERT INTO joylashgan (xona_id,ism,telefon,kishi,boshlanish,tugash,bron_id) VALUES (?,?,?,?,?,?,?)",
        (xona_id, ism, telefon, kishi, boshlanish, tugash, bron_id or ""))
    # Xonani band qil bugun uchun
    conn.execute("INSERT OR IGNORE INTO band (xona_id,sana,bron_id) VALUES (?,?,?)",
                (xona_id, boshlanish, bron_id or "joylashgan"))
    conn.commit()
    conn.close()


def bugungi_joylashganlar():
    bugun = datetime.now().strftime("%d.%m.%Y")
    conn = get_db()
    rows = conn.execute(
        "SELECT j.*, x.nomi as xona_nomi FROM joylashgan j LEFT JOIN xonalar x ON j.xona_id=x.id WHERE j.boshlanish=?",
        (bugun,)).fetchall()
    conn.close()
    return rows


def kengaytirilgan_stat():
    conn = get_db()
    bugun = datetime.now().strftime("%d.%m.%Y")
    
    # Bugungi
    bugun_f = conn.execute(
        "SELECT COUNT(DISTINCT user_id) as c FROM statistika WHERE vaqt LIKE ?",
        (f"{bugun}%",)).fetchone()["c"]
    
    # Haftalik
    from datetime import timedelta
    hafta = (datetime.now() - timedelta(days=7)).strftime("%d.%m.%Y")
    hafta_f = conn.execute(
        "SELECT COUNT(DISTINCT user_id) as c FROM statistika WHERE vaqt >= ?",
        (hafta,)).fetchone()["c"]
    
    # Oylik
    oy = datetime.now().strftime("%d.%m.")
    oy_f = conn.execute(
        "SELECT COUNT(DISTINCT user_id) as c FROM statistika WHERE vaqt LIKE ?",
        (f"%{oy}%",)).fetchone()["c"]
    
    # Eng ko'p harakatlar
    harakatlar = conn.execute(
        "SELECT harakat, COUNT(*) as c FROM statistika GROUP BY harakat ORDER BY c DESC LIMIT 10"
    ).fetchall()
    
    # Soat bo'yicha taqsimot
    soatlar = conn.execute(
        "SELECT substr(vaqt, 12, 2) as soat, COUNT(*) as c FROM statistika GROUP BY soat ORDER BY soat"
    ).fetchall()
    
    # Bronlar
    jami_bronlar = conn.execute("SELECT COUNT(*) as c FROM bronlar").fetchone()["c"]
    tasdiq_bronlar = conn.execute("SELECT COUNT(*) as c FROM bronlar WHERE holat='tasdiqlangan'").fetchone()["c"]
    
    # Mijozlar
    jami_mijozlar = conn.execute("SELECT COUNT(*) as c FROM mijozlar").fetchone()["c"]
    
    conn.close()
    return {
        "bugun": bugun_f, "hafta": hafta_f, "oy": oy_f,
        "harakatlar": harakatlar, "soatlar": soatlar,
        "jami_bronlar": jami_bronlar, "tasdiq_bronlar": tasdiq_bronlar,
        "jami_mijozlar": jami_mijozlar
    }


def bugungi_stat():
    bugun = datetime.now().strftime("%d.%m.%Y")
    conn = get_db()
    foydalanuvchilar = conn.execute(
        "SELECT COUNT(DISTINCT user_id) as c FROM statistika WHERE vaqt LIKE ?",
        (f"{bugun}%",)).fetchone()["c"]
    harakatlar = conn.execute(
        "SELECT harakat, COUNT(*) as c FROM statistika WHERE vaqt LIKE ? GROUP BY harakat ORDER BY c DESC LIMIT 8",
        (f"{bugun}%",)).fetchall()
    bronlar = conn.execute(
        "SELECT COUNT(*) as c FROM bronlar WHERE created_at LIKE ?",
        (f"{bugun}%",)).fetchone()["c"]
    conn.close()
    return {"foydalanuvchilar": foydalanuvchilar, "harakatlar": harakatlar, "bronlar": bronlar}


# ===== KOMBINATSIYA =====

def barcha_variantlar(kishi, guruh, sana, kunlar=1):
    """Barcha mumkin variantlarni qaytaradi - istalgan kishi soni uchun"""
    xonalar = get_xonalar()
    bosh = []
    for x in xonalar:
        xd = dict(x)
        if not xona_kunlar_band(xd["id"], sana, kunlar) and xd.get("yopiq", 0) == 0:
            bosh.append(xd)
    if not bosh:
        return []

    afzal_qavat = 1 if guruh == "oila" else 2
    variantlar = []

    # 1. Bitta xona - to'liq mos
    for x in sorted(bosh, key=lambda a: a["sigim"]):
        if x["sigim"] >= kishi:
            variantlar.append({
                "xonalar": [x],
                "tur": "bitta",
                "jami_sigim": x["sigim"],
                "ortiqcha": x["sigim"] - kishi,
                "afzal": x["qavat"] == afzal_qavat
            })
            break  # Eng kichik mosini birinchi

    # 2. Bitta xona - 1 ta ortiqcha (siqilsa ham bo'ladi)
    for x in sorted(bosh, key=lambda a: a["sigim"]):
        if x["sigim"] == kishi - 1:
            variantlar.append({
                "xonalar": [x],
                "tur": "ortiqcha_1",
                "jami_sigim": x["sigim"],
                "ortiqcha": -1,
                "afzal": x["qavat"] == afzal_qavat
            })
            break

    # 3. Kombinatsiya - afzal qavatdan boshlash
    def topish(kishi_qolgan, mavjud, tanlangan):
        if kishi_qolgan <= 0:
            return tanlangan
        if not mavjud:
            return None
        for i, x in enumerate(mavjud):
            if x["sigim"] >= kishi_qolgan:
                return tanlangan + [x]
        # Eng kattasidan boshlash
        x = mavjud[0]
        natija = topish(kishi_qolgan - x["sigim"], mavjud[1:], tanlangan + [x])
        if natija:
            return natija
        return topish(kishi_qolgan, mavjud[1:], tanlangan)

    afzal = sorted([x for x in bosh if x["qavat"] == afzal_qavat], key=lambda a: a["sigim"], reverse=True)
    boshqa = sorted([x for x in bosh if x["qavat"] != afzal_qavat], key=lambda a: a["sigim"], reverse=True)

    # Afzal qavat kombinatsiyasi
    kom1 = topish(kishi, afzal + boshqa, [])
    if kom1 and len(kom1) > 1:
        jami = sum(x["sigim"] for x in kom1)
        variantlar.append({
            "xonalar": kom1,
            "tur": "kombinatsiya",
            "jami_sigim": jami,
            "ortiqcha": jami - kishi,
            "afzal": True
        })

    # Aralash kombinatsiya (agar yuqoridagidan farqli bo'lsa)
    kom2 = topish(kishi, boshqa + afzal, [])
    if kom2 and len(kom2) > 1:
        ids1 = set(x["id"] for x in (kom1 or []))
        ids2 = set(x["id"] for x in kom2)
        if ids1 != ids2:
            jami = sum(x["sigim"] for x in kom2)
            variantlar.append({
                "xonalar": kom2,
                "tur": "kombinatsiya_2",
                "jami_sigim": jami,
                "ortiqcha": jami - kishi,
                "afzal": False
            })

    return variantlar[:4]  # Max 4 ta variant


def mos_kombinatsiya(kishi, guruh, sana, kunlar=1):
    variantlar = barcha_variantlar(kishi, guruh, sana, kunlar)
    return variantlar[0:1] if variantlar else []
