SELECT sku_id,
       on_hand,
       daily_demand,
       CASE WHEN daily_demand=0 THEN 0 ELSE ROUND(1.0/(on_hand*1.0/daily_demand),4) END AS stockout_risk_score
FROM inventory_snapshot
ORDER BY stockout_risk_score DESC
LIMIT 50;
