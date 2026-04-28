# Model Card — Demand Forecasting

## Model

- Type: GradientBoostingRegressor
- Target: `inbound_volume`
- Forecast unit: `dest_region_id × category_id × date_key`
- Test split: last 28 days temporal split

## Features

- Calendar: month, day of week, weekend, holiday, week of year
- Seasonality: sin/cos month and day-of-week
- Region: population, ecommerce_index, income_index
- Category: perishability_score, bulky_score
- Time-series lag: lag 1/7/14, rolling 7/14 mean

## Metrics

- MAE
- RMSE
- WAPE
- sMAPE

## Known Limitations

- Basic PoC uses synthetic data by default.
- Forecast is point forecast, not probabilistic forecast.
- External disruptions, weather, promotions, and capacity constraints are not modeled yet.
