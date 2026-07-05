"""
LogiPulse Global - Azure PySpark Lakehouse ETL Pipeline
Medallion Architecture Implementation (Bronze -> Silver -> Gold)
Target Execution Environment: Azure Databricks / Azure Synapse Spark Pool / Microsoft Fabric Notebooks

Author: BI & Data Engineering Team
Date: 2026-07-05
"""

import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, to_date, to_timestamp, datediff, when, round as spark_round,
    avg, sum as spark_sum, count, countDistinct, expr, lit, current_timestamp,
    date_trunc, concat_ws, md5
)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

def init_spark_session(app_name="LogiPulse_Lakehouse_ETL"):
    """Initialize Spark Session with Delta Lake & Azure ADLS Gen2 configurations."""
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.databricks.delta.schema.autoMerge.enabled", "true") \
        .getOrCreate()
    return spark

def ingest_bronze_layer(spark, adls_bronze_path, adls_raw_path):
    """
    Ingest raw CSV/JSON files from ADLS Gen2 raw container into Bronze Delta tables.
    Preserves raw payload and attaches metadata (ingestion timestamp, source filename).
    """
    print("=== [STAGE 1] Ingesting Bronze Layer ===")
    
    # 1. Ingest Carriers
    df_carriers = spark.read.option("header", "true").option("inferSchema", "true") \
        .csv(f"{adls_raw_path}/carriers.csv") \
        .withColumn("_ingested_at", current_timestamp()) \
        .withColumn("_source_system", lit("LogiPulse_ERP"))
    df_carriers.write.format("delta").mode("overwrite").save(f"{adls_bronze_path}/carriers")
    
    # 2. Ingest Warehouses
    df_warehouses = spark.read.option("header", "true").option("inferSchema", "true") \
        .csv(f"{adls_raw_path}/warehouses.csv") \
        .withColumn("_ingested_at", current_timestamp()) \
        .withColumn("_source_system", lit("LogiPulse_WMS"))
    df_warehouses.write.format("delta").mode("overwrite").save(f"{adls_bronze_path}/warehouses")
    
    # 3. Ingest Suppliers
    df_suppliers = spark.read.option("header", "true").option("inferSchema", "true") \
        .csv(f"{adls_raw_path}/suppliers.csv") \
        .withColumn("_ingested_at", current_timestamp()) \
        .withColumn("_source_system", lit("LogiPulse_SRM"))
    df_suppliers.write.format("delta").mode("overwrite").save(f"{adls_bronze_path}/suppliers")
    
    # 4. Ingest Shipments
    df_shipments = spark.read.option("header", "true").option("inferSchema", "true") \
        .csv(f"{adls_raw_path}/shipments.csv") \
        .withColumn("_ingested_at", current_timestamp()) \
        .withColumn("_source_system", lit("LogiPulse_TMS"))
    df_shipments.write.format("delta").mode("overwrite").save(f"{adls_bronze_path}/shipments")
    
    # 5. Ingest Telematics
    df_telematics = spark.read.option("multiline", "true") \
        .json(f"{adls_raw_path}/fleet_telematics.json") \
        .withColumn("_ingested_at", current_timestamp()) \
        .withColumn("_source_system", lit("LogiPulse_IoT_Hub"))
    df_telematics.write.format("delta").mode("overwrite").save(f"{adls_bronze_path}/fleet_telematics")
    
    print("Bronze layer ingestion completed successfully.")

def process_silver_layer(spark, adls_bronze_path, adls_silver_path):
    """
    Clean, validate, and enrich data from Bronze to Silver Delta tables.
    Calculates derived metrics: transit delay variance, OTIF compliance, surrogate keys.
    """
    print("=== [STAGE 2] Processing Silver Layer ===")
    
    # Read Bronze tables
    bronze_shipments = spark.read.format("delta").load(f"{adls_bronze_path}/shipments")
    bronze_carriers = spark.read.format("delta").load(f"{adls_bronze_path}/carriers")
    bronze_warehouses = spark.read.format("delta").load(f"{adls_bronze_path}/warehouses")
    bronze_suppliers = spark.read.format("delta").load(f"{adls_bronze_path}/suppliers")
    
    # 1. Clean & Enrich Shipments (Enforce data types, calculate lead time variance)
    silver_shipments = bronze_shipments \
        .filter(col("shipment_id").isNotNull() & col("order_id").isNotNull()) \
        .withColumn("order_date_dt", to_timestamp(col("order_date"))) \
        .withColumn("promised_delivery_dt", to_date(col("promised_delivery_date"))) \
        .withColumn("actual_delivery_dt", to_date(col("actual_delivery_date"))) \
        .withColumn("transit_delay_days", col("transit_days") - col("promised_transit_days")) \
        .withColumn("otif_compliance_flag", when((col("on_time_flag") == 1) & (col("in_full_flag") == 1), 1).otherwise(0)) \
        .withColumn("freight_cost_per_kg", spark_round(col("freight_cost_usd") / col("weight_kg"), 4)) \
        .withColumn("shipment_hash_key", md5(concat_ws("||", col("shipment_id"), col("order_date"))))
        
    silver_shipments.write.format("delta").mode("overwrite").save(f"{adls_silver_path}/shipments")
    
    # 2. Clean & Enrich Carriers
    silver_carriers = bronze_carriers \
        .withColumn("carrier_tier", when(col("sla_target_pct") >= 97.0, lit("Tier-1 Premier"))
                                    .when(col("sla_target_pct") >= 94.0, lit("Tier-2 Standard"))
                                    .otherwise(lit("Tier-3 Economy")))
    silver_carriers.write.format("delta").mode("overwrite").save(f"{adls_silver_path}/carriers")
    
    # 3. Clean & Enrich Warehouses
    silver_warehouses = bronze_warehouses \
        .withColumn("cost_per_sqft", spark_round(col("daily_op_cost_usd") * 365 / col("capacity_sqft"), 2))
    silver_warehouses.write.format("delta").mode("overwrite").save(f"{adls_silver_path}/warehouses")
    
    # 4. Clean & Enrich Suppliers
    silver_suppliers = bronze_suppliers \
        .withColumn("risk_profile", when(col("reliability_rating") >= 4.5, lit("Low Risk"))
                                    .when(col("reliability_rating") >= 4.0, lit("Medium Risk"))
                                    .otherwise(lit("High Risk")))
    silver_suppliers.write.format("delta").mode("overwrite").save(f"{adls_silver_path}/suppliers")
    
    print("Silver layer transformations completed successfully.")

