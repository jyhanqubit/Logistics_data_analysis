SELECT COUNT(*) AS shipment_count,
       AVG(CASE WHEN is_on_time THEN 1.0 ELSE 0.0 END) AS on_time_delivery_rate,
       AVG(delivered_in_hours) AS avg_delivery_hours
FROM delivery_sla;
