WITH evt AS (
  SELECT order_id,
         MIN(CASE WHEN event_type='ORDER_RECEIVED' THEN event_ts END) AS received_ts,
         MIN(CASE WHEN event_type='RELEASED_TO_WMS' THEN event_ts END) AS released_ts
  FROM order_status_events
  GROUP BY order_id
)
SELECT COUNT(*) AS order_count,
       AVG((julianday(released_ts)-julianday(received_ts))*24.0) AS order_to_release_lead_time
FROM evt;
