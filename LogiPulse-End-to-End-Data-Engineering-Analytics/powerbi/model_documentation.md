# LogiPulse Global - Power BI Semantic Model & Report Design Guide

## 1. Star Schema Relationship Diagram
The semantic model follows a strict enterprise Star Schema optimized for DirectQuery and Import mode performance in Power BI / Microsoft Fabric:

```
                  +-------------------+
                  |     dim_date      |
                  +-------------------+
                     1 |
                       | * (order_date / actual_delivery_date)
+----------------+     v     +---------------------------+     * +---------------+
|  dim_supplier  | 1 ------> | fact_shipment_fulfillment | <---- 1 |  dim_carrier  |
+----------------+           +---------------------------+       +---------------+
                                   * |
                                     | 1
                                     v
                             +---------------+
                             | dim_warehouse |
                             +---------------+
```

### Relationship Rules & Cardinality:
- **`dim_date[full_date]` 1 -> * `fact_shipment_fulfillment[actual_delivery_date]`** (Active Relationship)
- **`dim_date[full_date]` 1 -> * `fact_shipment_fulfillment[order_date]`** (Inactive Relationship — activated via `USERELATIONSHIP` for Order Intake analytics)
- **`dim_carrier[carrier_id]` 1 -> * `fact_shipment_fulfillment[carrier_id]`**
- **`dim_warehouse[warehouse_id]` 1 -> * `fact_shipment_fulfillment[destination_warehouse_id]`**
- **`dim_supplier[supplier_id]` 1 -> * `fact_shipment_fulfillment[supplier_id]`**

---

## 2. Row-Level Security (RLS) Roles
Enterprise security roles defined in Power BI Desktop / Fabric Service:

1. **Regional Warehouse Managers (`Role_Regional_Manager`)**:
   - Filter Expression on `dim_warehouse`: `[region] = USERPRINCIPALNAME()_Region` or static region lookup table.
2. **Supplier Relationship Managers (`Role_SRM`)**:
   - Filter Expression on `dim_supplier`: `[category] = LookupCategory(USERPRINCIPALNAME())`.

---

## 3. Power BI Report Page Layout & Wireframe

### Page 1: Executive Control Tower (Overview)
- **Top Header KPIs**: Total Shipments, OTIF Rate % (with Sparkline), Total Freight Spend ($M), Active Maintenance Alerts.
- **Center Visual (Combo Chart)**: Monthly Shipment Volume (Columns) vs. OTIF Rate % Trend (Line) overlaying Target SLA Line (95%).
- **Bottom Left Table**: Top 5 Logistics Carriers Scorecard (Carrier Name, Volume, OTIF Rate %, SLA Status indicator icon).
- **Bottom Right Matrix**: Regional Warehouse Fulfillment Performance (Inbound Weight, Freight Cost, OTIF %).

### Page 2: Carrier SLA & Freight Cost Deep-Dive
- **Scatter Plot**: Freight Cost per KG (X-axis) vs. OTIF Rate % (Y-axis) sized by Total Shipments. Identifies high-cost / low-reliability carriers.
- **Waterfall Chart**: Freight Spend Variance breakdown by Transport Mode (Sea, Air, Road, Rail).
- **Slicer Panel**: Filter by Carrier Tier, Transport Mode, and Date Range.

### Page 3: Supplier Reliability & Risk Matrix
- **Decomposition Tree**: Total Delay Days decomposed by Country -> Supplier Category -> Supplier Name -> Delay Reason.
- **Bar Chart**: Top 10 High-Risk Suppliers by Damage Rate %.
