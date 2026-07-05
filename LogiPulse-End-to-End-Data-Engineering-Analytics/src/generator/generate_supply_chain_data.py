"""
LogiPulse Global - Supply Chain & Logistics Data Generator
Generates realistic multi-entity enterprise datasets for testing ETL pipelines,
SQL Data Warehouses, and Power BI dashboards.
"""

import os
import json
import random
import csv
from datetime import datetime, timedelta

# Seed for reproducibility
random.seed(42)

DATA_DIR = "/home/user/data/raw"
os.makedirs(DATA_DIR, exist_ok=True)

# 1. Generate Carriers
carriers = [
    {"carrier_id": "CAR-001", "carrier_name": "FedEx Freight", "transport_mode": "Road/Air", "base_rate_per_kg": 2.45, "sla_target_pct": 96.5},
    {"carrier_id": "CAR-002", "carrier_name": "DHL Express", "transport_mode": "Air/Sea", "base_rate_per_kg": 3.10, "sla_target_pct": 98.0},
    {"carrier_id": "CAR-003", "carrier_name": "Maersk Line", "transport_mode": "Sea", "base_rate_per_kg": 0.85, "sla_target_pct": 92.0},
    {"carrier_id": "CAR-004", "carrier_name": "UPS Logistics", "transport_mode": "Road/Air", "base_rate_per_kg": 2.60, "sla_target_pct": 97.0},
    {"carrier_id": "CAR-005", "carrier_name": "XPO Logistics", "transport_mode": "Road", "base_rate_per_kg": 1.75, "sla_target_pct": 94.5},
    {"carrier_id": "CAR-006", "carrier_name": "DB Schenker", "transport_mode": "Rail/Road", "base_rate_per_kg": 1.50, "sla_target_pct": 93.5},
    {"carrier_id": "CAR-007", "carrier_name": "Kuehne + Nagel", "transport_mode": "Sea/Air", "base_rate_per_kg": 2.10, "sla_target_pct": 95.0},
    {"carrier_id": "CAR-008", "carrier_name": "C.H. Robinson", "transport_mode": "Road", "base_rate_per_kg": 1.85, "sla_target_pct": 94.0}
]

