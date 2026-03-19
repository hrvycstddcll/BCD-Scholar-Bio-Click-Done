import sqlite3, hashlib, os
from PyQt5.QtGui  import QPixmap
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice

_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_DIR, "sales_inventory.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# ── Image helpers ─────────────────────────────────────────────

def image_path_to_blob(path: str):
    """Read an image file → PNG bytes ready for SQLite BLOB storage.
    Returns None if path is empty or the file cannot be read."""
    if not path or not os.path.exists(path):
        return None
    px = QPixmap(path)
    if px.isNull():
        return None
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    px.save(buf, "PNG")
    return bytes(buf.data())


def blob_to_pixmap(blob):
    """Convert raw PNG bytes from the DB back to a QPixmap.
    Returns None if blob is empty/None/invalid."""
    if not blob:
        return None
    px = QPixmap()
    px.loadFromData(blob, "PNG")
    return px if not px.isNull() else None


# ── Schema / init ─────────────────────────────────────────────

def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT NOT NULL UNIQUE,
                password   TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS products (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                category   TEXT NOT NULL,
                price      REAL NOT NULL CHECK(price >= 0),
                stock      INTEGER NOT NULL CHECK(stock >= 0),
                image_data BLOB DEFAULT NULL,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS sales (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity   INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL,
                total      REAL NOT NULL,
                sold_at    TEXT DEFAULT (datetime('now','localtime'))
            );
        """)

        cols = [r[1] for r in conn.execute("PRAGMA table_info(products)").fetchall()]

        # ── Migration A: old schema had image_path TEXT ───────────
        if "image_data" not in cols and "image_path" in cols:
            conn.execute("ALTER TABLE products ADD COLUMN image_data BLOB DEFAULT NULL")
            # Migrate existing file-path images into blobs
            for row in conn.execute("SELECT id, image_path FROM products").fetchall():
                pid, path = row["id"], row["image_path"]
                if path and os.path.exists(path):
                    blob = image_path_to_blob(path)
                    if blob:
                        conn.execute("UPDATE products SET image_data=? WHERE id=?",
                                     (blob, pid))
            # Rebuild table without the old column (SQLite < 3.35 cannot DROP COLUMN)
            conn.executescript("""
                CREATE TABLE products_new (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    name       TEXT NOT NULL,
                    category   TEXT NOT NULL,
                    price      REAL NOT NULL CHECK(price >= 0),
                    stock      INTEGER NOT NULL CHECK(stock >= 0),
                    image_data BLOB DEFAULT NULL,
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                );
                INSERT INTO products_new
                    SELECT id, name, category, price, stock, image_data, created_at
                    FROM products;
                DROP TABLE products;
                ALTER TABLE products_new RENAME TO products;
            """)

        # ── Migration B: schema exists but image_data column missing
        elif "image_data" not in cols:
            conn.execute("ALTER TABLE products ADD COLUMN image_data BLOB DEFAULT NULL")

        # ── Default admin user ────────────────────────────────────
        if not conn.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
            conn.execute("INSERT INTO users (username, password) VALUES (?,?)",
                         ("admin", _hash("admin123")))


def verify_login(username: str, password: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, _hash(password))
        ).fetchone()
