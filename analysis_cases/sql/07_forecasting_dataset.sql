SELECT f.date_key,
       r.region_name,
       c.category_name,
       f.inbound_volume
FROM fact_daily_demand f
JOIN dim_region r ON f.dest_region_id = r.region_id
JOIN dim_category c ON f.category_id = c.category_id;
