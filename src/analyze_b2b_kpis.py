"""SQLite & Python KPI analytics for B2B engineering backlog and VMI spare parts."""

from __future__ import annotations

import argparse
from contextlib import closing
import csv
import json
import math
from pathlib import Path
import sqlite3
import sys
from typing import Dict, List, Optional

Z_SCORE_95 = 1.645

QUOTATION_RECORDS: List[Dict[str, object]] = [
    {"quote_id": "Q-2026-001", "business_unit": "Power & Flue-Gas", "deal_type": "Direct Supply", "status": "WON", "contract_thb": 18500000, "recognized_thb": 14800000, "cogs_thb": 10212000},
    {"quote_id": "Q-2026-002", "business_unit": "Power & Flue-Gas", "deal_type": "Turnkey EPC", "status": "WON", "contract_thb": 42000000, "recognized_thb": 16800000, "cogs_thb": 12768000},
    {"quote_id": "Q-2026-003", "business_unit": "Power & Flue-Gas", "deal_type": "Direct Supply", "status": "LOST", "contract_thb": 12400000, "recognized_thb": 0, "cogs_thb": 0},
    {"quote_id": "Q-2026-004", "business_unit": "Telecom & UPS", "deal_type": "Direct Supply", "status": "WON", "contract_thb": 24600000, "recognized_thb": 21000000, "cogs_thb": 14280000},
    {"quote_id": "Q-2026-005", "business_unit": "Telecom & UPS", "deal_type": "Turnkey EPC", "status": "WON", "contract_thb": 36500000, "recognized_thb": 14600000, "cogs_thb": 10950000},
    {"quote_id": "Q-2026-006", "business_unit": "Telecom & UPS", "deal_type": "Turnkey EPC", "status": "LOST", "contract_thb": 19000000, "recognized_thb": 0, "cogs_thb": 0},
    {"quote_id": "Q-2026-007", "business_unit": "Oil & Gas Support", "deal_type": "Direct Supply", "status": "WON", "contract_thb": 29800000, "recognized_thb": 19370000, "cogs_thb": 13171600},
    {"quote_id": "Q-2026-008", "business_unit": "Oil & Gas Support", "deal_type": "Direct Supply", "status": "LOST", "contract_thb": 15200000, "recognized_thb": 0, "cogs_thb": 0},
    {"quote_id": "Q-2026-009", "business_unit": "Environmental & Clean Energy", "deal_type": "Turnkey EPC", "status": "WON", "contract_thb": 31200000, "recognized_thb": 10920000, "cogs_thb": 8080800},
    {"quote_id": "Q-2026-010", "business_unit": "Environmental & Clean Energy", "deal_type": "Direct Supply", "status": "WON", "contract_thb": 14800000, "recognized_thb": 11840000, "cogs_thb": 8051200},
    {"quote_id": "Q-2026-011", "business_unit": "Environmental & Clean Energy", "deal_type": "Turnkey EPC", "status": "PENDING", "contract_thb": 27500000, "recognized_thb": 0, "cogs_thb": 0},
    {"quote_id": "Q-2026-012", "business_unit": "Power & Flue-Gas", "deal_type": "Direct Supply", "status": "WON", "contract_thb": 22400000, "recognized_thb": 17920000, "cogs_thb": 12185600},
]

SPARE_PART_RECORDS: List[Dict[str, object]] = [
    {"sku_code": "SP-FGD-101", "part_name": "Flue-Gas Desulfurization Nozzle Assembly", "business_unit": "Power & Flue-Gas", "unit_cost_thb": 48000, "annual_units": 320, "on_hand_qty": 18, "avg_daily_usage": 0.90, "std_daily_usage": 0.25, "lead_time_days": 28},
    {"sku_code": "SP-UPS-204", "part_name": "Industrial Modular UPS IGBT Power Module", "business_unit": "Telecom & UPS", "unit_cost_thb": 62000, "annual_units": 210, "on_hand_qty": 14, "avg_daily_usage": 0.60, "std_daily_usage": 0.20, "lead_time_days": 30},
    {"sku_code": "SP-BRN-108", "part_name": "Low-NOx Burner Igniter & Flame Scanner", "business_unit": "Power & Flue-Gas", "unit_cost_thb": 35000, "annual_units": 260, "on_hand_qty": 34, "avg_daily_usage": 0.72, "std_daily_usage": 0.18, "lead_time_days": 21},
    {"sku_code": "SP-VLV-302", "part_name": "High-Pressure Actuated Isolation Valve", "business_unit": "Oil & Gas Support", "unit_cost_thb": 85000, "annual_units": 95, "on_hand_qty": 9, "avg_daily_usage": 0.28, "std_daily_usage": 0.11, "lead_time_days": 35},
    {"sku_code": "SP-CEM-401", "part_name": "CEMS SO2/NOx Optical Gas Analyzer Cell", "business_unit": "Environmental & Clean Energy", "unit_cost_thb": 29000, "annual_units": 150, "on_hand_qty": 22, "avg_daily_usage": 0.42, "std_daily_usage": 0.12, "lead_time_days": 25},
    {"sku_code": "SP-RFM-209", "part_name": "Unified Tactical Radio Transceiver Card", "business_unit": "Telecom & UPS", "unit_cost_thb": 19500, "annual_units": 140, "on_hand_qty": 28, "avg_daily_usage": 0.38, "std_daily_usage": 0.10, "lead_time_days": 20},
    {"sku_code": "SP-GSK-510", "part_name": "Spiral Wound Heat-Exchanger Gasket Kit", "business_unit": "Oil & Gas Support", "unit_cost_thb": 4200, "annual_units": 410, "on_hand_qty": 190, "avg_daily_usage": 1.12, "std_daily_usage": 0.30, "lead_time_days": 14},
    {"sku_code": "SP-FLT-612", "part_name": "Auxiliary Control Cabinet Air Filter Pad", "business_unit": "Environmental & Clean Energy", "unit_cost_thb": 1800, "annual_units": 520, "on_hand_qty": 260, "avg_daily_usage": 1.40, "std_daily_usage": 0.35, "lead_time_days": 10},
]


