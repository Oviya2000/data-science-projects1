"""Generate an HR attrition dataset (IBM-style) for the Power BI project."""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)
N = 1470  # same size as the IBM HR Analytics benchmark

departments = ["Sales", "Research & Development", "Human Resources"]
dept = rng.choice(departments, N, p=[0.31, 0.65, 0.04])
roles_by_dept = {
    "Sales": ["Sales Executive", "Sales Representative", "Manager"],
    "Research & Development": ["Research Scientist", "Laboratory Technician",
                                "Research Director", "Manager", "Healthcare Representative"],
    "Human Resources": ["Human Resources", "Manager"],
}
role = np.array([rng.choice(roles_by_dept[d]) for d in dept])

age = rng.integers(20, 60, N)
gender = rng.choice(["Male", "Female"], N, p=[0.6, 0.4])
education = rng.choice([1, 2, 3, 4, 5], N, p=[0.11, 0.19, 0.39, 0.27, 0.04])
education_field = rng.choice(
    ["Life Sciences", "Medical", "Marketing", "Technical Degree", "Other", "Human Resources"],
    N, p=[0.41, 0.32, 0.11, 0.09, 0.05, 0.02],
)
marital = rng.choice(["Single", "Married", "Divorced"], N, p=[0.32, 0.46, 0.22])
distance_km = rng.integers(1, 30, N)
years_at_company = rng.integers(0, 25, N)
years_in_role = np.minimum(years_at_company, rng.integers(0, 15, N))
years_since_promo = np.minimum(years_in_role, rng.integers(0, 10, N))
years_with_manager = np.minimum(years_at_company, rng.integers(0, 15, N))
num_companies_worked = rng.integers(0, 8, N)
total_working_years = years_at_company + rng.integers(0, 15, N)
training_last_year = rng.integers(0, 7, N)

job_level = rng.choice([1, 2, 3, 4, 5], N, p=[0.37, 0.36, 0.15, 0.07, 0.05])
monthly_income = np.round(
    2000 + job_level * 2500 + rng.normal(0, 900, N) + age * 40, 0
).astype(int)
monthly_income = np.clip(monthly_income, 1500, 20000)
percent_salary_hike = rng.integers(11, 26, N)

overtime = rng.choice(["Yes", "No"], N, p=[0.28, 0.72])
business_travel = rng.choice(["Non-Travel", "Travel_Rarely", "Travel_Frequently"],
                             N, p=[0.10, 0.71, 0.19])
job_satisfaction = rng.integers(1, 5, N)
env_satisfaction = rng.integers(1, 5, N)
work_life_balance = rng.integers(1, 5, N)
relationship_satisfaction = rng.integers(1, 5, N)
performance_rating = rng.choice([3, 4], N, p=[0.85, 0.15])
job_involvement = rng.integers(1, 5, N)
stock_option = rng.choice([0, 1, 2, 3], N, p=[0.43, 0.41, 0.11, 0.05])

# Attrition logistic — mirrors documented IBM HR drivers.
logit = 1.4
logit += 0.9 * (overtime == "Yes")
logit += 0.5 * (business_travel == "Travel_Frequently")
logit -= 0.08 * years_at_company
logit -= 0.06 * years_with_manager
logit += 0.03 * distance_km
logit -= 0.30 * job_involvement
logit -= 0.25 * job_satisfaction
logit -= 0.20 * env_satisfaction
logit -= 0.20 * work_life_balance
logit -= 0.00008 * monthly_income
logit += 0.02 * (30 - age)
logit += 0.30 * (marital == "Single")
prob = 1 / (1 + np.exp(-logit))
attrition = np.where(rng.random(N) < prob, "Yes", "No")

df = pd.DataFrame({
    "EmployeeID": np.arange(1, N + 1),
    "Age": age, "Gender": gender, "MaritalStatus": marital,
    "Department": dept, "JobRole": role, "JobLevel": job_level,
    "Education": education, "EducationField": education_field,
    "DistanceFromHome": distance_km, "BusinessTravel": business_travel,
    "OverTime": overtime, "MonthlyIncome": monthly_income,
    "PercentSalaryHike": percent_salary_hike, "StockOptionLevel": stock_option,
    "YearsAtCompany": years_at_company, "YearsInCurrentRole": years_in_role,
    "YearsSinceLastPromotion": years_since_promo,
    "YearsWithCurrManager": years_with_manager,
    "NumCompaniesWorked": num_companies_worked,
    "TotalWorkingYears": total_working_years,
    "TrainingTimesLastYear": training_last_year,
    "JobSatisfaction": job_satisfaction,
    "EnvironmentSatisfaction": env_satisfaction,
    "WorkLifeBalance": work_life_balance,
    "RelationshipSatisfaction": relationship_satisfaction,
    "JobInvolvement": job_involvement, "PerformanceRating": performance_rating,
    "Attrition": attrition,
})
df.to_csv(str(Path(__file__).parent / "hr_attrition.csv"), index=False)
print(f"rows={len(df):,}  attrition_rate={(attrition=='Yes').mean():.3f}")
