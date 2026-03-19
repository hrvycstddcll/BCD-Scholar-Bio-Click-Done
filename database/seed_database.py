"""
seed_database.py  —  SalesTrack Demo Seeder
════════════════════════════════════════════
20 carefully chosen products across 5 categories.

Sales data is deliberately wave-shaped so every sparkline and the
donut chart show dramatic high→low→high variance:

  • Days 1-30  : BOOM  — high volume (holiday / launch rush)
  • Days 31-60 : CRASH — low volume  (post-season slump)
  • Days 61-90 : SURGE — medium-high (mid-year campaign)
  • Days 91-120: DIP   — low again   (quiet period)
  • Days 121-150: PEAK  — highest    (major promo event)
  • Days 151-180: DECAY — gradual decline to present

Total sales: ~2 400 transactions so every product has a rich history.

Safe to re-run — wipes products & sales, keeps users.

Usage:
    cd "Inventory System"
    python database/seed_database.py
"""

import sqlite3, hashlib, os, random, math
from datetime import datetime, timedelta

_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_DIR, "sales_inventory.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# ══════════════════════════════════════════════════════════════
#  20 PRODUCTS  — 5 categories, wide price spread, varied stock
# ══════════════════════════════════════════════════════════════
#  (name, category, price, current_stock)
PRODUCTS = [
    # ── Electronics (4) ──────────────────────────────────────
    ("Mechanical Keyboard RGB",       "Electronics",    3_799.00,  22),
    ("Wireless Noise-Cancel Earbuds", "Electronics",    2_499.00,  35),
    ("Portable Power Bank 20000mAh",  "Electronics",    1_899.00,  48),
    ("USB-C Hub 7-in-1",              "Electronics",      899.00,  60),

    # ── Clothing (4) ─────────────────────────────────────────
    ("Premium Hoodie Oversized",      "Clothing",       1_299.00,  55),
    ("Slim Fit Chinos Khaki",         "Clothing",         999.00,  70),
    ("Running Shoes Lightweight",     "Clothing",       2_199.00,  30),
    ("Compression Leggings Pro",      "Clothing",         799.00,  80),

    # ── Food & Beverage (4) ───────────────────────────────────
    ("Single-Origin Coffee Beans 500g","Food & Beverage",  699.00, 120),
    ("Matcha Powder Premium 100g",    "Food & Beverage",   549.00,  90),
    ("Whey Protein Vanilla 1kg",      "Food & Beverage", 1_499.00,  42),
    ("Mixed Nuts Roasted 500g",       "Food & Beverage",   449.00, 150),

    # ── Sports & Fitness (4) ─────────────────────────────────
    ("Adjustable Dumbbell Set 20kg",  "Sports & Fitness",3_299.00,  15),
    ("Yoga Mat Premium 6mm",          "Sports & Fitness",  899.00,  40),
    ("Resistance Band Set Pro",       "Sports & Fitness",  649.00,  65),
    ("Jump Rope Speed Pro",           "Sports & Fitness",  399.00,  85),

    # ── Home & Garden (4) ────────────────────────────────────
    ("Bamboo Desk Organizer Set",     "Home & Garden",     599.00,  50),
    ("Ceramic Pour-Over Coffee Set",  "Home & Garden",   1_199.00,  28),
    ("Scented Soy Candle Set 3pc",    "Home & Garden",     549.00,  75),
    ("Smart LED Strip 5m RGB",        "Home & Garden",     799.00,  38),
]


# ══════════════════════════════════════════════════════════════
#  WAVE ENGINE — sinusoidal sales volume across 180 days
#  Each product has its own phase so peaks differ per product,
#  making each sparkline visually unique.
# ══════════════════════════════════════════════════════════════

def wave_weight(day_ago: int, phase_offset: float, amplitude: float = 1.0) -> float:
    """
    Returns a multiplier (0.05 – 3.0) for how many sales happen on a given day.
    day_ago = 0 means today, 180 = six months ago.

    The shape is a compound wave:
      - Primary: slow 180-day sine (one full boom/bust cycle)
      - Secondary: fast 30-day sine (monthly mini-cycles)
    Combined they produce the high-low-high-low pattern requested.
    """
    t = (180 - day_ago) / 180.0          # 0 = oldest, 1 = today
    primary   = math.sin(math.pi * t * 2 + phase_offset)         # 2 full cycles
    secondary = math.sin(math.pi * t * 12 + phase_offset * 3)    # monthly ripple
    raw = 0.55 + 0.38 * primary + 0.12 * secondary
    return max(0.04, raw * amplitude)