def compute_reorder_point(
    avg_daily_usage: float,
    std_daily_usage: float,
    lead_time_days: int,
    z_score: float = Z_SCORE_95,
) -> int:
    """Computes integer Reorder Point (ROP) with statistical safety stock."""
    if lead_time_days <= 0 or avg_daily_usage <= 0:
        return 0
    demand_during_lt = avg_daily_usage * lead_time_days
    safety_stock = z_score * max(0.0, std_daily_usage) * math.sqrt(lead_time_days)
    return int(math.ceil(demand_during_lt + safety_stock))


def build_sqlite_warehouse(db_path: Path) -> None:
    """Loads quotations and VMI spare-parts tables into SQLite."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            conn.executescript(
                """
                DROP TABLE IF EXISTS quotations;
                DROP TABLE IF EXISTS spare_parts;

                CREATE TABLE quotations (
                    quote_id TEXT PRIMARY KEY,
                    business_unit TEXT NOT NULL,
                    deal_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    contract_thb REAL NOT NULL,
                    recognized_thb REAL NOT NULL,
                    cogs_thb REAL NOT NULL
                );

                CREATE TABLE spare_parts (
                    sku_code TEXT PRIMARY KEY,
                    part_name TEXT NOT NULL,
                    business_unit TEXT NOT NULL,
                    unit_cost_thb REAL NOT NULL,
                    annual_units INTEGER NOT NULL,
                    on_hand_qty INTEGER NOT NULL,
                    avg_daily_usage REAL NOT NULL,
                    std_daily_usage REAL NOT NULL,
                    lead_time_days INTEGER NOT NULL,
                    rop_qty INTEGER NOT NULL
                );
                """
            )

            conn.executemany(
                """
                INSERT INTO quotations (
                    quote_id, business_unit, deal_type, status,
                    contract_thb, recognized_thb, cogs_thb
                ) VALUES (:quote_id, :business_unit, :deal_type, :status, :contract_thb, :recognized_thb, :cogs_thb);
                """,
                QUOTATION_RECORDS,
            )

            enriched_parts = []
            for item in SPARE_PART_RECORDS:
                rop = compute_reorder_point(
                    float(item["avg_daily_usage"]),
                    float(item["std_daily_usage"]),
                    int(item["lead_time_days"]),
                )
                row = dict(item)
                row["rop_qty"] = rop
                enriched_parts.append(row)

            conn.executemany(
                """
                INSERT INTO spare_parts (
                    sku_code, part_name, business_unit, unit_cost_thb,
                    annual_units, on_hand_qty, avg_daily_usage,
                    std_daily_usage, lead_time_days, rop_qty
                ) VALUES (
                    :sku_code, :part_name, :business_unit, :unit_cost_thb,
                    :annual_units, :on_hand_qty, :avg_daily_usage,
                    :std_daily_usage, :lead_time_days, :rop_qty
                );
                """,
                enriched_parts,
            )


def run_kpi_queries(db_path: Path) -> Dict[str, object]:
    """Executes SQLite aggregations and window functions for Sales, Backlog & VMI."""
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row

        exec_row = conn.execute(
            """
            SELECT
                SUM(CASE WHEN status = 'WON' THEN 1 ELSE 0 END) AS won_deals,
                SUM(CASE WHEN status IN ('WON', 'LOST') THEN 1 ELSE 0 END) AS closed_deals,
                SUM(CASE WHEN status = 'WON' THEN contract_thb ELSE 0 END) AS won_contract_thb,
                SUM(CASE WHEN status = 'WON' THEN recognized_thb ELSE 0 END) AS recognized_thb,
                SUM(CASE WHEN status = 'WON' THEN (contract_thb - recognized_thb) ELSE 0 END) AS backlog_thb,
                SUM(CASE WHEN status = 'WON' THEN (recognized_thb - cogs_thb) ELSE 0 END) AS gross_profit_thb
            FROM quotations;
            """
        ).fetchone()

        win_rate_pct = round((exec_row["won_deals"] / exec_row["closed_deals"]) * 100.0, 1)
        gross_margin_pct = round(
            (exec_row["gross_profit_thb"] / exec_row["recognized_thb"]) * 100.0, 1
        )

        bu_rows = conn.execute(
            """
            SELECT
                business_unit,
                ROUND(
                    100.0 * SUM(CASE WHEN status = 'WON' THEN 1 ELSE 0 END) /
                    NULLIF(SUM(CASE WHEN status IN ('WON', 'LOST') THEN 1 ELSE 0 END), 0),
                    1
                ) AS win_rate_pct,
                SUM(CASE WHEN status = 'WON' THEN recognized_thb ELSE 0 END) AS recognized_thb,
                SUM(CASE WHEN status = 'WON' THEN (contract_thb - recognized_thb) ELSE 0 END) AS backlog_thb,
                ROUND(
                    100.0 * SUM(CASE WHEN status = 'WON' THEN (recognized_thb - cogs_thb) ELSE 0 END) /
                    NULLIF(SUM(CASE WHEN status = 'WON' THEN recognized_thb ELSE 0 END), 0),
                    1
                ) AS gross_margin_pct
            FROM quotations
            GROUP BY business_unit
            ORDER BY recognized_thb DESC;
            """
        ).fetchall()

        mix_rows = conn.execute(
            """
            SELECT
                deal_type,
                COUNT(*) AS deal_count,
                SUM(recognized_thb) AS recognized_thb,
                SUM(contract_thb - recognized_thb) AS backlog_thb,
                ROUND(100.0 * SUM(recognized_thb - cogs_thb) / SUM(recognized_thb), 1) AS gross_margin_pct
            FROM quotations
            WHERE status = 'WON'
            GROUP BY deal_type
            ORDER BY recognized_thb DESC;
            """
        ).fetchall()

        abc_rows = conn.execute(
            """
            WITH spend_cte AS (
                SELECT
                    sku_code,
                    part_name,
                    business_unit,
                    unit_cost_thb,
                    annual_units,
                    (unit_cost_thb * annual_units) AS annual_spend_thb,
                    on_hand_qty,
                    rop_qty,
                    avg_daily_usage
                FROM spare_parts
            ),
            pareto_cte AS (
                SELECT
                    *,
                    ROUND(
                        100.0 * SUM(annual_spend_thb) OVER (
                            ORDER BY annual_spend_thb DESC, sku_code ASC
                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                        ) / SUM(annual_spend_thb) OVER (),
                        1
                    ) AS cumulative_spend_pct
                FROM spend_cte
            )
            SELECT
                sku_code,
                part_name,
                business_unit,
                annual_spend_thb,
                cumulative_spend_pct,
                CASE
                    WHEN cumulative_spend_pct <= 80.0 THEN 'A'
                    WHEN cumulative_spend_pct <= 96.0 THEN 'B'
                    ELSE 'C'
                END AS abc_class,
                on_hand_qty,
                rop_qty,
                CASE
                    WHEN on_hand_qty <= rop_qty THEN 'REORDER_NOW'
                    WHEN (on_hand_qty / NULLIF(avg_daily_usage, 0)) > 120.0 THEN 'OVERSTOCK_SLOW'
                    ELSE 'HEALTHY'
                END AS stock_status
            FROM pareto_cte
            ORDER BY annual_spend_thb DESC, sku_code ASC;
            """
        ).fetchall()

    return {
        "executive_summary": {
            "win_rate_pct": win_rate_pct,
            "won_contract_thb": exec_row["won_contract_thb"],
            "recognized_revenue_thb": exec_row["recognized_thb"],
            "remaining_backlog_thb": exec_row["backlog_thb"],
            "blended_gross_margin_pct": gross_margin_pct,
        },
        "by_business_unit": [dict(r) for r in bu_rows],
        "by_deal_type": [dict(r) for r in mix_rows],
        "vmi_pareto_inventory": [dict(r) for r in abc_rows],
    }


def export_csv_and_report(output_dir: Path) -> Dict[str, object]:
    """Writes CSV datasets, builds SQLite DB, and exports JSON KPI summary."""
    output_dir.mkdir(parents=True, exist_ok=True)
    quotes_csv = output_dir / "quotations.csv"
    parts_csv = output_dir / "vmi_spare_parts.csv"
    db_path = output_dir / "b2b_analytics.db"
    report_json = output_dir / "kpi_summary.json"

    with quotes_csv.open("w", newline="", encoding="utf-8") as fq:
        writer = csv.DictWriter(fq, fieldnames=list(QUOTATION_RECORDS[0].keys()))
        writer.writeheader()
        writer.writerows(QUOTATION_RECORDS)

    with parts_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(SPARE_PART_RECORDS[0].keys()))
        writer.writeheader()
        writer.writerows(SPARE_PART_RECORDS)

    build_sqlite_warehouse(db_path)
    report = run_kpi_queries(db_path)
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run B2B sales, backlog & VMI SQL analytics.")
    parser.add_argument("--output-dir", type=str, default="./outputs", help="Output folder path.")
    args = parser.parse_args(argv)

    report = export_csv_and_report(Path(args.output_dir))
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
