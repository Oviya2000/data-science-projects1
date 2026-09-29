# Retail Analytics · SQL Query Book

Ten analytical SQL queries for an e-commerce business — CTEs, window
functions, cohort analysis, and RFM segmentation — run against a
purpose-built SQLite database of ~45,000 rows across five tables.

## Schema

```
customers (5,000)      products (500)          categories (10)
   customer_id ─┐         product_id ─┐            category_id
   name         │         name        │            name
   country      │         category_id ─────────────┘
   signup_date  │         unit_price
                │         cost
                │
   orders (11,430)          order_items (28,478)
      order_id ─┼─────────────── order_id
      customer_id                 product_id ────► products
      order_date                  quantity
                                  unit_price
```

Data span: 24 months (2024-09 through 2026-09). Signup dates and
purchase timing are staggered so cohort and retention queries produce
non-trivial curves.

## Queries

| # | Business question | SQL technique |
|---|---|---|
| Q1  | Monthly revenue and MoM growth | `LAG()` window |
| Q2  | Top-10 products with rank and share | `RANK()` + `SUM() OVER ()` |
| Q3  | Category revenue with running total | `SUM() OVER (ROWS ...)` |
| Q4  | Customer LTV decile breakdown | `NTILE(10)` |
| Q5  | RFM customer segmentation | 3 × `NTILE(5)` + CASE |
| Q6  | Cohort retention by signup month | Self-join + month math |
| Q7  | Repeat-purchase rate by country | Conditional aggregation |
| Q8  | Top-2 SKU per category | `ROW_NUMBER() PARTITION BY` |
| Q9  | Average basket value & margin/month | Multi-table join, margin math |
| Q10 | Days between purchases per customer | `LAG()` inside partitions |

## Sample outputs

**Q5 — RFM segmentation** (from `results/q5.csv`)

| segment | customers | avg_monetary | avg_frequency | avg_recency_days |
|---|---|---|---|---|
| Champions       | 798  | 546.91 | 4.09 | 18.3 |
| At Risk         | 476  | 467.21 | 3.64 | 190.3 |
| Can't Lose Them | 114  | 402.66 | 1.89 | 247.5 |
| Needs Attention | 1,184 | 304.23 | 2.57 | 110.9 |
| Loyal           | 480  | 286.85 | 2.54 | 21.0 |
| New / Recent    | 532  | 132.56 | 1.42 | 22.1 |
| Hibernating     | 940  | 126.76 | 1.28 | 275.6 |

**Q1 — Monthly revenue** (first 6 months from `results/q1.csv`)

| month | revenue | orders | active_customers | MoM growth |
|---|---|---|---|---|
| 2024-09 | 1,275   | 12  | 12  | – |
| 2024-10 | 4,868   | 33  | 31  | +281.7 % |
| 2024-11 | 5,965   | 50  | 48  |  +22.5 % |
| 2024-12 | 6,880   | 64  | 60  |  +15.4 % |
| 2025-01 | 14,772  | 113 | 103 | +114.7 % |
| 2025-02 | 14,574  | 112 | 107 |   −1.3 % |

## Repo layout

```
sql_retail/
├── build_db.py             # generates retail.db (~45k rows)
├── queries.sql             # the 10 analytical queries
├── run_queries.py          # runs each query and writes results/*.csv
├── retail.db               # SQLite database (created by build_db.py)
└── results/                # one CSV per query
    ├── q1.csv … q10.csv
```

## Reproducing

```bash
python3 build_db.py     # creates retail.db
python3 run_queries.py  # writes results/q1..q10.csv
```

Queries are ANSI SQL and run unchanged on PostgreSQL apart from the
SQLite-specific `strftime` / `julianday` date functions (swap for
`TO_CHAR` / date subtraction in Postgres).

## Tech

SQLite 3 · Python 3.12 · pandas (results only)