with open(f"{DATA_DIR}/carriers.csv", mode="w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=carriers[0].keys())
    writer.writeheader()
    writer.writerows(carriers)

# 2. Generate Warehouses
warehouses = [
    {"warehouse_id": "WH-SEA-01", "name": "Seattle Global Hub", "city": "Seattle", "country": "USA", "region": "North America", "capacity_sqft": 500000, "daily_op_cost_usd": 12500},
    {"warehouse_id": "WH-CHI-02", "name": "Chicago Midwest DC", "city": "Chicago", "country": "USA", "region": "North America", "capacity_sqft": 420000, "daily_op_cost_usd": 10800},
    {"warehouse_id": "WH-DAL-03", "name": "Dallas South DC", "city": "Dallas", "country": "USA", "region": "North America", "capacity_sqft": 380000, "daily_op_cost_usd": 9200},
    {"warehouse_id": "WH-ROT-04", "name": "Rotterdam Euro Hub", "city": "Rotterdam", "country": "Netherlands", "region": "Europe", "capacity_sqft": 600000, "daily_op_cost_usd": 15400},
    {"warehouse_id": "WH-FRA-05", "name": "Frankfurt Central DC", "city": "Frankfurt", "country": "Germany", "region": "Europe", "capacity_sqft": 450000, "daily_op_cost_usd": 13200},
    {"warehouse_id": "WH-LON-06", "name": "London UK Gateway", "city": "London", "country": "UK", "region": "Europe", "capacity_sqft": 350000, "daily_op_cost_usd": 14000},
    {"warehouse_id": "WH-SIN-07", "name": "Singapore APAC Hub", "city": "Singapore", "country": "Singapore", "region": "APAC", "capacity_sqft": 550000, "daily_op_cost_usd": 16000},
    {"warehouse_id": "WH-TYO-08", "name": "Tokyo East DC", "city": "Tokyo", "country": "Japan", "region": "APAC", "capacity_sqft": 400000, "daily_op_cost_usd": 14500},
    {"warehouse_id": "WH-SYD-09", "name": "Sydney ANZ Hub", "city": "Sydney", "country": "Australia", "region": "APAC", "capacity_sqft": 300000, "daily_op_cost_usd": 11000},
    {"warehouse_id": "WH-DXB-10", "name": "Dubai MEA Gateway", "city": "Dubai", "country": "UAE", "region": "MEA", "capacity_sqft": 480000, "daily_op_cost_usd": 11800}
]

with open(f"{DATA_DIR}/warehouses.csv", mode="w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=warehouses[0].keys())
    writer.writeheader()
    writer.writerows(warehouses)

# 3. Generate Suppliers
categories = ["Electronics Components", "Raw Packaging", "Precision Hydraulics", "Automotive Parts", "Industrial Sensors", "Chemical Additives"]
countries = ["China", "Taiwan", "Germany", "USA", "Mexico", "Vietnam", "India", "South Korea"]
suppliers = []
for i in range(1, 51):
    supp_id = f"SUP-{i:03d}"
    country = random.choice(countries)
    cat = random.choice(categories)
    suppliers.append({
        "supplier_id": supp_id,
        "supplier_name": f"{country} {cat.split()[0]} Enterprises Ltd #{i}",
        "category": cat,
        "country": country,
        "agreed_lead_days": random.randint(3, 14),
        "reliability_rating": round(random.uniform(3.8, 5.0), 2),
        "contract_sla_pct": random.choice([95.0, 96.0, 98.0, 99.0])
    })

with open(f"{DATA_DIR}/suppliers.csv", mode="w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=suppliers[0].keys())
    writer.writeheader()
    writer.writerows(suppliers)

# 4. Generate Shipments (5000 records spanning the last 180 days)
start_date = datetime(2026, 1, 1)
shipments = []
delay_reasons = ["Weather Disruption", "Customs Hold", "Carrier Breakdown", "Port Congestion", "Documentation Error", "None"]

for i in range(1, 5001):
    ship_id = f"SHP-2026-{i:05d}"
    wh = random.choice(warehouses)
    carrier = random.choice(carriers)
    supp = random.choice(suppliers)
    
    order_day_offset = random.randint(0, 180)
    order_dt = start_date + timedelta(days=order_day_offset, hours=random.randint(6, 20))
    
    # Promised transit days based on carrier mode
    if carrier["transport_mode"] == "Sea":
        promised_days = random.randint(18, 30)
    elif "Air" in carrier["transport_mode"]:
        promised_days = random.randint(2, 5)
    else:
        promised_days = random.randint(4, 10)
        
    promised_delivery_dt = order_dt + timedelta(days=promised_days)
    
    # Determine if on time or delayed (simulate ~15% delay rate)
    is_delayed = random.random() < 0.16
    if is_delayed:
        actual_days = promised_days + random.randint(1, 8)
        delay_reason = random.choice([r for r in delay_reasons if r != "None"])
    else:
        actual_days = max(1, promised_days - random.randint(0, 2))
        delay_reason = "None"
        
    actual_delivery_dt = order_dt + timedelta(days=actual_days)
    
    weight_kg = round(random.uniform(50.0, 4500.0), 2)
    freight_cost = round(weight_kg * carrier["base_rate_per_kg"] * random.uniform(0.9, 1.2), 2)
    quantity_units = random.randint(10, 500)
    is_damaged = random.random() < 0.024 # ~2.4% damage rate
    
    shipments.append({
        "shipment_id": ship_id,
        "order_id": f"ORD-{random.randint(10000, 99999)}",
        "supplier_id": supp["supplier_id"],
        "destination_warehouse_id": wh["warehouse_id"],
        "carrier_id": carrier["carrier_id"],
        "order_date": order_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "promised_delivery_date": promised_delivery_dt.strftime("%Y-%m-%d"),
        "actual_delivery_date": actual_delivery_dt.strftime("%Y-%m-%d"),
        "transit_days": actual_days,
        "promised_transit_days": promised_days,
        "on_time_flag": 0 if is_delayed else 1,
        "in_full_flag": 0 if is_damaged else 1,
        "weight_kg": weight_kg,
        "quantity_units": quantity_units,
        "freight_cost_usd": freight_cost,
        "damage_reported_flag": 1 if is_damaged else 0,
        "delay_reason": delay_reason,
        "shipment_status": "Delivered" if order_day_offset < 170 else random.choice(["In Transit", "Customs Processing", "Delivered"])
    })

with open(f"{DATA_DIR}/shipments.csv", mode="w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=shipments[0].keys())
    writer.writeheader()
    writer.writerows(shipments)

# 5. Generate Fleet Telematics IoT JSON data (2000 records)
vehicles = [f"TRK-{wh['warehouse_id'].split('-')[1]}-{i:02d}" for wh in warehouses[:5] for i in range(1, 11)]
telematics = []
for i in range(1, 2001):
    veh = random.choice(vehicles)
    dt = start_date + timedelta(days=random.randint(0, 180), hours=random.randint(0, 23))
    speed = round(random.uniform(0.0, 75.0), 1)
    fuel_l_100km = round(random.uniform(22.0, 38.0), 2) if speed > 5 else 0.0
    engine_temp_c = round(random.uniform(82.0, 104.0), 1)
    maintenance_alert = 1 if engine_temp_c > 100.0 or random.random() < 0.05 else 0
    
    telematics.append({
        "telematics_id": f"TLM-{i:06d}",
        "vehicle_id": veh,
        "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "speed_kmh": speed,
        "fuel_consumption_l_100km": fuel_l_100km,
        "engine_temp_celsius": engine_temp_c,
        "idle_minutes_today": random.randint(15, 120),
        "maintenance_alert_flag": maintenance_alert,
        "gps_latitude": round(random.uniform(30.0, 52.0), 6),
        "gps_longitude": round(random.uniform(-120.0, 20.0), 6)
    })

with open(f"{DATA_DIR}/fleet_telematics.json", mode="w") as f:
    json.dump(telematics, f, indent=2)

print(f"Data generation complete! Files generated in {DATA_DIR}:")
for fname in os.listdir(DATA_DIR):
    fpath = os.path.join(DATA_DIR, fname)
    size_kb = os.path.getsize(fpath) / 1024.0
    print(f"  - {fname}: {size_kb:.1f} KB")
