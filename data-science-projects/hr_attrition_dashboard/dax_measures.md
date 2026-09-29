# Power BI Data Model & DAX Measures

## Star schema

```
                    ┌────────────────────┐
                    │  DimDate           │
                    │  DateKey (PK)      │
                    │  Year, Quarter,    │
                    │  Month, MonthName  │
                    └─────────┬──────────┘
                              │
   ┌────────────────┐   ┌─────┴──────────┐   ┌───────────────────┐
   │ DimDepartment  │◄──┤  FactEmployee  ├──►│ DimJobRole        │
   │ DeptKey (PK)   │   │  EmpKey (PK)   │   │ RoleKey (PK)      │
   │ Department     │   │  DeptKey (FK)  │   │ JobRole           │
   └────────────────┘   │  RoleKey (FK)  │   │ JobLevel          │
                       │  HireDate (FK) │   └───────────────────┘
   ┌────────────────┐   │  Age, Gender   │
   │ DimDemographics│◄──┤  Attrition     │   ┌───────────────────┐
   │ DemoKey (PK)   │   │  MonthlyIncome ├──►│ DimCompensation   │
   │ AgeBand        │   │  YearsAt…      │   │ CompKey (PK)      │
   │ TenureBand     │   │  Satisfaction  │   │ IncomeBand        │
   │ MaritalStatus  │   │  OverTime      │   │ StockOptionLevel  │
   └────────────────┘   └────────────────┘   └───────────────────┘
```

## Power Query steps

1. **Source** — CSV `hr_attrition.csv` (1,470 rows).
2. **Change type** — set `Age`, `MonthlyIncome`, `YearsAtCompany` to whole numbers; `Attrition`, `OverTime`, `Department` to text.
3. **Add banded columns**
   * `AgeBand` — nested `if` on `Age`.
   * `TenureBand` — nested `if` on `YearsAtCompany`.
   * `IncomeBand` — nested `if` on `MonthlyIncome`.
4. **Boolean flag** — `IsAttrition = if [Attrition] = "Yes" then 1 else 0`.
5. **Merge queries** — join to `DimDate` on synthetic `HireDate` for time-intelligence.

## DAX measures

### Base

```DAX
Employees            = COUNTROWS( FactEmployee )
Leavers              = CALCULATE( COUNTROWS( FactEmployee ),
                                  FactEmployee[Attrition] = "Yes" )
Stayers              = [Employees] - [Leavers]
Attrition Rate       = DIVIDE( [Leavers], [Employees], 0 )
Attrition Rate %     = FORMAT( [Attrition Rate], "0.0%" )
```

### Compensation & tenure

```DAX
Avg Monthly Income   = AVERAGE( FactEmployee[MonthlyIncome] )
Median Income        = MEDIAN(  FactEmployee[MonthlyIncome] )
Avg Tenure (Years)   = AVERAGE( FactEmployee[YearsAtCompany] )
Salary Delta vs Co   =
    [Avg Monthly Income]
        - CALCULATE( [Avg Monthly Income], ALL( FactEmployee ) )
```

### Segment risk

```DAX
Attrition vs Company =
    [Attrition Rate] - CALCULATE( [Attrition Rate], ALL( FactEmployee ) )

High-Risk Flag =
    IF( [Attrition Rate] > 1.5 * CALCULATE( [Attrition Rate], ALL( FactEmployee ) ),
        "🔴 High", "🟢 Normal" )
```

### Overtime & travel effects

```DAX
Overtime Attrition   = CALCULATE( [Attrition Rate], FactEmployee[OverTime] = "Yes" )
No-Overtime Attrition = CALCULATE( [Attrition Rate], FactEmployee[OverTime] = "No" )
Overtime Lift        = [Overtime Attrition] - [No-Overtime Attrition]
```

### Time intelligence (once tied to `DimDate`)

```DAX
Attrition YTD        =
    TOTALYTD( [Leavers], DimDate[Date] )

Attrition MoM %      =
    VAR Prior = CALCULATE( [Attrition Rate], DATEADD(DimDate[Date], -1, MONTH) )
    RETURN DIVIDE( [Attrition Rate] - Prior, Prior )
```

## Visuals in the report page

| Section | Visual | Field(s) |
|---|---|---|
| KPI row (top)   | 5× card visuals | Employees · Leavers · Attrition Rate % · Avg Income · Avg Tenure |
| Left panel      | Slicers | Department · JobRole · Gender · OverTime |
| Row 1 chart 1   | Donut  | `Attrition` count |
| Row 1 chart 2   | Bar    | `JobRole` × `Attrition Rate` (sorted desc) |
| Row 2 chart 1   | Stacked column | `AgeBand` × `Attrition` |
| Row 2 chart 2   | Column | `IncomeBand` × `Attrition Rate` |
| Row 3 chart 1   | Small multiples | `OverTime` × `BusinessTravel` × `Attrition Rate` |
| Row 3 chart 2   | Matrix heat | `JobSatisfaction` × `WorkLifeBalance` |
| Drill-through   | Table  | `EmployeeID`, all HR fields for the selected slice |

## Refresh

Scheduled daily refresh from the source CSV in OneDrive; incremental refresh
on `HireDate` (retain 5 years, refresh last 30 days).
