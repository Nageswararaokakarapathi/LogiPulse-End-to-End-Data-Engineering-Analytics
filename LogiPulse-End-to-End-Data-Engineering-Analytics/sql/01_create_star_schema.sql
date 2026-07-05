-- ============================================================================
-- LogiPulse Global - Azure Synapse Analytics / Azure SQL Data Warehouse DDL
-- Star Schema Definition (Dimensions, Facts, and Aggregation Scorecards)
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'bi')
BEGIN
    EXEC('CREATE SCHEMA bi')
END;
GO

-- 1. Dimension: Carriers
IF OBJECT_ID('bi.dim_carrier', 'U') IS NOT NULL DROP TABLE bi.dim_carrier;
CREATE TABLE bi.dim_carrier (
    carrier_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    carrier_id NVARCHAR(50) NOT NULL UNIQUE,
    carrier_name NVARCHAR(100) NOT NULL,
    transport_mode NVARCHAR(50) NOT NULL,
    base_rate_per_kg DECIMAL(10,4) NOT NULL,
    sla_target_pct DECIMAL(5,2) NOT NULL,
    carrier_tier NVARCHAR(50) NOT NULL,
    effective_start_date DATETIME2 DEFAULT CURRENT_TIMESTAMP,
    is_active BIT DEFAULT 1
);

-- 2. Dimension: Warehouses
IF OBJECT_ID('bi.dim_warehouse', 'U') IS NOT NULL DROP TABLE bi.dim_warehouse;
CREATE TABLE bi.dim_warehouse (
    warehouse_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    warehouse_id NVARCHAR(50) NOT NULL UNIQUE,
    name NVARCHAR(100) NOT NULL,
    city NVARCHAR(100) NOT NULL,
    country NVARCHAR(100) NOT NULL,
    region NVARCHAR(50) NOT NULL,
    capacity_sqft BIGINT NOT NULL,
    daily_op_cost_usd DECIMAL(12,2) NOT NULL,
    cost_per_sqft DECIMAL(10,2) NOT NULL
);

-- 3. Dimension: Suppliers
IF OBJECT_ID('bi.dim_supplier', 'U') IS NOT NULL DROP TABLE bi.dim_supplier;
CREATE TABLE bi.dim_supplier (
    supplier_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    supplier_id NVARCHAR(50) NOT NULL UNIQUE,
    supplier_name NVARCHAR(150) NOT NULL,
    category NVARCHAR(100) NOT NULL,
    country NVARCHAR(100) NOT NULL,
    agreed_lead_days INT NOT NULL,
    reliability_rating DECIMAL(4,2) NOT NULL,
    contract_sla_pct DECIMAL(5,2) NOT NULL,
    risk_profile NVARCHAR(50) NOT NULL
);

-- 4. Dimension: Date Calendar
IF OBJECT_ID('bi.dim_date', 'U') IS NOT NULL DROP TABLE bi.dim_date;
CREATE TABLE bi.dim_date (
    date_key INT NOT NULL PRIMARY KEY, -- YYYYMMDD format
    full_date DATE NOT NULL UNIQUE,
    day_of_week INT NOT NULL,
    day_name NVARCHAR(20) NOT NULL,
    month_num INT NOT NULL,
    month_name NVARCHAR(20) NOT NULL,
    quarter_num INT NOT NULL,
    year_num INT NOT NULL,
    is_weekend BIT NOT NULL
);

-- 5. Fact Table: Shipment Fulfillment (Granular Transaction Level)
IF OBJECT_ID('bi.fact_shipment_fulfillment', 'U') IS NOT NULL DROP TABLE bi.fact_shipment_fulfillment;
CREATE TABLE bi.fact_shipment_fulfillment (
    shipment_key BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    shipment_id NVARCHAR(50) NOT NULL,
    order_id NVARCHAR(50) NOT NULL,
    supplier_id NVARCHAR(50) NOT NULL,
    destination_warehouse_id NVARCHAR(50) NOT NULL,
    carrier_id NVARCHAR(50) NOT NULL,
    order_date DATETIME2 NOT NULL,
    promised_delivery_date DATE NOT NULL,
    actual_delivery_date DATE NOT NULL,
    transit_days INT NOT NULL,
    promised_transit_days INT NOT NULL,
    transit_delay_days INT NOT NULL,
    on_time_flag BIT NOT NULL,
    in_full_flag BIT NOT NULL,
    otif_compliance_flag BIT NOT NULL,
    weight_kg DECIMAL(10,2) NOT NULL,
    quantity_units INT NOT NULL,
    freight_cost_usd DECIMAL(12,2) NOT NULL,
    freight_cost_per_kg DECIMAL(10,4) NOT NULL,
    damage_reported_flag BIT NOT NULL,
    delay_reason NVARCHAR(100) NULL,
    shipment_status NVARCHAR(50) NOT NULL,
    loaded_at DATETIME2 DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for Query Performance
CREATE NONCLUSTERED INDEX IX_FactShipment_Carrier ON bi.fact_shipment_fulfillment(carrier_id);
CREATE NONCLUSTERED INDEX IX_FactShipment_Warehouse ON bi.fact_shipment_fulfillment(destination_warehouse_id);
CREATE NONCLUSTERED INDEX IX_FactShipment_Supplier ON bi.fact_shipment_fulfillment(supplier_id);
CREATE NONCLUSTERED INDEX IX_FactShipment_DeliveryDate ON bi.fact_shipment_fulfillment(actual_delivery_date);

-- 6. Aggregation Table: Gold Carrier Scorecard
IF OBJECT_ID('bi.agg_carrier_scorecard', 'U') IS NOT NULL DROP TABLE bi.agg_carrier_scorecard;
CREATE TABLE bi.agg_carrier_scorecard (
    carrier_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    carrier_name NVARCHAR(100) NOT NULL,
    transport_mode NVARCHAR(50) NOT NULL,
    sla_target_pct DECIMAL(5,2) NOT NULL,
    total_shipments INT NOT NULL,
    on_time_shipments INT NOT NULL,
    in_full_shipments INT NOT NULL,
    otif_shipments INT NOT NULL,
    avg_transit_days DECIMAL(6,2) NOT NULL,
    avg_delay_days DECIMAL(6,2) NOT NULL,
    total_freight_spend_usd DECIMAL(14,2) NOT NULL,
    actual_on_time_pct DECIMAL(5,2) NOT NULL,
    actual_otif_pct DECIMAL(5,2) NOT NULL,
    sla_breach_flag BIT NOT NULL,
    updated_at DATETIME2 DEFAULT CURRENT_TIMESTAMP
);
