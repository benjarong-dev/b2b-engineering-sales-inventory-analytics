const Z_95 = 1.645;

const QUOTATIONS = [
  { id: "Q-2026-001", bu: "Power & Flue-Gas", type: "Direct Supply", status: "WON", contract: 18500000, rec: 14800000, cogs: 10212000 },
  { id: "Q-2026-002", bu: "Power & Flue-Gas", type: "Turnkey EPC", status: "WON", contract: 42000000, rec: 16800000, cogs: 12768000 },
  { id: "Q-2026-003", bu: "Power & Flue-Gas", type: "Direct Supply", status: "LOST", contract: 12400000, rec: 0, cogs: 0 },
  { id: "Q-2026-004", bu: "Telecom & UPS", type: "Direct Supply", status: "WON", contract: 24600000, rec: 21000000, cogs: 14280000 },
  { id: "Q-2026-005", bu: "Telecom & UPS", type: "Turnkey EPC", status: "WON", contract: 36500000, rec: 14600000, cogs: 10950000 },
  { id: "Q-2026-006", bu: "Telecom & UPS", type: "Turnkey EPC", status: "LOST", contract: 19000000, rec: 0, cogs: 0 },
  { id: "Q-2026-007", bu: "Oil & Gas Support", type: "Direct Supply", status: "WON", contract: 29800000, rec: 19370000, cogs: 13171600 },
  { id: "Q-2026-008", bu: "Oil & Gas Support", type: "Direct Supply", status: "LOST", contract: 15200000, rec: 0, cogs: 0 },
  { id: "Q-2026-009", bu: "Environmental & Clean Energy", type: "Turnkey EPC", status: "WON", contract: 31200000, rec: 10920000, cogs: 8080800 },
  { id: "Q-2026-010", bu: "Environmental & Clean Energy", type: "Direct Supply", status: "WON", contract: 14800000, rec: 11840000, cogs: 8051200 },
  { id: "Q-2026-011", bu: "Environmental & Clean Energy", type: "Turnkey EPC", status: "PENDING", contract: 27500000, rec: 0, cogs: 0 },
  { id: "Q-2026-012", bu: "Power & Flue-Gas", type: "Direct Supply", status: "WON", contract: 22400000, rec: 17920000, cogs: 12185600 }
];

const SPARE_PARTS = [
  { sku: "SP-FGD-101", name: "Flue-Gas Desulfurization Nozzle Assembly", bu: "Power & Flue-Gas", cost: 48000, annual: 320, onHand: 18, avgDaily: 0.90, stdDaily: 0.25, lt: 28 },
  { sku: "SP-UPS-204", name: "Industrial Modular UPS IGBT Power Module", bu: "Telecom & UPS", cost: 62000, annual: 210, onHand: 14, avgDaily: 0.60, stdDaily: 0.20, lt: 30 },
  { sku: "SP-BRN-108", name: "Low-NOx Burner Igniter & Flame Scanner", bu: "Power & Flue-Gas", cost: 35000, annual: 260, onHand: 34, avgDaily: 0.72, stdDaily: 0.18, lt: 21 },
  { sku: "SP-VLV-302", name: "High-Pressure Actuated Isolation Valve", bu: "Oil & Gas Support", cost: 85000, annual: 95, onHand: 9, avgDaily: 0.28, stdDaily: 0.11, lt: 35 },
  { sku: "SP-CEM-401", name: "CEMS SO2/NOx Optical Gas Analyzer Cell", bu: "Environmental & Clean Energy", cost: 29000, annual: 150, onHand: 22, avgDaily: 0.42, stdDaily: 0.12, lt: 25 },
  { sku: "SP-RFM-209", name: "Unified Tactical Radio Transceiver Card", bu: "Telecom & UPS", cost: 19500, annual: 140, onHand: 28, avgDaily: 0.38, stdDaily: 0.10, lt: 20 },
  { sku: "SP-GSK-510", name: "Spiral Wound Heat-Exchanger Gasket Kit", bu: "Oil & Gas Support", cost: 4200, annual: 410, onHand: 190, avgDaily: 1.12, stdDaily: 0.30, lt: 14 },
  { sku: "SP-FLT-612", name: "Auxiliary Control Cabinet Air Filter Pad", bu: "Environmental & Clean Energy", cost: 1800, annual: 520, onHand: 260, avgDaily: 1.40, stdDaily: 0.35, lt: 10 }
];

function computeRop(avgDaily, stdDaily, lt) {
  return Math.ceil((avgDaily * lt) + (Z_95 * stdDaily * Math.sqrt(lt)));
}

function fmtMillions(val) {
  return `${(val / 1e6).toFixed(2)}M THB`;
}

function buildParetoInventory(selectedBu) {
  const enriched = SPARE_PARTS.map((item) => {
    const spend = item.cost * item.annual;
    const rop = computeRop(item.avgDaily, item.stdDaily, item.lt);
    const daysCover = Math.round(item.onHand / item.avgDaily);
    let status = "HEALTHY";
    if (item.onHand <= rop) status = "REORDER_NOW";
    else if (daysCover > 120) status = "OVERSTOCK_SLOW";
    return { ...item, spend, rop, daysCover, status };
  }).sort((a, b) => b.spend - a.spend || a.sku.localeCompare(b.sku));

  const totalSpend = enriched.reduce((acc, r) => acc + r.spend, 0);
  let cumSpend = 0;
  const withAbc = enriched.map((r) => {
    cumSpend += r.spend;
    const cumPct = (cumSpend / totalSpend) * 100;
    const abc = cumPct <= 80.0 ? "A" : cumPct <= 96.0 ? "B" : "C";
    return { ...r, abc };
  });

  return selectedBu === "ALL" ? withAbc : withAbc.filter((r) => r.bu === selectedBu);
}

