"""Generate a realistic Telco Customer Churn dataset for the churn-prediction project."""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 7043  # size mirrors the well-known IBM Telco Churn benchmark

gender = rng.choice(["Male", "Female"], N, p=[0.505, 0.495])
senior = rng.choice([0, 1], N, p=[0.84, 0.16])
partner = rng.choice(["Yes", "No"], N, p=[0.48, 0.52])
dependents = rng.choice(["Yes", "No"], N, p=[0.30, 0.70])
tenure = rng.integers(0, 73, N)
phone = rng.choice(["Yes", "No"], N, p=[0.90, 0.10])
multi_lines = np.where(phone == "No", "No phone service",
                       rng.choice(["Yes", "No"], N, p=[0.47, 0.53]))
internet = rng.choice(["DSL", "Fiber optic", "No"], N, p=[0.34, 0.44, 0.22])
online_sec = np.where(internet == "No", "No internet service",
                      rng.choice(["Yes", "No"], N, p=[0.36, 0.64]))
online_bak = np.where(internet == "No", "No internet service",
                      rng.choice(["Yes", "No"], N, p=[0.44, 0.56]))
device_prot = np.where(internet == "No", "No internet service",
                       rng.choice(["Yes", "No"], N, p=[0.44, 0.56]))
tech_sup = np.where(internet == "No", "No internet service",
                    rng.choice(["Yes", "No"], N, p=[0.37, 0.63]))
stream_tv = np.where(internet == "No", "No internet service",
                     rng.choice(["Yes", "No"], N, p=[0.49, 0.51]))
stream_mov = np.where(internet == "No", "No internet service",
                      rng.choice(["Yes", "No"], N, p=[0.50, 0.50]))
contract = rng.choice(["Month-to-month", "One year", "Two year"], N, p=[0.55, 0.21, 0.24])
paperless = rng.choice(["Yes", "No"], N, p=[0.59, 0.41])
pay_method = rng.choice(["Electronic check", "Mailed check",
                         "Bank transfer (automatic)", "Credit card (automatic)"],
                        N, p=[0.34, 0.23, 0.22, 0.21])

# Realistic monthly charges tied to services
base = 20.0
mc = base + rng.normal(0, 3, N)
mc += np.where(internet == "DSL", 25, 0)
mc += np.where(internet == "Fiber optic", 45, 0)
mc += np.where(phone == "Yes", 5, 0)
mc += np.where(multi_lines == "Yes", 5, 0)
for svc in (online_sec, online_bak, device_prot, tech_sup, stream_tv, stream_mov):
    mc += np.where(svc == "Yes", 5, 0)
monthly_charges = np.round(np.clip(mc, 18, 120), 2)
total_charges = np.round(monthly_charges * tenure + rng.normal(0, 15, N), 2)
total_charges = np.where(tenure == 0, 0.0, np.clip(total_charges, 0, None))

# Churn probability model — reflects the real IBM benchmark drivers.
logit = -1.6
logit += 1.4 * (contract == "Month-to-month")
logit += -1.1 * (contract == "Two year")
logit += 0.6 * (internet == "Fiber optic")
logit += -0.9 * (internet == "No")
logit += -0.03 * tenure
logit += 0.5 * senior
logit += 0.4 * (pay_method == "Electronic check")
logit += -0.3 * (tech_sup == "Yes")
logit += -0.25 * (online_sec == "Yes")
logit += 0.25 * (paperless == "Yes")
prob = 1 / (1 + np.exp(-logit))
churn = (rng.random(N) < prob).astype(int)

df = pd.DataFrame({
    "customerID": [f"C{7000000+i}" for i in range(N)],
    "gender": gender, "SeniorCitizen": senior, "Partner": partner, "Dependents": dependents,
    "tenure": tenure, "PhoneService": phone, "MultipleLines": multi_lines,
    "InternetService": internet, "OnlineSecurity": online_sec, "OnlineBackup": online_bak,
    "DeviceProtection": device_prot, "TechSupport": tech_sup, "StreamingTV": stream_tv,
    "StreamingMovies": stream_mov, "Contract": contract, "PaperlessBilling": paperless,
    "PaymentMethod": pay_method, "MonthlyCharges": monthly_charges,
    "TotalCharges": total_charges, "Churn": np.where(churn == 1, "Yes", "No"),
})
df.to_csv(str(Path(__file__).parent / "telco_churn.csv"), index=False)
print(f"rows={len(df):,}  churn_rate={churn.mean():.3f}")
