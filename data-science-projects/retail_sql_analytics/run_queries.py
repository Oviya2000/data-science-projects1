"""Run every query in queries.sql, printing and saving each result as CSV."""
import re
import sqlite3
from pathlib import Path
import pandas as pd

HERE = Path(__file__).parent
sql = (HERE / "queries.sql").read_text()

# Split on lines that start with "-- Q<n>" — the section headers.
blocks = re.split(r"^-- (Q\d+)\s*—\s*(.+?)\s*-{2,}\s*$", sql, flags=re.M)
# blocks = [preamble, "Q1", "title", "sql", "Q2", "title", "sql", ...]
queries = []
for i in range(1, len(blocks), 3):
    qid, title, body = blocks[i], blocks[i + 1], blocks[i + 2]
    # Trim leading blank lines and trailing next-section noise.
    body = body.strip()
    # Only keep up to the terminating semicolon of the first statement.
    if ";" in body:
        body = body[: body.index(";") + 1]
    queries.append((qid.strip(), title.strip(), body))

con = sqlite3.connect(HERE / "retail.db")
out_dir = HERE / "results"
out_dir.mkdir(exist_ok=True)

for qid, title, body in queries:
    df = pd.read_sql_query(body, con)
    df.to_csv(out_dir / f"{qid.lower()}.csv", index=False)
    print(f"\n══ {qid} · {title}  ({len(df)} rows)")
    with pd.option_context("display.max_rows", 15, "display.width", 120):
        print(df.head(12).to_string(index=False))

con.close()
print(f"\nSaved {len(queries)} result sets to {out_dir}/")
