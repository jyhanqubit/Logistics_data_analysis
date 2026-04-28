DROP TABLE IF EXISTS dim_calendar;
DROP TABLE IF EXISTS dim_region;
DROP TABLE IF EXISTS dim_category;
DROP TABLE IF EXISTS dim_hub_candidate;
DROP TABLE IF EXISTS fact_parcel_od_daily;
DROP TABLE IF EXISTS fact_postcode_volume_monthly;
DROP TABLE IF EXISTS fact_daily_demand;

CREATE TABLE dim_calendar (
    date_key TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_weekend INTEGER NOT NULL,
    is_holiday INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL
);

CREATE TABLE dim_region (
    region_id INTEGER PRIMARY KEY,
    region_name TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    population INTEGER NOT NULL,
    ecommerce_index REAL NOT NULL,
    income_index REAL NOT NULL
);

CREATE TABLE dim_category (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL,
    perishability_score REAL NOT NULL,
    bulky_score REAL NOT NULL
);

CREATE TABLE dim_hub_candidate (
    hub_id INTEGER PRIMARY KEY,
    hub_name TEXT NOT NULL,
    region_id INTEGER NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    capacity_daily INTEGER NOT NULL,
    fixed_cost_score REAL NOT NULL,
    FOREIGN KEY(region_id) REFERENCES dim_region(region_id)
);

CREATE TABLE fact_parcel_od_daily (
    date_key TEXT NOT NULL,
    origin_region_id INTEGER NOT NULL,
    dest_region_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    parcel_volume INTEGER NOT NULL,
    avg_distance_km REAL NOT NULL,
    promised_sla_hours REAL NOT NULL,
    simulated_delay_rate REAL NOT NULL,
    FOREIGN KEY(date_key) REFERENCES dim_calendar(date_key),
    FOREIGN KEY(origin_region_id) REFERENCES dim_region(region_id),
    FOREIGN KEY(dest_region_id) REFERENCES dim_region(region_id),
    FOREIGN KEY(category_id) REFERENCES dim_category(category_id)
);

CREATE TABLE fact_postcode_volume_monthly (
    month_key TEXT NOT NULL,
    postcode TEXT NOT NULL,
    region_id INTEGER NOT NULL,
    inbound_volume INTEGER NOT NULL,
    FOREIGN KEY(region_id) REFERENCES dim_region(region_id)
);

CREATE TABLE fact_daily_demand (
    date_key TEXT NOT NULL,
    dest_region_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    inbound_volume INTEGER NOT NULL,
    PRIMARY KEY(date_key, dest_region_id, category_id),
    FOREIGN KEY(date_key) REFERENCES dim_calendar(date_key),
    FOREIGN KEY(dest_region_id) REFERENCES dim_region(region_id),
    FOREIGN KEY(category_id) REFERENCES dim_category(category_id)
);

CREATE INDEX idx_od_date_dest ON fact_parcel_od_daily(date_key, dest_region_id);
CREATE INDEX idx_demand_region_cat_date ON fact_daily_demand(dest_region_id, category_id, date_key);
