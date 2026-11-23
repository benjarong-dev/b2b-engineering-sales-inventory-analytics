"""Unit tests for B2B engineering revenue reconciliation, Pareto ABC, and VMI ROP."""

from pathlib import Path
import tempfile
import unittest

from src.analyze_b2b_kpis import compute_reorder_point, export_csv_and_report


class B2BAnalyticsTestSuite(unittest.TestCase):
    def test_reorder_point_includes_95_percent_safety_stock(self) -> None:
        rop = compute_reorder_point(avg_daily_usage=0.90, std_daily_usage=0.25, lead_time_days=28)
        self.assertEqual(rop, 28)
        self.assertEqual(compute_reorder_point(0.0, 0.2, 14), 0)

    def test_backlog_plus_recognized_equals_total_won_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report = export_csv_and_report(Path(tmp_dir))
            summary = report["executive_summary"]

            self.assertEqual(
                summary["recognized_revenue_thb"] + summary["remaining_backlog_thb"],
                summary["won_contract_thb"],
            )
            self.assertEqual(summary["win_rate_pct"], 72.7)

    def test_direct_supply_delivers_higher_gross_margin_than_turnkey_epc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report = export_csv_and_report(Path(tmp_dir))
            mix = {row["deal_type"]: row for row in report["by_deal_type"]}

            self.assertGreater(
                mix["Direct Supply"]["gross_margin_pct"],
                mix["Turnkey EPC"]["gross_margin_pct"],
            )

    def test_pareto_abc_flags_critical_stockout_risk_and_class_c_overstock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report = export_csv_and_report(Path(tmp_dir))
            items = {row["sku_code"]: row for row in report["vmi_pareto_inventory"]}

            self.assertEqual(items["SP-FGD-101"]["abc_class"], "A")
            self.assertEqual(items["SP-FGD-101"]["stock_status"], "REORDER_NOW")
            self.assertEqual(items["SP-FLT-612"]["abc_class"], "C")
            self.assertEqual(items["SP-FLT-612"]["stock_status"], "OVERSTOCK_SLOW")


if __name__ == "__main__":
    unittest.main()
