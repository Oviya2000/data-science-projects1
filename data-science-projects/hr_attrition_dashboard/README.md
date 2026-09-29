# HR Attrition — Data Analysis & Power BI-style Dashboard

End-to-end analytics project on employee attrition: a cleaned dataset,
Power Query steps, a documented star schema, DAX measures, and a live
interactive dashboard that mirrors the Power BI report page.

Because Power BI files (`.pbix`) cannot render in a hosted portfolio,
`dashboard.html` is a self-contained HTML replica of the same report
page with the same slicers, KPI row and visuals — one click, no login.
The DAX model that would back a real Power BI publish is documented
in `dax_measures.md`.

## Dataset

- 1,470 rows, 29 columns, 0 nulls, 0 duplicates.
- Schema mirrors the IBM HR Analytics Employee Attrition benchmark;
  attrition is generated from a documented logistic model
  (`generate_hr_data.py`) with the same causal structure as the real
  dataset.
- Company-wide attrition rate: **12.5 %**.

## Findings

| Segment | Attrition | vs. company |
|---|---|---|
| Overtime = **Yes** | 18.9 % | +6.4 pp |
| Age band **20-29** | 14.6 % | +2.2 pp |
| Income band **3-5k** | 17.7 % | +5.3 pp |
| Overtime = No | 10.1 % | −2.4 pp |
| Age 50+ | 10.1 % | −2.4 pp |

Overtime nearly doubles attrition against no-overtime peers — the
strongest single lever on the dataset.

## Repo layout

```
hr_attrition_dashboard/
├── generate_hr_data.py     # reproducible synthetic dataset
├── eda.py                  # data-quality + segment aggregates
├── dashboard.html          # ONE-FILE interactive Power BI replica
├── dax_measures.md         # star schema, Power Query steps, DAX
├── hr_attrition.csv        # 1,470 rows
├── data_quality.json
└── dashboard_data/         # aggregates the dashboard displays
    ├── by_department.csv
    ├── by_job_role.csv
    ├── by_overtime.csv
    ├── by_travel.csv
    ├── by_marital.csv
    ├── by_gender.csv
    ├── by_age_band.csv
    ├── by_tenure_band.csv
    ├── by_income_band.csv
    └── satisfaction_matrix.csv
```

## Dashboard visuals

- **KPI cards** — Employees, Leavers, Attrition Rate (with pp delta vs. company), Avg Income, Avg Tenure.
- **Slicers** — Department, Overtime, Gender, Business Travel (cross-filter every visual).
- **Bar / column charts** — attrition by department, job role, age band, tenure band, income band, overtime, business travel.
- **Reset button** — clears all slicers.

## Reproducing

```bash
python3 generate_hr_data.py    # writes hr_attrition.csv
python3 eda.py                 # writes dashboard_data/*.csv
xdg-open dashboard.html        # or double-click
```

## In a real Power BI publish

1. Load `hr_attrition.csv` into Power BI Desktop.
2. Apply the Power Query steps in `dax_measures.md`.
3. Build the star schema (`FactEmployee`, `DimDepartment`, `DimJobRole`, `DimDate`, `DimDemographics`).
4. Paste the DAX measures.
5. Recreate the visuals per the "Visuals in the report page" table.
6. Publish to Power BI Service; set the daily refresh from OneDrive.

## Tech

Python 3.12 · pandas · Power BI (documented) · Chart.js (HTML replica)