def build_gold_layer(spark, adls_silver_path, adls_gold_path):
    """
    Build Star Schema aggregated analytics tables ready for Azure Synapse / SQL Data Warehouse loading.
    """
    print("=== [STAGE 3] Building Gold Dimensional & Summary Tables ===")
    
    shipments = spark.read.format("delta").load(f"{adls_silver_path}/shipments")
    carriers = spark.read.format("delta").load(f"{adls_silver_path}/carriers")
    warehouses = spark.read.format("delta").load(f"{adls_silver_path}/warehouses")
    suppliers = spark.read.format("delta").load(f"{adls_silver_path}/suppliers")
    
    # 1. Gold Summary: Carrier Performance SLA Scorecard
    gold_carrier_scorecard = shipments.join(carriers, "carrier_id", "inner") \
        .groupBy("carrier_id", "carrier_name", "transport_mode", "sla_target_pct") \
        .agg(
            count("shipment_id").alias("total_shipments"),
            spark_sum("on_time_flag").alias("on_time_shipments"),
            spark_sum("in_full_flag").alias("in_full_shipments"),
            spark_sum("otif_compliance_flag").alias("otif_shipments"),
            spark_round(avg("transit_days"), 2).alias("avg_transit_days"),
            spark_round(avg("transit_delay_days"), 2).alias("avg_delay_days"),
            spark_round(spark_sum("freight_cost_usd"), 2).alias("total_freight_spend_usd"),
            spark_round((spark_sum("on_time_flag") / count("shipment_id")) * 100, 2).alias("actual_on_time_pct"),
            spark_round((spark_sum("otif_compliance_flag") / count("shipment_id")) * 100, 2).alias("actual_otif_pct")
        ) \
        .withColumn("sla_breach_flag", when(col("actual_on_time_pct") < col("sla_target_pct"), 1).otherwise(0))
        
    gold_carrier_scorecard.write.format("delta").mode("overwrite").save(f"{adls_gold_path}/gold_carrier_scorecard")
    
    # 2. Gold Summary: Daily Warehouse Operations & Fulfillment Performance
    gold_warehouse_daily = shipments.join(warehouses, shipments.destination_warehouse_id == warehouses.warehouse_id, "inner") \
        .withColumn("delivery_month", date_trunc("month", col("actual_delivery_dt"))) \
        .groupBy("destination_warehouse_id", "name", "region", "delivery_month") \
        .agg(
            count("shipment_id").alias("monthly_inbound_shipments"),
            spark_round(spark_sum("weight_kg"), 2).alias("total_inbound_weight_kg"),
            spark_round(spark_sum("freight_cost_usd"), 2).alias("monthly_freight_cost_usd"),
            spark_round((spark_sum("otif_compliance_flag") / count("shipment_id")) * 100, 2).alias("monthly_otif_pct")
        )
    gold_warehouse_daily.write.format("delta").mode("overwrite").save(f"{adls_gold_path}/gold_warehouse_monthly_ops")
    
    # 3. Gold Summary: Supplier Risk & Reliability Index
    gold_supplier_reliability = shipments.join(suppliers, "supplier_id", "inner") \
        .groupBy("supplier_id", "supplier_name", "category", "country", "agreed_lead_days", "reliability_rating") \
        .agg(
            count("shipment_id").alias("total_orders"),
            spark_round(avg("transit_days"), 2).alias("avg_actual_lead_days"),
            spark_round(spark_sum("damage_reported_flag") / count("shipment_id") * 100, 2).alias("damage_rate_pct"),
            spark_round((spark_sum("otif_compliance_flag") / count("shipment_id")) * 100, 2).alias("supplier_otif_pct")
        )
    gold_supplier_reliability.write.format("delta").mode("overwrite").save(f"{adls_gold_path}/gold_supplier_reliability")
    
    print("Gold layer summary tables built successfully.")

if __name__ == "__main__":
    # In production Azure Databricks / Synapse, paths point to abfss:// containers
    ADLS_RAW = "abfss://raw@logipulselake.dfs.core.windows.net"
    ADLS_BRONZE = "abfss://bronze@logipulselake.dfs.core.windows.net"
    ADLS_SILVER = "abfss://silver@logipulselake.dfs.core.windows.net"
    ADLS_GOLD = "abfss://gold@logipulselake.dfs.core.windows.net"
    
    spark = init_spark_session()
    ingest_bronze_layer(spark, ADLS_BRONZE, ADLS_RAW)
    process_silver_layer(spark, ADLS_BRONZE, ADLS_SILVER)
    build_gold_layer(spark, ADLS_SILVER, ADLS_GOLD)
