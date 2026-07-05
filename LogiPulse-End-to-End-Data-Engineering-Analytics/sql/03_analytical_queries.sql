-- ============================================================================
-- LogiPulse Global - Advanced Analytical SQL Queries
-- Designed for Power BI DirectQuery Views and Executive Reporting
-- ============================================================================

-- Query 1: Executive KPI Summary (YTD & Rolling 30-Day OTIF & Cost Analysis)
SELECT 
    COUNT(f.shipment_id) AS Total_Shipments,
    SUM(f.freight_cost_usd) AS Total_Freight_Spend_USD,
    ROUND(AVG(f.freight_cost_per_kg), 4) AS Avg_Freight_Cost_Per_Kg,
    ROUND((CAST(SUM(CAST(f.otif_compliance_flag AS INT)) AS FLOAT) / COUNT(f.shipment_id)) * 100.0, 2) AS OTIF_Compliance_Rate_Pct,
    ROUND((CAST(SUM(CAST(f.damage_reported_flag AS INT)) AS FLOAT) / COUNT(f.shipment_id)) * 100.0, 2) AS Damage_Rate_Pct,
    ROUND(AVG(CAST(f.transit_delay_days AS FLOAT)), 2) AS Avg_Transit_Delay_Days
FROM bi.fact_shipment_fulfillment f;

-- Query 2: Carrier Tier & SLA Scorecard Ranking with Window Functions
SELECT 
    c.carrier_id,
    c.carrier_name,
    c.transport_mode,
    c.carrier_tier,
    c.sla_target_pct,
    COUNT(f.shipment_id) AS Total_Shipments,
    ROUND((CAST(SUM(CAST(f.on_time_flag AS INT)) AS FLOAT) / COUNT(f.shipment_id)) * 100.0, 2) AS Actual_OnTime_Pct,
    ROUND((CAST(SUM(CAST(f.otif_compliance_flag AS INT)) AS FLOAT) / COUNT(f.shipment_id)) * 100.0, 2) AS Actual_OTIF_Pct,
    CASE 
        WHEN ROUND((CAST(SUM(CAST(f.on_time_flag AS INT)) AS FLOAT) / COUNT(f.shipment_id)) * 100.0, 2) < c.sla_target_pct 
        THEN 'BREACH' ELSE 'COMPLIANT' 
    END AS SLA_Status,
    RANK() OVER(PARTITION BY c.transport_mode ORDER BY ROUND((CAST(SUM(CAST(f.otif_compliance_flag AS INT)) AS FLOAT) / COUNT(f.shipment_id)) * 100.0, 2) DESC) AS Mode_Rank
FROM bi.fact_shipment_fulfillment f
JOIN bi.dim_carrier c ON f.carrier_id = c.carrier_id
GROUP BY c.carrier_id, c.carrier_name, c.transport_mode, c.carrier_tier, c.sla_target_pct
ORDER BY Actual_OTIF_Pct DESC;

-- Query 3: Warehouse Bottleneck & Freight Cost Efficiency Breakdown
SELECT 
    w.region,
    w.warehouse_id,
    w.name AS Warehouse_Name,
    COUNT(f.shipment_id) AS Inbound_Shipments,
    ROUND(SUM(f.weight_kg), 2) AS Total_Inbound_Weight_Kg,
    ROUND(SUM(f.freight_cost_usd), 2) AS Total_Freight_Spend_USD,
    ROUND((CAST(SUM(CAST(f.otif_compliance_flag AS INT)) AS FLOAT) / COUNT(f.shipment_id)) * 100.0, 2) AS Warehouse_OTIF_Pct,
    w.cost_per_sqft AS Facility_Cost_Per_SqFt
FROM bi.fact_shipment_fulfillment f
JOIN bi.dim_warehouse w ON f.destination_warehouse_id = w.warehouse_id
GROUP BY w.region, w.warehouse_id, w.name, w.cost_per_sqft
ORDER BY Total_Freight_Spend_USD DESC;

-- Query 4: Supplier Risk Evaluation Matrix (Top High-Risk Suppliers by Damage & Delay)
SELECT 
    s.supplier_id,
    s.supplier_name,
    s.country,
    s.category,
    s.risk_profile,
    COUNT(f.shipment_id) AS Order_Count,
    ROUND((CAST(SUM(CAST(f.damage_reported_flag AS INT)) AS FLOAT) / COUNT(f.shipment_id)) * 100.0, 2) AS Damage_Rate_Pct,
    ROUND(AVG(CAST(f.transit_delay_days AS FLOAT)), 2) AS Avg_Delay_Days
FROM bi.fact_shipment_fulfillment f
JOIN bi.dim_supplier s ON f.supplier_id = s.supplier_id
GROUP BY s.supplier_id, s.supplier_name, s.country, s.category, s.risk_profile
HAVING COUNT(f.shipment_id) >= 10
ORDER BY Damage_Rate_Pct DESC, Avg_Delay_Days DESC;
