# Telco Customer Churn Prediction

End-to-end binary classification pipeline that predicts churn for a
telecom operator from 19 customer/service attributes and identifies the
strongest churn drivers to guide retention outreach.

## Business framing

A retention team can only afford to contact a limited number of
customers per month. The model outputs a churn probability that the
team can rank; the notebook shows two operating points:

| Operating point | Threshold | Precision | Recall | Use |
|---|---|---|---|---|
| Best-F1 balance | 0.30 | 0.49 | 0.62 | Default retention list |
| Recall-first | 0.23 | 0.41 | 0.71 | Catch as many churners as possible |

## Data

- 7,043 customer rows, 19 features, binary `Churn` target.
- Schema and driver structure mirror the IBM Telco Churn benchmark;
  values are synthesised with a documented probabilistic model
  (`generate_data.py`) so the project is fully reproducible.
- Churn base rate: 19.0%.

## Pipeline

```
raw CSV
  └─ ColumnTransformer (StandardScaler on numerics, OneHotEncoder on categoricals)
       └─ 3 candidate models fit on the same folds
            └─ hold-out evaluation (stratified 80/20)
                 └─ best model persisted, threshold tuned for operating points
```

## Models compared

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| **Logistic Regression** (selected) | 0.822 | 0.581 | 0.228 | 0.327 | **0.812** |
| Gradient Boosting | 0.810 | 0.500 | 0.216 | 0.302 | 0.803 |
| Random Forest | 0.816 | 0.553 | 0.157 | 0.244 | 0.797 |

The three ROC-AUCs are within 0.02 of one another; Logistic Regression
wins on both AUC and interpretability, so it is the shipped model. The
low recall at the default 0.5 threshold reflects class imbalance, which
is why the threshold-tuning step is part of the pipeline rather than
an afterthought.

## Repo layout

```
ml_churn/
├── generate_data.py         # reproducible synthetic dataset
├── train.py                 # preprocessing + 3-model bake-off
├── threshold_tune.py        # operating-point selection
├── telco_churn.csv          # 7,043 rows
├── best_model.joblib        # persisted sklearn Pipeline
├── metrics.csv              # per-model hold-out metrics
├── threshold_grid.csv       # 91 thresholds × 3 scores
├── threshold_summary.json   # chosen operating points
├── summary.json             # run summary
├── confusion_matrix.png
├── roc_curve.png
└── threshold_curve.png
```

## Reproducing

```bash
python3 generate_data.py     # writes telco_churn.csv
python3 train.py             # trains, saves best_model.joblib and plots
python3 threshold_tune.py    # writes threshold grid + summary
```

Deterministic: `numpy` and every model uses `random_state=42`.

## Key drivers (largest logistic-regression coefficients, standardised inputs)

Raise churn risk: **month-to-month contract** (+1.32), senior citizen (+0.22),
fiber-optic internet (+0.20), no online security (+0.18), higher monthly charges (+0.18).

Lower churn risk: **two-year contract** (-1.05), **longer tenure** (-0.68),
one-year contract (-0.27).

The data is synthetic and these drivers come from the rules used to generate it,
so they show the pipeline recovers the built-in structure, not real customer behaviour.

## Tech

Python 3.12 · scikit-learn 1.8 · pandas 3.0 · NumPy · matplotlib · joblib
