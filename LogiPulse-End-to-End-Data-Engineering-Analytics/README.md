# LogiPulse Global - End-to-End Enterprise BI Platform

An enterprise-grade, hybrid cloud Business Intelligence & Analytics platform built for **LogiPulse Global** (Supply Chain & Fleet Logistics). This reference architecture demonstrates a complete, production-ready stack utilizing **Azure Data Factory (ADF)**, **Azure Databricks / PySpark Lakehouse**, **Azure Synapse / SQL Data Warehouse**, and **Power BI Interactive Dashboards**.

---

## 🏛️ End-to-End Reference Architecture

```
[ ERP / WMS / IoT Feeds ]
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Azure Data Factory (ADF) Master Orchestration Pipeline │
└────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ ADLS Gen2 Medallion Lakehouse (PySpark / Delta Lake)   │
│   ├── Bronze : Raw Ingestion & Schema Enforcing        │
│   ├── Silver : Data Cleansing, Enriched KPIs & Hashes  │
│   └── Gold    : Dimensional Aggregates & Scorecards     │
└────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Azure Synapse Analytics / Azure SQL Data Warehouse     │
│   └── Enterprise Star Schema (Fact & Dimension Tables) │
└────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Power BI Semantic Model & Live Interactive Dashboard   │
│   └── DAX Measures, RLS Security & Executive Views     │
└────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```text
/home/user/
├── README.md                                   # Master project documentation
├── app/
│   └── dashboard.html                          # Offline-compatible interactive web BI Dashboard previewable in workspace
├── azure/
│   └── adf/
│       └── pipeline_master_logistics_etl.json  # ARM / ADF JSON template defining copy, notebook & SP activities
├── data/
│   ├── raw/                                    # Synthetic raw CSV/JSON files (carriers, warehouses, shipments, IoT telematics)
│   └── processed/                              # Processed analytics outputs & local relational SQLite Data Warehouse
├── powerbi/
│   ├── dax_measures.dax                        # Complete production DAX formulas organized by subject area
│   └── model_documentation.md                  # Semantic star schema diagram, RLS definitions, and wireframes
├── sql/
│   ├── 01_create_star_schema.sql               # Complete DDL for Synapse Dedicated SQL Pool / Azure SQL Database
│   ├── 02_etl_stored_procedures.sql            # T-SQL MERGE & upsert stored procedures for pipeline automation
│   └── 03_analytical_queries.sql               # Advanced analytical queries for reporting & DirectQuery views
└── src/
    ├── etl/
    │   ├── pyspark_lakehouse_pipeline.py       # Enterprise PySpark script for Databricks / Synapse Medallion Lakehouse
    │   └── run_local_etl_pipeline.py           # Local execution engine running data pipelines with Pandas & SQLite
    └── generator/
        ├── generate_supply_chain_data.py       # Multi-entity enterprise logistics dataset generator
        └── build_interactive_dashboard.py      # Dashboard static HTML compiler embedding processed metrics
```

---

## 🚀 Quickstart & Execution Guide

### 1. Generate Synthetic Enterprise Data
Run the generator script to create realistic supply chain transactions, warehouse capacities, supplier SLAs, and delivery truck IoT telematics data:
```bash
python3 src/generator/generate_supply_chain_data.py
```

### 2. Execute Data Pipeline & Load Data Warehouse
Run the ETL engine to process raw data through the Bronze/Silver/Gold layers and populate the relational Star Schema Data Warehouse (`data/processed/logipulse_warehouse.db`):
```bash
python3 src/etl/run_local_etl_pipeline.py
```

### 3. Build & Preview Live Interactive Dashboard
Compile the interactive single-page HTML application and view it directly in your file viewer:
```bash
python3 src/generator/build_interactive_dashboard.py
```
Open **`app/dashboard.html`** in the viewer to interact with live executive scorecards, carrier SLA compliance rankings, and supplier risk matrices!

---

## 💡 Key Solution Highlights

1. **Enterprise Medallion Lakehouse (`src/etl/pyspark_lakehouse_pipeline.py`)**: Implements Delta Lake ACID compliance, surrogate key MD5 hashing, and automated SLA calculation.
2. **Robust T-SQL Warehousing (`sql/`)**: Star schema dimensions (`dim_carrier`, `dim_warehouse`, `dim_supplier`, `dim_date`) joined to granular transaction fact tables (`fact_shipment_fulfillment`, `fact_fleet_telematics`) with idempotent MERGE stored procedures.
3. **Automated ADF Orchestration (`azure/adf/`)**: Production ARM pipeline JSON linking REST copy sources to PySpark notebooks and SQL stored procedures with error notification hooks.
4. **Comprehensive Power BI DAX Suite (`powerbi/dax_measures.dax`)**: Includes OTIF Rate %, Avg Transit Delays, Freight Spend YoY Growth %, and active telematics monitoring measures.