let currentInventoryRows = [];

function renderDashboard() {
  const bu = document.getElementById("buFilter").value;
  const deal = document.getElementById("dealFilter").value;

  const quotes = QUOTATIONS.filter(
    (q) => (bu === "ALL" || q.bu === bu) && (deal === "ALL" || q.type === deal)
  );

  const won = quotes.filter((q) => q.status === "WON");
  const closed = quotes.filter((q) => q.status === "WON" || q.status === "LOST");
  const winRate = closed.length ? ((won.length / closed.length) * 100).toFixed(1) : "0.0";

  const recTotal = won.reduce((s, q) => s + q.rec, 0);
  const bklTotal = won.reduce((s, q) => s + (q.contract - q.rec), 0);
  const gpTotal = won.reduce((s, q) => s + (q.rec - q.cogs), 0);
  const gmPct = recTotal > 0 ? ((gpTotal / recTotal) * 100).toFixed(1) : "0.0";

  currentInventoryRows = buildParetoInventory(bu);
  const alerts = currentInventoryRows.filter((r) => r.status === "REORDER_NOW").length;

  document.getElementById("kpiWinRate").textContent = `${winRate}%`;
  document.getElementById("kpiDealCount").textContent = `${won.length} won / ${closed.length} closed bids`;
  document.getElementById("kpiRecognized").textContent = fmtMillions(recTotal);
  document.getElementById("kpiBacklog").textContent = fmtMillions(bklTotal);
  document.getElementById("kpiMargin").textContent = `${gmPct}%`;
  document.getElementById("kpiRopAlerts").textContent = `${alerts} SKUs`;

  const segments = ["Power & Flue-Gas", "Telecom & UPS", "Oil & Gas Support", "Environmental & Clean Energy"];
  const segStats = segments
    .filter((s) => bu === "ALL" || s === bu)
    .map((seg) => {
      const segWon = won.filter((q) => q.bu === seg);
      const rec = segWon.reduce((a, q) => a + q.rec, 0);
      const bkl = segWon.reduce((a, q) => a + (q.contract - q.rec), 0);
      return { seg, rec, bkl, total: rec + bkl };
    });

  const maxSegTotal = Math.max(1, ...segStats.map((s) => s.total));
  document.getElementById("segmentChart").innerHTML = segStats
    .map((s) => {
      const recW = ((s.rec / maxSegTotal) * 100).toFixed(1);
      const bklW = ((s.bkl / maxSegTotal) * 100).toFixed(1);
      return `
        <div class="bar-row">
          <div class="bar-meta">
            <strong>${s.seg}</strong>
            <span>${fmtMillions(s.rec)} rec / ${fmtMillions(s.bkl)} backlog</span>
          </div>
          <div class="bar-track">
            <div class="bar-rec" style="width:${recW}%"></div>
            <div class="bar-bkl" style="width:${bklW}%"></div>
          </div>
        </div>`;
    })
    .join("");

  const dealTypes = ["Direct Supply", "Turnkey EPC"];
  document.getElementById("mixSummary").innerHTML = dealTypes
    .map((dt) => {
      const sub = won.filter((q) => q.type === dt);
      const r = sub.reduce((a, q) => a + q.rec, 0);
      const b = sub.reduce((a, q) => a + (q.contract - q.rec), 0);
      const gp = sub.reduce((a, q) => a + (q.rec - q.cogs), 0);
      const gm = r > 0 ? ((gp / r) * 100).toFixed(1) : "0.0";
      return `
        <div class="mix-card">
          <div class="mix-top">
            <span>${dt} (${sub.length} active contracts)</span>
            <span>GM: ${gm}%</span>
          </div>
          <div class="mix-sub">
            Recognized: ${fmtMillions(r)} &bull; Scheduled Backlog: ${fmtMillions(b)}
          </div>
        </div>`;
    })
    .join("");

  document.getElementById("vmiTableBody").innerHTML = currentInventoryRows
    .map(
      (r) => `
      <tr>
        <td><strong>${r.sku}</strong></td>
        <td>${r.name}</td>
        <td>${r.bu}</td>
        <td><strong>Class ${r.abc}</strong></td>
        <td class="num">${r.spend.toLocaleString()}</td>
        <td class="num">${r.onHand}</td>
        <td class="num">${r.rop}</td>
        <td class="num">${r.daysCover}d</td>
        <td><span class="badge ${r.status}">${r.status}</span></td>
      </tr>`
    )
    .join("");
}

document.getElementById("exportBtn").addEventListener("click", () => {
  const header = "sku,part_name,business_unit,abc_class,annual_spend_thb,on_hand,rop_95,days_cover,status\n";
  const body = currentInventoryRows
    .map((r) => `${r.sku},"${r.name}","${r.bu}",${r.abc},${r.spend},${r.onHand},${r.rop},${r.daysCover},${r.status}`)
    .join("\n");
  const blob = new Blob([header + body], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "vmi_reorder_analysis.csv";
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById("buFilter").addEventListener("change", renderDashboard);
document.getElementById("dealFilter").addEventListener("change", renderDashboard);
renderDashboard();
