"""EDA for HR attrition — produces the aggregates the Power BI dashboard consumes."""
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).parent
df = pd.read_csv(HERE / "hr_attrition.csv")

# --- Data quality ---
qa = {
    "rows": int(len(df)), "cols": int(df.shape[1]),
    "missing_values": int(df.isna().sum().sum()),
    "duplicates": int(df.duplicated().sum()),
    "attrition_rate": round(float((df["Attrition"] == "Yes").mean()), 4),
    "avg_monthly_income": int(df["MonthlyIncome"].mean()),
    "avg_age": round(float(df["Age"].mean()), 1),
    "avg_years_at_company": round(float(df["YearsAtCompany"].mean()), 1),
}
print(json.dumps(qa, indent=2))

# --- Aggregates powering the dashboard visuals ---
out = HERE / "dashboard_data"
out.mkdir(exist_ok=True)

def rate(g):
    return pd.Series({
        "headcount": len(g),
        "leavers":   int((g["Attrition"] == "Yes").sum()),
        "attrition_rate": round(float((g["Attrition"] == "Yes").mean()), 4),
        "avg_income": int(g["MonthlyIncome"].mean()),
    })

df.groupby("Department").apply(rate, include_groups=False)\
   .reset_index().to_csv(out / "by_department.csv", index=False)

df.groupby("JobRole").apply(rate, include_groups=False)\
   .reset_index().sort_values("attrition_rate", ascending=False)\
   .to_csv(out / "by_job_role.csv", index=False)

df.groupby("OverTime").apply(rate, include_groups=False)\
   .reset_index().to_csv(out / "by_overtime.csv", index=False)

df.groupby("BusinessTravel").apply(rate, include_groups=False)\
   .reset_index().to_csv(out / "by_travel.csv", index=False)

df.groupby("MaritalStatus").apply(rate, include_groups=False)\
   .reset_index().to_csv(out / "by_marital.csv", index=False)

df.groupby("Gender").apply(rate, include_groups=False)\
   .reset_index().to_csv(out / "by_gender.csv", index=False)

# Age bands + tenure bands (drives the "who's leaving" story)
df["AgeBand"] = pd.cut(df["Age"], bins=[19, 29, 39, 49, 60],
                      labels=["20-29", "30-39", "40-49", "50+"])
df.groupby("AgeBand", observed=True).apply(rate, include_groups=False)\
   .reset_index().to_csv(out / "by_age_band.csv", index=False)

df["TenureBand"] = pd.cut(df["YearsAtCompany"], bins=[-1, 2, 5, 10, 25],
                          labels=["0-2", "3-5", "6-10", "10+"])
df.groupby("TenureBand", observed=True).apply(rate, include_groups=False)\
   .reset_index().to_csv(out / "by_tenure_band.csv", index=False)

df["IncomeBand"] = pd.cut(
    df["MonthlyIncome"], bins=[0, 3000, 5000, 8000, 12000, 25000],
    labels=["<3k", "3-5k", "5-8k", "8-12k", "12k+"])
df.groupby("IncomeBand", observed=True).apply(rate, include_groups=False)\
   .reset_index().to_csv(out / "by_income_band.csv", index=False)

# Job satisfaction × attrition heat data
sat = df.groupby(["JobSatisfaction", "WorkLifeBalance"])\
        .apply(lambda g: round(float((g["Attrition"] == "Yes").mean()), 4),
               include_groups=False)\
        .reset_index().rename(columns={0: "attrition_rate"})
sat.to_csv(out / "satisfaction_matrix.csv", index=False)

# Save data quality summary
(HERE / "data_quality.json").write_text(json.dumps(qa, indent=2))
print(f"\nWrote {len(list(out.glob('*.csv')))} aggregate CSVs to {out}/")
