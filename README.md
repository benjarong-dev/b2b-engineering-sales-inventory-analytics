# B2B Industrial Engineering Sales, Backlog & VMI Inventory Analytics

End-to-end business data analysis and interactive executive BI dashboard modeled for **B2B industrial engineering, equipment supply, and Vendor-Managed Inventory (VMI)** operations. Combines **SQLite window-function queries**, **Python statistical KPI modeling**, and a zero-dependency **HTML5 Executive Dashboard** hosted via GitHub Pages.

## Live Executive BI Dashboard

Once GitHub Pages is enabled on `main`, open:
`https://benjarong-dev.github.io/b2b-engineering-sales-inventory-analytics/`

## Business Questions Addressed

1. **Quotation Win-Rate & Margin Mix:** How do win rates and gross margins compare between **Direct Equipment Supply** (fast revenue recognition) and **Turnkey EPC Installation** across 4 industrial business units?
2. **Backlog Burn & Revenue Visibility:** How much contracted backlog (`THB`) is scheduled for recognition over upcoming quarters vs. at-risk delayed milestones?
3. **VMI Spare-Parts Optimization (ABC & Reorder Point):** Which critical Class-A plant spare parts breach their 95%-service-level **Reorder Point (`ROP`)**, and which slow-moving Class-C items tie up working capital?

## Repository Structure

```text
b2b-engineering-sales-inventory-analytics/
├── LICENSE                         # MIT License
├── README.md                       # Business context, KPI formulas, and SQL verification
├── index.html                      # Interactive Executive BI Dashboard (GitHub Pages)
├── dashboard.js                    # Client-side KPI filtering, Canvas charts & CSV export
├── styles.css                      # Clean tabular & analytical dashboard stylesheet
├── src/
│   ├── __init__.py
│   └── analyze_b2b_kpis.py         # Deterministic CSV generator + SQLite KPI & ROP engine
└── tests/
    └── test_b2b_kpis.py            # Automated unit tests for win-rate, Pareto ABC & ROP math
```

## Core Analytical Definitions & Formulas

| Domain | Metric | Formula / SQL Logic |
|---|---|---|
| **Sales Pipeline** | Quotation Win-Rate (%) | `Won Quotations / (Won + Lost Quotations) * 100` |
| **Project Finance** | Contracted Backlog (`THB`) | `SUM(contract_value_thb - recognized_revenue_thb)` for active won deals |
| **Profitability** | Blended Gross Margin (%) | `SUM(gross_profit_thb) / SUM(recognized_revenue_thb) * 100` |
| **VMI Inventory** | Pareto ABC Classification | Cumulative annual consumption value via `SUM(val) OVER (ORDER BY val DESC)` (`A <= 80%`, `B <= 95%`, `C > 95%`) |
| **Supply Chain** | Reorder Point (`ROP`) | `(avg_daily_usage * lead_time_days) + (1.645 * std_daily_usage * sqrt(lead_time_days))` (95% service level) |

## Local Verification (Zero Third-Party Packages Required)

```bash
git clone https://github.com/benjarong-dev/b2b-engineering-sales-inventory-analytics.git
cd b2b-engineering-sales-inventory-analytics

# 1. Run unit tests for SQL window queries, margin math, and ROP calculations
python3 -m unittest discover -s tests -v

# 2. Generate synthetic CSV datasets, run SQLite analytics, and print JSON KPI summary
python3 -m src.analyze_b2b_kpis --output-dir ./outputs
```

## License

Distributed under the MIT License. See `LICENSE` for details.
