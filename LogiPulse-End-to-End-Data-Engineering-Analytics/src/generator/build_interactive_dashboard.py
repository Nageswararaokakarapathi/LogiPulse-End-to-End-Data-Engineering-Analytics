"""
LogiPulse Global - Interactive Dashboard HTML Builder
Generates a self-contained, offline-compatible interactive HTML BI Dashboard
embedding processed data directly inside the HTML file so it renders perfectly
in sandboxed iframes without requiring external CDNs.
"""

import json
import os

JSON_PATH = "/home/user/data/processed/dashboard_data.json"
HTML_PATH = "/home/user/app/dashboard.html"

os.makedirs("/home/user/app", exist_ok=True)

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# Extract summary metrics
kpis = data["kpis"]
carriers = data["carrier_scorecard"]
warehouses = data["warehouse_summary"]
suppliers = data["supplier_summary"]
delays = data["delay_breakdown"]

# Sort carriers by volume
carriers.sort(key=lambda x: x["total_shipments"], reverse=True)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LogiPulse Global - Supply Chain & Fleet BI Platform</title>
<style>
  :root {{
    --bg-main: #0f172a;
    --bg-card: #1e293b;
    --bg-hover: #334155;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --primary: #3b82f6;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --border: #334155;
  }}
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  }}
  body {{
    background-color: var(--bg-main);
    color: var(--text-main);
    padding: 24px;
  }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding-bottom: 16px;
    margin-bottom: 24px;
  }}
  .header h1 {{
    font-size: 24px;
    color: var(--text-main);
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .header .badge {{
    background: #1d4ed8;
    color: white;
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 600;
  }}
  .header .meta {{
    font-size: 13px;
    color: var(--text-muted);
  }}
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }}
  .kpi-card {{
    background-color: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .kpi-label {{
    font-size: 13px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
  }}
  .kpi-value {{
    font-size: 28px;
    font-weight: 700;
    color: var(--text-main);
  }}
  .kpi-sub {{
    font-size: 12px;
    color: var(--success);
    margin-top: 6px;
  }}
  .tabs {{
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 12px;
  }}
  .tab-btn {{
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-muted);
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s;
  }}
  .tab-btn.active, .tab-btn:hover {{
    background: var(--primary);
    color: white;
    border-color: var(--primary);
  }}
  .tab-pane {{
    display: none;
  }}
  .tab-pane.active {{
    display: block;
  }}
  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 24px;
  }}
  @media (max-width: 900px) {{
    .grid-2 {{ grid-template-columns: 1fr; }}
  }}
  .card {{
    background-color: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
  }}
  .card-title {{
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--text-main);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }}
  th, td {{
    padding: 12px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }}
  th {{
    color: var(--text-muted);
    font-weight: 600;
    background-color: rgba(255,255,255,0.02);
  }}
  tr:hover {{
    background-color: var(--bg-hover);
  }}
  .status-badge {{
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
  }}
  .status-compliant {{ background-color: rgba(16, 185, 129, 0.2); color: #34d399; }}
  .status-breach {{ background-color: rgba(239, 68, 68, 0.2); color: #f87171; }}
  .bar-container {{
    width: 100%;
    background: var(--border);
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    margin-top: 6px;
  }}
  .bar-fill {{
    height: 100%;
    border-radius: 4px;
  }}
  .flex-row {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }}
</style>
</head>
<body>

  <div class="header">
    <div>
      <h1>LogiPulse Global <span class="badge">Enterprise Lakehouse BI</span></h1>
      <div class="meta">Hybrid Architecture: ADF + PySpark Lakehouse + Azure Synapse Star Schema + Power BI</div>
    </div>
    <div class="meta">Data Generated: {data['generated_at']}</div>
  </div>

  <!-- Executive KPIs -->
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">Total Shipments (180d)</div>
      <div class="kpi-value">{kpis['total_shipments']:,}</div>
      <div class="kpi-sub">Across 12 Global Warehouses</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">OTIF Compliance Rate</div>
      <div class="kpi-value" style="color: {'var(--success)' if kpis['otif_rate_pct'] >= 80 else 'var(--warning)'}">{kpis['otif_rate_pct']}%</div>
      <div class="kpi-sub">On-Time In-Full Target: 85%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Total Freight Spend</div>
      <div class="kpi-value">${kpis['total_freight_spend_usd']}M</div>
      <div class="kpi-sub">Avg Transit: {kpis['avg_transit_days']} Days</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Active Suppliers</div>
      <div class="kpi-value">{kpis['active_suppliers']}</div>
      <div class="kpi-sub">Damage Rate: {kpis['damage_rate_pct']}%</div>
    </div>
  </div>

  <!-- Navigation Tabs -->
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('overview')">📊 Executive Control Tower</button>
    <button class="tab-btn" onclick="switchTab('carriers')">🚚 Carrier SLA Scorecard</button>
    <button class="tab-btn" onclick="switchTab('warehouses')">🏢 Global Warehouses</button>
    <button class="tab-btn" onclick="switchTab('suppliers')">🏭 Supplier Risk Matrix</button>
  </div>

  <!-- TAB 1: OVERVIEW -->
  <div id="tab-overview" class="tab-pane active">
    <div class="grid-2">
      <div class="card">
        <div class="card-title">Top Carrier Volume & OTIF Share</div>
        <div id="carrier-chart-bars">
"""

# Add interactive custom bars for carriers
for c in carriers[:6]:
    otif = c["actual_otif_pct"]
    color = "#10b981" if otif >= c["sla_target_pct"] else "#ef4444"
    html_content += f"""
          <div style="margin-bottom: 14px;">
            <div class="flex-row">
              <span><strong>{c['carrier_name']}</strong> ({c['transport_mode']})</span>
              <span>OTIF: <strong style="color:{color}">{otif}%</strong> | Vol: {c['total_shipments']:,}</span>
            </div>
            <div class="bar-container">
              <div class="bar-fill" style="width: {otif}%; background-color: {color};"></div>
            </div>
          </div>
"""

html_content += """
        </div>
      </div>
      <div class="card">
        <div class="card-title">Primary Shipment Delay Root Causes</div>
        <div id="delay-breakdown">
"""

max_delay = max([d["count"] for d in delays]) if delays else 1
for d in delays:
    pct = round((d["count"] / max_delay) * 100)
    html_content += f"""
          <div style="margin-bottom: 14px;">
            <div class="flex-row">
              <span>{d['reason']}</span>
              <strong>{d['count']:,} incidents</strong>
            </div>
            <div class="bar-container">
              <div class="bar-fill" style="width: {pct}%; background-color: #f59e0b;"></div>
            </div>
          </div>
"""

html_content += """
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 2: CARRIERS -->
  <div id="tab-carriers" class="tab-pane">
    <div class="card">
      <div class="card-title">Logistics Carrier SLA Performance Matrix</div>
      <table>
        <thead>
          <tr>
            <th>Carrier ID</th>
            <th>Carrier Name</th>
            <th>Mode</th>
            <th>SLA Target</th>
            <th>Actual On-Time %</th>
            <th>Actual OTIF %</th>
            <th>Total Spend (USD)</th>
            <th>SLA Compliance</th>
          </tr>
        </thead>
        <tbody>
"""

for c in carriers:
    status_class = "status-breach" if c["sla_breach_flag"] == 1 else "status-compliant"
    status_text = "🚨 SLA Breach" if c["sla_breach_flag"] == 1 else "✅ Compliant"
    html_content += f"""
          <tr>
            <td><code>{c['carrier_id']}</code></td>
            <td><strong>{c['carrier_name']}</strong></td>
            <td>{c['transport_mode']}</td>
            <td>{c['sla_target_pct']}%</td>
            <td>{c['actual_on_time_pct']}%</td>
            <td><strong>{c['actual_otif_pct']}%</strong></td>
            <td>${c['total_freight_spend_usd']:,.2f}</td>
            <td><span class="status-badge {status_class}">{status_text}</span></td>
          </tr>
"""

html_content += """
        </tbody>
      </table>
    </div>
  </div>

  <!-- TAB 3: WAREHOUSES -->
  <div id="tab-warehouses" class="tab-pane">
    <div class="card">
      <div class="card-title">Global Warehouse Operations & Fulfillment Summary</div>
      <table>
        <thead>
          <tr>
            <th>Warehouse ID</th>
            <th>Facility Name</th>
            <th>Region</th>
            <th>Month</th>
            <th>Inbound Volume</th>
            <th>Total Weight (KG)</th>
            <th>Monthly Freight Spend</th>
            <th>OTIF %</th>
          </tr>
        </thead>
        <tbody>
"""

for w in warehouses[:15]:
    otif_w = w["monthly_otif_pct"]
    color_w = "#34d399" if otif_w >= 80 else "#f87171"
    html_content += f"""
          <tr>
            <td><code>{w['warehouse_id']}</code></td>
            <td><strong>{w['name']}</strong></td>
            <td>{w['region']}</td>
            <td>{w['delivery_month']}</td>
            <td>{w['monthly_inbound_shipments']:,}</td>
            <td>{w['total_inbound_weight_kg']:,.1f}</td>
            <td>${w['monthly_freight_cost_usd']:,.2f}</td>
            <td style="color:{color_w}; font-weight:bold;">{otif_w}%</td>
          </tr>
"""

html_content += """
        </tbody>
      </table>
    </div>
  </div>

  <!-- TAB 4: SUPPLIERS -->
  <div id="tab-suppliers" class="tab-pane">
    <div class="card">
      <div class="card-title">Supplier Risk & Reliability Scorecard (Top 15 Active Suppliers)</div>
      <table>
        <thead>
          <tr>
            <th>Supplier ID</th>
            <th>Supplier Name</th>
            <th>Country</th>
            <th>Category</th>
            <th>Orders</th>
            <th>Avg Actual Lead (Days)</th>
            <th>Damage Rate %</th>
            <th>Supplier OTIF %</th>
          </tr>
        </thead>
        <tbody>
"""

for s in suppliers:
    dmg = s["damage_rate_pct"]
    dmg_color = "#f87171" if dmg > 3.0 else "#34d399"
    html_content += f"""
          <tr>
            <td><code>{s['supplier_id']}</code></td>
            <td><strong>{s['supplier_name']}</strong></td>
            <td>{s['country']}</td>
            <td>{s['category']}</td>
            <td>{s['total_orders']}</td>
            <td>{s['avg_actual_lead_days']}</td>
            <td style="color:{dmg_color}; font-weight:bold;">{dmg}%</td>
            <td>{s['supplier_otif_pct']}%</td>
          </tr>
"""

html_content += """
        </tbody>
      </table>
    </div>
  </div>

<script>
  function switchTab(tabId) {
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById('tab-' + tabId).classList.add('active');
    event.target.classList.add('active');
  }
</script>
</body>
</html>
"""

with open(HTML_PATH, "w") as f:
    f.write(html_content)

print(f"Interactive Dashboard HTML successfully generated at {HTML_PATH}")
