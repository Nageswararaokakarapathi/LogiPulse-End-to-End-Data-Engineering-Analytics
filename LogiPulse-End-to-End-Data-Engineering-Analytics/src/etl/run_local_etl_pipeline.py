"""
LogiPulse Global - Local Execution Engine for ETL Pipeline
Runs the exact Medallion transformations locally using Pandas & SQLite to populate
local data files and the local relational Data Warehouse simulation.
"""

import os
import json
import sqlite3
import pandas as pd
from datetime import datetime

RAW_DIR = "/home/user/data/raw"
PROCESSED_DIR = "/home/user/data/processed"
DB_PATH = f"{PROCESSED_DIR}/logipulse_warehouse.db"

os.makedirs(PROCESSED_DIR, exist_ok=True)

def run_pipeline():
    print("=== [LOCAL ETL ENGINE] Starting LogiPulse Pipeline Execution ===")
    
    # 1. Ingest Raw Data (Bronze)
    carriers_df = pd.read_csv(f"{RAW_DIR}/carriers.csv")
    warehouses_df = pd.read_csv(f"{RAW_DIR}/warehouses.csv")
    suppliers_df = pd.read_csv(f"{RAW_DIR}/suppliers.csv")
    shipments_df = pd.read_csv(f"{RAW_DIR}/shipments.csv")
    with open(f"{RAW_DIR}/fleet_telematics.json", "r") as f:
        telematics_data = json.load(f)
    telematics_df = pd.DataFrame(telematics_data)
    
    print(f"Ingested {len(shipments_df)} shipments, {len(telematics_df)} telematics records.")

    # 2. Transform Data (Silver Layer)
    shipments_df["transit_delay_days"] = shipments_df["transit_days"] - shipments_df["promised_transit_days"]
    shipments_df["otif_compliance_flag"] = ((shipments_df["on_time_flag"] == 1) & (shipments_df["in_full_flag"] == 1)).astype(int)
    shipments_df["freight_cost_per_kg"] = (shipments_df["freight_cost_usd"] / shipments_df["weight_kg"]).round(4)
    shipments_df["delivery_month"] = shipments_df["actual_delivery_date"].str[:7]
    
    carriers_df["carrier_tier"] = carriers_df["sla_target_pct"].apply(
        lambda x: "Tier-1 Premier" if x >= 97.0 else ("Tier-2 Standard" if x >= 94.0 else "Tier-3 Economy")
    )
    
    warehouses_df["cost_per_sqft"] = (warehouses_df["daily_op_cost_usd"] * 365 / warehouses_df["capacity_sqft"]).round(2)
    
    suppliers_df["risk_profile"] = suppliers_df["reliability_rating"].apply(
        lambda x: "Low Risk" if x >= 4.5 else ("Medium Risk" if x >= 4.0 else "High Risk")
    )

    # 3. Aggregate Data (Gold Layer)
    # Carrier Scorecard
    merged_ship_carrier = pd.merge(shipments_df, carriers_df, on="carrier_id")
    gold_carrier_scorecard = merged_ship_carrier.groupby(["carrier_id", "carrier_name", "transport_mode", "sla_target_pct"]).agg(
        total_shipments=("shipment_id", "count"),
        on_time_shipments=("on_time_flag", "sum"),
        in_full_shipments=("in_full_flag", "sum"),
        otif_shipments=("otif_compliance_flag", "sum"),
        avg_transit_days=("transit_days", "mean"),
        avg_delay_days=("transit_delay_days", "mean"),
        total_freight_spend_usd=("freight_cost_usd", "sum")
    ).reset_index()
    
    gold_carrier_scorecard["actual_on_time_pct"] = (gold_carrier_scorecard["on_time_shipments"] / gold_carrier_scorecard["total_shipments"] * 100).round(2)
    gold_carrier_scorecard["actual_otif_pct"] = (gold_carrier_scorecard["otif_shipments"] / gold_carrier_scorecard["total_shipments"] * 100).round(2)
    gold_carrier_scorecard["sla_breach_flag"] = (gold_carrier_scorecard["actual_on_time_pct"] < gold_carrier_scorecard["sla_target_pct"]).astype(int)
    gold_carrier_scorecard["avg_transit_days"] = gold_carrier_scorecard["avg_transit_days"].round(2)
    gold_carrier_scorecard["avg_delay_days"] = gold_carrier_scorecard["avg_delay_days"].round(2)
    gold_carrier_scorecard["total_freight_spend_usd"] = gold_carrier_scorecard["total_freight_spend_usd"].round(2)

    # Warehouse Monthly Summary
    merged_ship_wh = pd.merge(shipments_df, warehouses_df, left_on="destination_warehouse_id", right_on="warehouse_id")
    gold_warehouse_monthly = merged_ship_wh.groupby(["warehouse_id", "name", "region", "delivery_month"]).agg(
        monthly_inbound_shipments=("shipment_id", "count"),
        total_inbound_weight_kg=("weight_kg", "sum"),
        monthly_freight_cost_usd=("freight_cost_usd", "sum"),
        otif_count=("otif_compliance_flag", "sum")
    ).reset_index()
    gold_warehouse_monthly["monthly_otif_pct"] = (gold_warehouse_monthly["otif_count"] / gold_warehouse_monthly["monthly_inbound_shipments"] * 100).round(2)
    gold_warehouse_monthly.drop(columns=["otif_count"], inplace=True)

    # Supplier Reliability Summary
    merged_ship_supp = pd.merge(shipments_df, suppliers_df, on="supplier_id")
    gold_supplier_reliability = merged_ship_supp.groupby(["supplier_id", "supplier_name", "category", "country", "agreed_lead_days", "reliability_rating"]).agg(
        total_orders=("shipment_id", "count"),
        avg_actual_lead_days=("transit_days", "mean"),
        damaged_count=("damage_reported_flag", "sum"),
        otif_count=("otif_compliance_flag", "sum")
    ).reset_index()
    gold_supplier_reliability["avg_actual_lead_days"] = gold_supplier_reliability["avg_actual_lead_days"].round(2)
    gold_supplier_reliability["damage_rate_pct"] = (gold_supplier_reliability["damaged_count"] / gold_supplier_reliability["total_orders"] * 100).round(2)
    gold_supplier_reliability["supplier_otif_pct"] = (gold_supplier_reliability["otif_count"] / gold_supplier_reliability["total_orders"] * 100).round(2)
    gold_supplier_reliability.drop(columns=["damaged_count", "otif_count"], inplace=True)

    # Save processed CSVs
    gold_carrier_scorecard.to_csv(f"{PROCESSED_DIR}/gold_carrier_scorecard.csv", index=False)
    gold_warehouse_monthly.to_csv(f"{PROCESSED_DIR}/gold_warehouse_monthly.csv", index=False)
    gold_supplier_reliability.to_csv(f"{PROCESSED_DIR}/gold_supplier_reliability.csv", index=False)
    shipments_df.to_csv(f"{PROCESSED_DIR}/silver_shipments.csv", index=False)
    
    # Also save a JSON summary for our interactive HTML dashboard!
    dashboard_summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kpis": {
            "total_shipments": int(len(shipments_df)),
            "otif_rate_pct": float(round(shipments_df["otif_compliance_flag"].mean() * 100, 1)),
            "total_freight_spend_usd": float(round(shipments_df["freight_cost_usd"].sum() / 1e6, 2)), # in Millions
            "avg_transit_days": float(round(shipments_df["transit_days"].mean(), 1)),
            "damage_rate_pct": float(round(shipments_df["damage_reported_flag"].mean() * 100, 2)),
            "active_suppliers": int(len(suppliers_df)),
            "active_warehouses": int(len(warehouses_df))
        },
        "carrier_scorecard": gold_carrier_scorecard.to_dict(orient="records"),
        "warehouse_summary": gold_warehouse_monthly.to_dict(orient="records"),
        "supplier_summary": gold_supplier_reliability.sort_values(by="total_orders", ascending=False).head(15).to_dict(orient="records"),
        "delay_breakdown": shipments_df[shipments_df["delay_reason"] != "None"]["delay_reason"].value_counts().reset_index().rename(columns={"delay_reason": "reason"}).to_dict(orient="records")
    }
    
    with open(f"{PROCESSED_DIR}/dashboard_data.json", "w") as f:
        json.dump(dashboard_summary, f, indent=2)

    # 4. Load into Local Relational Data Warehouse Simulation (SQLite Star Schema)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    carriers_df.to_sql("dim_carrier", conn, if_exists="replace", index=False)
    warehouses_df.to_sql("dim_warehouse", conn, if_exists="replace", index=False)
    suppliers_df.to_sql("dim_supplier", conn, if_exists="replace", index=False)
    shipments_df.to_sql("fact_shipment_fulfillment", conn, if_exists="replace", index=False)
    telematics_df.to_sql("fact_fleet_telematics", conn, if_exists="replace", index=False)
    gold_carrier_scorecard.to_sql("gold_carrier_scorecard", conn, if_exists="replace", index=False)
    gold_warehouse_monthly.to_sql("gold_warehouse_monthly", conn, if_exists="replace", index=False)
    gold_supplier_reliability.to_sql("gold_supplier_reliability", conn, if_exists="replace", index=False)
    
    conn.commit()
    conn.close()
    
    print(f"Pipeline finished! Data Warehouse updated at {DB_PATH}")
    print(f"Dashboard summary written to {PROCESSED_DIR}/dashboard_data.json")

if __name__ == "__main__":
    run_pipeline()
