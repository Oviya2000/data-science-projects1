"""Build a SQLite e-commerce database for the SQL analytics project.

Generates ~5,000 customers, ~500 products across 10 categories, and
~40,000 order-lines across 24 months so window-function queries and
cohort analyses have realistic distributions.
"""
import sqlite3
from datetime import date, timedelta
from pathlib import Path
import numpy as np

DB = Path(__file__).parent / "retail.db"
if DB.exists():
    DB.unlink()

con = sqlite3.connect(DB)
cur = con.cursor()
rng = np.random.default_rng(7)

cur.executescript(
    """
    CREATE TABLE customers (
        customer_id  INTEGER PRIMARY KEY,
        name         TEXT NOT NULL,
        country      TEXT NOT NULL,
        signup_date  DATE NOT NULL
    );
    CREATE TABLE categories (
        category_id  INTEGER PRIMARY KEY,
        name         TEXT NOT NULL
    );
    CREATE TABLE products (
        product_id   INTEGER PRIMARY KEY,
        name         TEXT NOT NULL,
        category_id  INTEGER NOT NULL REFERENCES categories(category_id),
        unit_price   REAL NOT NULL,
        cost         REAL NOT NULL
    );
    CREATE TABLE orders (
        order_id     INTEGER PRIMARY KEY,
        customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
        order_date   DATE NOT NULL
    );
    CREATE TABLE order_items (
        order_id     INTEGER NOT NULL REFERENCES orders(order_id),
        product_id   INTEGER NOT NULL REFERENCES products(product_id),
        quantity     INTEGER NOT NULL,
        unit_price   REAL NOT NULL,
        PRIMARY KEY (order_id, product_id)
    );
    CREATE INDEX idx_orders_customer ON orders(customer_id);
    CREATE INDEX idx_orders_date     ON orders(order_date);
    CREATE INDEX idx_items_product   ON order_items(product_id);
    """
)

# --- Reference data ---
cats = ["Apparel", "Electronics", "Home & Kitchen", "Beauty", "Books",
        "Sports", "Toys", "Grocery", "Office", "Garden"]
cur.executemany("INSERT INTO categories(category_id,name) VALUES (?,?)",
                list(enumerate(cats, 1)))

# --- Products ---
products = []
for pid in range(1, 501):
    cat = int(rng.integers(1, 11))
    base = float(rng.gamma(2.5, 8.0)) + 5
    price = round(base, 2)
    cost = round(price * float(rng.uniform(0.45, 0.70)), 2)
    products.append((pid, f"SKU-{pid:04d}", cat, price, cost))
cur.executemany(
    "INSERT INTO products(product_id,name,category_id,unit_price,cost) VALUES (?,?,?,?,?)",
    products,
)

# --- Customers (staggered signups across 24 months) ---
today = date(2026, 9, 1)
start = today - timedelta(days=730)
customers = []
sign_dates = []
for cid in range(1, 5001):
    signup = start + timedelta(days=int(rng.integers(0, 730)))
    country = rng.choice(
        ["US", "UK", "DE", "IN", "CA", "AU", "FR", "BR"],
        p=[0.40, 0.13, 0.10, 0.12, 0.07, 0.06, 0.07, 0.05],
    )
    customers.append((cid, f"Customer {cid}", str(country), signup.isoformat()))
    sign_dates.append(signup)
cur.executemany(
    "INSERT INTO customers(customer_id,name,country,signup_date) VALUES (?,?,?,?)",
    customers,
)

# --- Orders + line items ---
orders = []
items = []
oid = 0
for cid, signup in zip(range(1, 5001), sign_dates):
    # Repeat-purchase rate follows a Poisson tail; ~30% of customers make 0 orders after signup.
    n_orders = int(rng.poisson(2.3))
    for _ in range(n_orders):
        day_offset = int(rng.integers(0, max(1, (today - signup).days)))
        odate = signup + timedelta(days=day_offset)
        if odate > today:
            continue
        oid += 1
        orders.append((oid, cid, odate.isoformat()))
        n_lines = int(rng.integers(1, 5))
        chosen = rng.choice(500, size=n_lines, replace=False) + 1
        for pid in chosen:
            unit_price = products[pid - 1][3]
            qty = int(rng.integers(1, 4))
            items.append((oid, int(pid), qty, unit_price))

cur.executemany(
    "INSERT INTO orders(order_id,customer_id,order_date) VALUES (?,?,?)", orders,
)
cur.executemany(
    "INSERT INTO order_items(order_id,product_id,quantity,unit_price) VALUES (?,?,?,?)",
    items,
)

con.commit()
print(
    f"customers={len(customers):,}  products={len(products):,}  "
    f"orders={len(orders):,}  order_items={len(items):,}"
)
con.close()
