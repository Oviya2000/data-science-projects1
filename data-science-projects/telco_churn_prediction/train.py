"""Telco Customer Churn — training pipeline.

Compares Logistic Regression, Random Forest, and Gradient Boosting on the
same preprocessing stack (one-hot + scale). Reports accuracy, precision,
recall, F1, ROC-AUC on a stratified hold-out. Saves the best model, the
top-20 feature importances, and a confusion matrix.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score,
                             roc_curve)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HERE = Path(__file__).parent
df = pd.read_csv(HERE / "telco_churn.csv")

y = (df["Churn"] == "Yes").astype(int)
X = df.drop(columns=["customerID", "Churn"])

num_cols = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]
cat_cols = [c for c in X.columns if c not in num_cols]

pre = ColumnTransformer([
    ("num", StandardScaler(), num_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
])

models = {
    "LogisticRegression": LogisticRegression(max_iter=1000, C=0.5, random_state=42),
    "RandomForest": RandomForestClassifier(n_estimators=300, max_depth=12,
                                           min_samples_leaf=5, random_state=42, n_jobs=-1),
    "GradientBoosting": GradientBoostingClassifier(n_estimators=250, max_depth=3,
                                                   learning_rate=0.08, random_state=42),
}

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.20,
                                          stratify=y, random_state=42)

results = []
fitted = {}
for name, clf in models.items():
    pipe = Pipeline([("pre", pre), ("clf", clf)])
    pipe.fit(X_tr, y_tr)
    proba = pipe.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    results.append({
        "model": name,
        "accuracy": round(accuracy_score(y_te, pred), 4),
        "precision": round(precision_score(y_te, pred), 4),
        "recall": round(recall_score(y_te, pred), 4),
        "f1": round(f1_score(y_te, pred), 4),
        "roc_auc": round(roc_auc_score(y_te, proba), 4),
    })
    fitted[name] = pipe

res_df = pd.DataFrame(results).sort_values("roc_auc", ascending=False)
res_df.to_csv(HERE / "metrics.csv", index=False)
print(res_df.to_string(index=False))

best_name = res_df.iloc[0]["model"]
best = fitted[best_name]
joblib.dump(best, HERE / "best_model.joblib")

# Feature importance for the tree-based winner
if best_name in ("RandomForest", "GradientBoosting"):
    clf = best.named_steps["clf"]
    ohe = best.named_steps["pre"].named_transformers_["cat"]
    feat_names = num_cols + list(ohe.get_feature_names_out(cat_cols))
    imp = pd.DataFrame({"feature": feat_names,
                        "importance": clf.feature_importances_})
    imp = imp.sort_values("importance", ascending=False).head(20)
    imp.to_csv(HERE / "feature_importance.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(imp["feature"][::-1], imp["importance"][::-1], color="#4c72b0")
    ax.set_xlabel("Importance")
    ax.set_title(f"Top-20 features · {best_name}")
    fig.tight_layout()
    fig.savefig(HERE / "feature_importance.png", dpi=140)
    plt.close(fig)

# Confusion matrix + ROC for the winner
proba = best.predict_proba(X_te)[:, 1]
pred = (proba >= 0.5).astype(int)
cm = confusion_matrix(y_te, pred)
fig, ax = plt.subplots(figsize=(4.5, 4))
im = ax.imshow(cm, cmap="Blues")
ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
ax.set_xticklabels(["No churn", "Churn"]); ax.set_yticklabels(["No churn", "Churn"])
for i in range(2):
    for j in range(2):
        ax.text(j, i, cm[i, j], ha="center", va="center",
                color="white" if cm[i, j] > cm.max()/2 else "black")
ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
ax.set_title(f"Confusion matrix · {best_name}")
fig.tight_layout(); fig.savefig(HERE / "confusion_matrix.png", dpi=140); plt.close(fig)

fpr, tpr, _ = roc_curve(y_te, proba)
fig, ax = plt.subplots(figsize=(5, 4.5))
ax.plot(fpr, tpr, label=f"AUC={roc_auc_score(y_te, proba):.3f}", color="#4c72b0")
ax.plot([0, 1], [0, 1], "--", color="gray")
ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
ax.set_title(f"ROC · {best_name}"); ax.legend()
fig.tight_layout(); fig.savefig(HERE / "roc_curve.png", dpi=140); plt.close(fig)

summary = {
    "n_rows": int(len(df)),
    "churn_rate": round(float(y.mean()), 4),
    "test_size": int(len(X_te)),
    "best_model": best_name,
    "best_metrics": res_df[res_df["model"] == best_name].iloc[0].to_dict(),
}
(HERE / "summary.json").write_text(json.dumps(summary, indent=2))
print("\nSaved:", best_name, "->", HERE)
