# Dashboard Data Specification (Used Columns)

## outputs/insights/business_action_recommendations.csv
- action_id, priority, area, business_finding, recommended_action, expected_impact
- evidence_metric, evidence_value, risk_level, owner_function, dashboard_section
- expected_impact_score, urgency_score, action_value

## outputs/insights/action_priority_matrix.csv
- action_id, priority, area, expected_impact_score, implementation_urgency, action_value, recommended_action

## outputs/analysis_cases/01_oms_order_flow.csv
- region_name, product_category, period_type, order_count
- avg_order_to_release_hours, p95_order_to_release_hours, delayed_release_rate, business_action

## outputs/analysis_cases/02_oms_peak_order_risk.csv
- region_name, product_category, baseline_order_volume, peak_order_volume
- peak_order_ratio, risk_score, risk_level, business_action

## outputs/analysis_cases/03_wms_inventory_risk.csv
- warehouse_id, region_name, product_category, forecast_demand, available_inventory
- safety_stock, stockout_gap, stockout_risk_score, reorder_priority, business_action

## outputs/analysis_cases/04_wms_picking_workload.csv
- warehouse_id, warehouse_name, region_name, product_category
- expected_order_lines, expected_pick_units, avg_pick_pack_cycle_minutes
- warehouse_capacity_units, warehouse_utilization, workload_risk_level, business_action

## outputs/analysis_cases/05_tms_delivery_sla.csv
- region_name, product_category, shipment_count, avg_route_distance_km
- avg_vehicle_utilization, on_time_delivery_rate, late_delivery_risk_score
- risk_level, business_action

## outputs/analysis_cases/06_tms_route_optimization.csv
- vehicle_id, stops, vehicle_load, vehicle_capacity, vehicle_utilization
- baseline_distance_km, optimized_distance_km, distance_saving_km
- distance_saving_rate, business_action

## outputs/analysis_cases/07_demand_forecasting_region_category.csv
- region_name, product_category, model, wape, smape, mae, rmse
- peak_season_wape, forecast_risk_level, business_action

## outputs/analysis_cases/08_locker_site_recommendation.csv
- region_name, rank, locker_score, mfc_score, forecast_volume, peak_ratio
- volatility, nearest_hub_distance_km, recommendation_reason, business_action

## outputs/advanced_analytics/*
- regression: model_metrics, predictions, feature_importance
- classification: model_metrics, predictions, confusion_matrix, feature_importance
- statistics: statistical_tests, effect_sizes, group_summary
- time_series: decomposition(observed/trend/seasonal/residual/arima_fitted), acf_pacf, cross_correlation
- clustering: cluster_assignments, cluster_profiles, cluster_quality_scores, seoul_district_centroids
- optimization: optimization_formulation, solver_comparison
- qubo: qubo_matrix_extended, qubo_solution_extended, qubo_eigenvalues, qubo_candidates