def make_timestamp(days_ago: int) -> str:
    """Random working-hours timestamp on a given day."""
    dt = datetime.now() - timedelta(
        days=days_ago,
        hours=random.randint(8, 21),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ══════════════════════════════════════════════════════════════
#  SEEDER
# ══════════════════════════════════════════════════════════════

def seed():
    conn = get_conn()

    # ── Ensure schema ─────────────────────────────────────
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
            image_path TEXT DEFAULT '',
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

    # Migrate: add image_path if missing
    cols = [r[1] for r in conn.execute("PRAGMA table_info(products)").fetchall()]
    if "image_path" not in cols:
        conn.execute("ALTER TABLE products ADD COLUMN image_path TEXT DEFAULT ''")

    # ── Admin user ────────────────────────────────────────
    if not conn.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
        conn.execute("INSERT INTO users (username, password) VALUES (?,?)",
                     ("admin", _hash("admin123")))

    # ── Wipe products & sales (keep users) ───────────────
    conn.execute("DELETE FROM sales")
    conn.execute("DELETE FROM products")
    conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('products','sales')")
    conn.commit()

    # ── Insert products ───────────────────────────────────
    pids    = []
    prices  = []
    phases  = []   # per-product wave phase so each sparkline is unique

    random.seed(42)   # reproducible
    for i, (name, cat, price, stock) in enumerate(PRODUCTS):
        # Stagger creation dates: oldest products ~8 months ago
        created = make_timestamp(random.randint(180, 240))
        cur = conn.execute(
            "INSERT INTO products (name, category, price, stock, image_path, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (name, cat, price, stock, "", created)
        )
        pids.append(cur.lastrowid)
        prices.append(price)
        # Unique wave phase per product (evenly distributed + jitter)
        phases.append((i / len(PRODUCTS)) * 2 * math.pi + random.uniform(-0.3, 0.3))

    conn.commit()
    print(f"  ✔  Inserted {len(pids)} products")

    # ── Category weights (drives donut proportions) ──────
    # Electronics & Sports earn more per sale, Food & Home sell in bulk
    cat_amp = {
        "Electronics":     1.6,   # high revenue impact
        "Sports & Fitness":1.3,
        "Clothing":        1.2,
        "Food & Beverage": 1.5,   # very high unit volume
        "Home & Garden":   1.0,
    }

    # ── Generate ~2400 sales across 180 days ─────────────
    # Target: ~13 sales per product per day average,
    # but heavily modulated by the wave function.
    TARGET_TOTAL = 2_400

    # Build a pool: for every day (0–179) for every product,
    # decide how many transactions happen based on wave weight.
    sales_rows = []
    random.seed(99)

    base_daily = TARGET_TOTAL / (len(pids) * 180)  # ~0.67 tx / product / day

    for pid_idx, (pid, price) in enumerate(zip(pids, prices)):
        cat = PRODUCTS[pid_idx][1]
        amp = cat_amp.get(cat, 1.0)

        for day in range(180):          # day=0 is today, day=179 is 6 months ago
            wt  = wave_weight(day, phases[pid_idx], amplitude=amp)
            # Expected transactions this day for this product
            expected = base_daily * wt * random.uniform(0.7, 1.4)
            # Round probabilistically so totals stay realistic
            n_tx = int(expected) + (1 if random.random() < (expected % 1) else 0)

            for _ in range(n_tx):
                # Quantity per transaction: 1–8, skewed low
                qty = random.choices(
                    [1, 2, 3, 4, 5, 6, 8, 10],
                    weights=[38, 26, 16, 9, 5, 3, 2, 1], k=1)[0]
                total    = round(price * qty, 2)
                sold_at  = make_timestamp(day)
                sales_rows.append((pid, qty, price, total, sold_at))

    # Sort chronologically (oldest first)
    sales_rows.sort(key=lambda r: r[4])

    conn.executemany(
        "INSERT INTO sales (product_id, quantity, unit_price, total, sold_at) "
        "VALUES (?,?,?,?,?)",
        sales_rows
    )
    conn.commit()

    # ── Summary ───────────────────────────────────────────
    total_rev  = sum(r[3] for r in sales_rows)
    total_qty  = sum(r[1] for r in sales_rows)
    low_stock  = conn.execute("SELECT COUNT(*) FROM products WHERE stock <= 5").fetchone()[0]
    out_stock  = conn.execute("SELECT COUNT(*) FROM products WHERE stock = 0").fetchone()[0]

    # Per-category revenue breakdown
    cat_rev = conn.execute("""
        SELECT p.category, SUM(s.total), COUNT(s.id)
        FROM sales s JOIN products p ON p.id = s.product_id
        GROUP BY p.category ORDER BY SUM(s.total) DESC
    """).fetchall()

    print(f"  ✔  Inserted {len(sales_rows):,} sales transactions")
    print(f"  ✔  Total units sold  : {total_qty:,}")
    print(f"  ✔  Total revenue     : ₱{total_rev:,.2f}")
    print()
    print("  Revenue by category:")
    for row in cat_rev:
        print(f"    {row[0]:<26} ₱{row[1]:>12,.2f}  ({row[2]:>4} tx)")
    print()
    print(f"  📦  Products         : {len(pids)}")
    print(f"  ⚠   Low stock (≤5)  : {low_stock}")
    print(f"  🚫  Out of stock     : {out_stock}")
    print(f"  💰  Sales records    : {len(sales_rows):,}")
    print(f"  📈  Total revenue    : ₱{total_rev:,.2f}")
    print()
    print(f"  Wave pattern per product:")
    print(f"    Days 150-180  → PEAK   (promo event)")
    print(f"    Days 120-150  → DIP    (quiet period)")
    print(f"    Days  90-120  → SURGE  (mid-year campaign)")
    print(f"    Days  60- 90  → CRASH  (post-season slump)")
    print(f"    Days  30- 60  → BOOM   (launch rush)")
    print(f"    Days   0- 30  → DECAY  (gradual decline)")
    print()
    print(f"  Database : {DB_PATH}")
    print("  Done! Run:  python app_manager.py")

    conn.close()


if __name__ == "__main__":
    print()
    print("  SalesTrack — Database Seeder")
    print("  " + "─" * 44)
    seed()
