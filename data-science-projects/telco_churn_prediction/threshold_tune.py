"""Tune the classification threshold for the best-F1 operating point.

Also reports the threshold that hits recall >= 0.70 (a retention-team use
case where catching churners matters more than false positives).
"""
from pathlib import Path
import json
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (f1_score, precision_recall_curve,
                             precision_score, recall_score)
from sklearn.model_selection import train_test_split

HERE = Path(__file__).parent
df = pd.read_csv(HERE / "telco_churn.csv")
y = (df["Churn"] == "Yes").astype(int)
X = df.drop(columns=["customerID", "Churn"])
_, X_te, _, y_te = train_test_split(X, y, test_size=0.20, stratify=y, random_state=42)

model = joblib.load(HERE / "best_model.joblib")
proba = model.predict_proba(X_te)[:, 1]

thr_grid = np.linspace(0.05, 0.95, 91)
rows = []
for t in thr_grid:
    p = (proba >= t).astype(int)
    rows.append({"threshold": round(t, 2),
                 "precision": round(precision_score(y_te, p, zero_division=0), 4),
                 "recall": round(recall_score(y_te, p), 4),
                 "f1": round(f1_score(y_te, p), 4)})
grid = pd.DataFrame(rows)
grid.to_csv(HERE / "threshold_grid.csv", index=False)

best_f1 = grid.loc[grid["f1"].idxmax()]
recall_target = grid[grid["recall"] >= 0.70].sort_values("precision", ascending=False)
recall_row = recall_target.iloc[0] if len(recall_target) else None

fig, ax = plt.subplots(figsize=(6.5, 4.5))
ax.plot(grid["threshold"], grid["precision"], label="Precision", color="#4c72b0")
ax.plot(grid["threshold"], grid["recall"], label="Recall", color="#dd8452")
ax.plot(grid["threshold"], grid["f1"], label="F1", color="#55a868")
ax.axvline(best_f1["threshold"], ls="--", color="gray",
           label=f"best F1 @ {best_f1['threshold']:.2f}")
ax.set_xlabel("Decision threshold"); ax.set_ylabel("Score")
ax.set_title("Precision / Recall / F1 vs. threshold")
ax.legend(); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(HERE / "threshold_curve.png", dpi=140); plt.close(fig)

out = {
    "best_f1_operating_point": best_f1.to_dict(),
    "recall_ge_0_70": recall_row.to_dict() if recall_row is not None else None,
}
(HERE / "threshold_summary.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
