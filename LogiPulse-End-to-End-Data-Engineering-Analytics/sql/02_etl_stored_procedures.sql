-- ============================================================================
-- LogiPulse Global - T-SQL ETL Stored Procedures
-- Orchestrated by Azure Data Factory (ADF) Stored Procedure Activity
-- ============================================================================

CREATE OR ALTER PROCEDURE bi.usp_LoadDimCarrier
AS
BEGIN
    SET NOCOUNT ON;
    
    PRINT 'Upserting bi.dim_carrier from Silver staging table...';
    
    MERGE INTO bi.dim_carrier AS target
    USING (
        SELECT DISTINCT carrier_id, carrier_name, transport_mode, base_rate_per_kg, sla_target_pct, carrier_tier
        FROM stg.silver_carriers
    ) AS source
    ON target.carrier_id = source.carrier_id
    WHEN MATCHED THEN
        UPDATE SET 
            target.carrier_name = source.carrier_name,
            target.transport_mode = source.transport_mode,
            target.base_rate_per_kg = source.base_rate_per_kg,
            target.sla_target_pct = source.sla_target_pct,
            target.carrier_tier = source.carrier_tier
    WHEN NOT MATCHED THEN
        INSERT (carrier_id, carrier_name, transport_mode, base_rate_per_kg, sla_target_pct, carrier_tier)
        VALUES (source.carrier_id, source.carrier_name, source.transport_mode, source.base_rate_per_kg, source.sla_target_pct, source.carrier_tier);
        
    PRINT 'bi.dim_carrier load completed successfully.';
END;
GO

CREATE OR ALTER PROCEDURE bi.usp_LoadFactShipments
    @BatchDate DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @BatchDate IS NULL
        SET @BatchDate = CAST(CURRENT_TIMESTAMP AS DATE);
        
    PRINT 'Loading bi.fact_shipment_fulfillment for batch date: ' + CAST(@BatchDate AS VARCHAR(10));
    
    -- Truncate staging matches or perform idempotent delete/insert for the batch
    DELETE FROM bi.fact_shipment_fulfillment
    WHERE CAST(order_date AS DATE) = @BatchDate;
    
    INSERT INTO bi.fact_shipment_fulfillment (
        shipment_id, order_id, supplier_id, destination_warehouse_id, carrier_id,
        order_date, promised_delivery_date, actual_delivery_date, transit_days,
        promised_transit_days, transit_delay_days, on_time_flag, in_full_flag,
        otif_compliance_flag, weight_kg, quantity_units, freight_cost_usd,
        freight_cost_per_kg, damage_reported_flag, delay_reason, shipment_status
    )
    SELECT 
        shipment_id, order_id, supplier_id, destination_warehouse_id, carrier_id,
        order_date, promised_delivery_date, actual_delivery_date, transit_days,
        promised_transit_days, transit_delay_days, on_time_flag, in_full_flag,
        otif_compliance_flag, weight_kg, quantity_units, freight_cost_usd,
        freight_cost_per_kg, damage_reported_flag, delay_reason, shipment_status
    FROM stg.silver_shipments
    WHERE CAST(order_date AS DATE) = @BatchDate;
    
    PRINT 'bi.fact_shipment_fulfillment load completed successfully.';
END;
GO

CREATE OR ALTER PROCEDURE bi.usp_LoadMasterStarSchema
    @BatchDate VARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
            
            PRINT 'Executing Master ETL Pipeline Load...';
            EXEC bi.usp_LoadDimCarrier;
            EXEC bi.usp_LoadFactShipments @BatchDate = @BatchDate;
            
        COMMIT TRANSACTION;
        PRINT 'Master Star Schema load completed successfully without errors.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
        DECLARE @ErrorState INT = ERROR_STATE();
        
        RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
    END CATCH
END;
GO
