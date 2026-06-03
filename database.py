import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "/data/resort.db")

def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS binolar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomi TEXT NOT NULL,
            tavsif TEXT,
            aktiv INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS xonalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bino_id INTEGER NOT NULL,
            nomi TEXT NOT NULL,
            qavat INTEGER DEFAULT 1,
            sigim INTEGER NOT NULL,
            narx INTEGER NOT NULL,
            aktiv INTEGER DEFAULT 1,
            FOREIGN KEY (bino_id) REFERENCES binolar(id)
        );

        CREATE TABLE IF NOT EXISTS xona_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            xona_id INTEGER,
            tur TEXT,
            file_id TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS umumiy_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tur TEXT,
            file_id TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS greeting_media (
            id INTEGER PRIMARY KEY,
            file_id TEXT,
            tur TEXT
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
            created_at TEXT,
            izoh TEXT
        );

        CREATE TABLE IF NOT EXISTS bron_xonalar (
            bron_id TEXT,
            xona_id INTEGER,
            PRIMARY KEY (bron_id, xona_id)
        );

        CREATE TABLE IF NOT EXISTS mijozlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            ism TEXT,
            telefon TEXT,
            username TEXT,
            til TEXT DEFAULT 'uz',
            bloklangan INTEGER DEFAULT 0,
            created_at TEXT,
            last_active TEXT
        );

        CREATE TABLE IF NOT EXISTS adminlar (
            user_id INTEGER PRIMARY KEY,
            ism TEXT,
            lavozim TEXT DEFAULT 'admin',
            qoshilgan TEXT
        );

        CREATE TABLE IF NOT EXISTS ai_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matn TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS til (
            user_id INTEGER PRIMARY KEY,
            til TEXT
        );

        CREATE TABLE IF NOT EXISTS narx_tariflar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            xona_id INTEGER,
            nom TEXT,
            narx INTEGER,
            aktiv INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS bot_statistika (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            harakat TEXT,
            ma_lumot TEXT,
            vaqt TEXT
        );
        """)

        # 1-binoni boshlang'ich qiymat bilan to'ldirish
        bino = conn.execute("SELECT id FROM binolar WHERE id=1").fetchone()
        if not bino:
            conn.execute("INSERT INTO binolar (id, nomi, tavsif) VALUES (1, '1-bino', 'Asosiy bino')")

        # Xonalarni boshlang'ich qiymatlar bilan to'ldirish
        existing = conn.execute("SELECT COUNT(*) as c FROM xonalar").fetchone()["c"]
        if existing == 0:
            xonalar = [
                (1,1,"1-xona",1,3,300000),(1,2,"2-xona",1,3,300000),
                (1,3,"3-xona",1,7,700000),(1,4,"4-xona",1,7,700000),
                (1,5,"5-xona",2,3,300000),(1,6,"6-xona",2,3,300000),
                (1,7,"7-xona",2,3,300000),(1,8,"8-xona",2,3,300000),
                (1,9,"9-xona",2,3,300000),(1,10,"10-xona",2,3,300000),
            ]
            conn.executemany(
                "INSERT INTO xonalar (bino_id,id,nomi,qavat,sigim,narx) VALUES (?,?,?,?,?,?)",
                xonalar)
        conn.commit()

    # Migration - eski bazaga yangi ustunlar qo'shish
    try:
        conn.execute("ALTER TABLE mijozlar ADD COLUMN last_active TEXT")
        conn.commit()
    except: pass
    try:
        conn.execute("ALTER TABLE mijozlar ADD COLUMN til TEXT DEFAULT 'uz'")
        conn.commit()
    except: pass
    try:
        conn.execute("ALTER TABLE bronlar ADD COLUMN izoh TEXT")
        conn.commit()
    except: pass

# ==================== XONA FUNKSIYALAR ====================

def get_xonalar(bino_id=None, aktiv=True):
    with db() as conn:
        if bino_id:
            return conn.execute(
                "SELECT x.*, b.nomi as bino_nomi FROM xonalar x JOIN binolar b ON x.bino_id=b.id WHERE x.bino_id=? AND x.aktiv=?",
                (bino_id, 1 if aktiv else 0)).fetchall()
        return conn.execute(
            "SELECT x.*, b.nomi as bino_nomi FROM xonalar x JOIN binolar b ON x.bino_id=b.id WHERE x.aktiv=?",
            (1 if aktiv else 0,)).fetchall()

def get_binolar():
    with db() as conn:
        return conn.execute("SELECT * FROM binolar WHERE aktiv=1").fetchall()

def xona_band_mi(xid, sana):
    with db() as conn:
        r = conn.execute("SELECT id FROM band WHERE xona_id=? AND sana=?", (xid, sana)).fetchone()
        return r is not None

def xona_kunlar_band(xid, bosh_sana, kunlar):
    from datetime import timedelta
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    for i in range(kunlar):
        sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
        if xona_band_mi(xid, sana):
            return True
    return False

def band_qil(xid, bosh_sana, kunlar, bron_id):
    from datetime import timedelta
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    with db() as conn:
        for i in range(kunlar):
            sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
            conn.execute(
                "INSERT OR IGNORE INTO band (xona_id, sana, bron_id) VALUES (?,?,?)",
                (xid, sana, bron_id))
        conn.commit()

def bosh_qil_bron(bron_id):
    with db() as conn:
        conn.execute("DELETE FROM band WHERE bron_id=?", (bron_id,))
        conn.commit()

def bosh_qil_sana(xid, bosh_sana, kunlar):
    from datetime import timedelta
    bosh = datetime.strptime(bosh_sana, "%d.%m.%Y").date()
    with db() as conn:
        for i in range(kunlar):
            sana = (bosh + timedelta(days=i)).strftime("%d.%m.%Y")
            conn.execute("DELETE FROM band WHERE xona_id=? AND sana=?", (xid, sana))
        conn.commit()

# ==================== BRON FUNKSIYALAR ====================

def get_bron(bron_id):
    with db() as conn:
        return conn.execute("SELECT * FROM bronlar WHERE id=?", (bron_id,)).fetchone()

def get_bron_xonalar(bron_id):
    with db() as conn:
        rows = conn.execute("SELECT xona_id FROM bron_xonalar WHERE bron_id=?", (bron_id,)).fetchall()
        return [r["xona_id"] for r in rows]

def bekor_qil_bron(bron_id):
    with db() as conn:
        conn.execute("UPDATE bronlar SET holat='bekor' WHERE id=?", (bron_id,))
        conn.commit()
    bosh_qil_bron(bron_id)

def tugash_sanasi(bron_id):
    from datetime import timedelta
    b = get_bron(bron_id)
    if not b:
        return None
    bosh = datetime.strptime(b["sana"], "%d.%m.%Y")
    return (bosh + timedelta(days=b["kunlar"])).strftime("%d.%m.%Y")

# ==================== MIJOZ FUNKSIYALAR ====================

def get_yoki_yarat_mijoz(user_id, ism=None, username=None):
    with db() as conn:
        m = conn.execute("SELECT * FROM mijozlar WHERE user_id=?", (user_id,)).fetchone()
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        if not m:
            conn.execute(
                "INSERT INTO mijozlar (user_id,ism,username,created_at,last_active) VALUES (?,?,?,?,?)",
                (user_id, ism or "Noma'lum", username or "", now, now))
            conn.commit()
        else:
            conn.execute("UPDATE mijozlar SET last_active=? WHERE user_id=?", (now, user_id))
            conn.commit()
        return conn.execute("SELECT * FROM mijozlar WHERE user_id=?", (user_id,)).fetchone()

def qidir_mijoz(qidiruv):
    with db() as conn:
        # Bron ID bo'yicha
        b = conn.execute("SELECT * FROM bronlar WHERE id=?", (qidiruv.upper(),)).fetchone()
        if b:
            m = conn.execute("SELECT * FROM mijozlar WHERE user_id=?", (b["user_id"],)).fetchone()
            return {"bron": dict(b), "mijoz": dict(m) if m else None}

        # Telefon bo'yicha (turli formatlar)
        tel_variants = [qidiruv, "+998"+qidiruv.lstrip("+"), "998"+qidiruv.lstrip("+")]
        for tel in tel_variants:
            m = conn.execute("SELECT * FROM mijozlar WHERE telefon=?", (tel,)).fetchone()
            if m:
                return {"mijoz": dict(m), "bron": None}

        # Oxirgi 9 raqam bo'yicha
        if len(qidiruv) >= 9:
            oxiri = qidiruv[-9:]
            all_m = conn.execute("SELECT * FROM mijozlar").fetchall()
            for m in all_m:
                if m["telefon"] and str(m["telefon"])[-9:] == oxiri:
                    return {"mijoz": dict(m), "bron": None}

        # Username bo'yicha
        uname = qidiruv.lstrip("@")
        m = conn.execute("SELECT * FROM mijozlar WHERE username=?", (uname,)).fetchone()
        if m:
            return {"mijoz": dict(m), "bron": None}

        return None

# ==================== STATISTIKA ====================

def log_harakat(user_id, harakat, ma_lumot=""):
    with db() as conn:
        conn.execute(
            "INSERT INTO bot_statistika (user_id,harakat,ma_lumot,vaqt) VALUES (?,?,?,?)",
            (user_id, harakat, ma_lumot, datetime.now().strftime("%d.%m.%Y %H:%M")))
        conn.commit()

def bugungi_statistika():
    bugun = datetime.now().strftime("%d.%m.%Y")
    with db() as conn:
        jami = conn.execute(
            "SELECT COUNT(DISTINCT user_id) as c FROM bot_statistika WHERE vaqt LIKE ?",
            (f"{bugun}%",)).fetchone()["c"]
        harakatlar = conn.execute(
            "SELECT harakat, COUNT(*) as c FROM bot_statistika WHERE vaqt LIKE ? GROUP BY harakat ORDER BY c DESC LIMIT 10",
            (f"{bugun}%",)).fetchall()
        yangi_bronlar = conn.execute(
            "SELECT COUNT(*) as c FROM bronlar WHERE created_at LIKE ?",
            (f"{bugun}%",)).fetchone()["c"]
        return {"jami_foydalanuvchi": jami, "harakatlar": harakatlar, "yangi_bronlar": yangi_bronlar}

# ==================== TIL ====================

def get_til(uid):
    with db() as conn:
        r = conn.execute("SELECT til FROM til WHERE user_id=?", (uid,)).fetchone()
        return r["til"] if r else None

def set_til(uid, til):
    with db() as conn:
        conn.execute("INSERT OR REPLACE INTO til VALUES (?,?)", (uid, til))
        conn.commit()

# ==================== ADMIN ====================

def is_director(uid):
    return uid in [8886176055, 7323184602]

def is_admin(uid):
    if is_director(uid):
        return True
    with db() as conn:
        r = conn.execute("SELECT user_id FROM adminlar WHERE user_id=?", (uid,)).fetchone()
        return r is not None

def format_narx(n):
    return f"{n:,}".replace(",", " ")
