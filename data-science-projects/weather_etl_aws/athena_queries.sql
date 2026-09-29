-- Athena queries against the `weather_dev.readings` table
-- (partitioned by year/month/day for cost-effective scans).

-- Q1 — Latest reading per city (uses partition pruning) --------------------
WITH ranked AS (
  SELECT r.*,
         ROW_NUMBER() OVER (PARTITION BY city ORDER BY observed_at_utc DESC) AS rn
  FROM   weather_dev.readings
  WHERE  year  = date_format(current_date, '%Y')
    AND  month = date_format(current_date, '%m')
)
SELECT city, country, observed_at_utc, temperature_c, feels_like_c,
       humidity_pct, condition, comfort_band
FROM   ranked
WHERE  rn = 1
ORDER  BY city;

-- Q2 — Daily min/max/avg per city ------------------------------------------
SELECT city, year, month, day,
       ROUND(MIN(temperature_c),  1) AS min_c,
       ROUND(AVG(temperature_c),  1) AS avg_c,
       ROUND(MAX(temperature_c),  1) AS max_c,
       ROUND(AVG(feels_like_c),   1) AS avg_feels_c,
       COUNT(*)                     AS readings
FROM   weather_dev.readings
WHERE  year = '2026' AND month = '09'
GROUP  BY city, year, month, day
ORDER  BY city, day;

-- Q3 — Hourly rolling 3-hour temp trend for one city -----------------------
SELECT observed_at_utc, temperature_c,
       ROUND(AVG(temperature_c) OVER (
              ORDER BY observed_at_utc
              ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS temp_3h_avg
FROM   weather_dev.readings
WHERE  city = 'Blacksburg' AND year = '2026' AND month = '09'
ORDER  BY observed_at_utc;

-- Q4 — Comfort-band share across all cities --------------------------------
SELECT comfort_band,
       COUNT(*)                                                 AS readings,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)       AS share_pct
FROM   weather_dev.readings
WHERE  year = '2026' AND month = '09'
GROUP  BY comfort_band
ORDER  BY readings DESC;
