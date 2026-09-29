-- ============================================================================
--  Retail Analytics Query Book · SQLite / PostgreSQL-compatible ANSI SQL
--  All 10 queries use CTEs, and 7 of them use window functions.
--  Each query answers a business question a retail analyst is actually asked.
-- ============================================================================

-- Q1 — Monthly revenue, orders, and month-over-month growth ------------------
WITH monthly AS (
    SELECT
        strftime('%Y-%m', o.order_date)         AS month,
        SUM(oi.quantity * oi.unit_price)        AS revenue,
        COUNT(DISTINCT o.order_id)              AS orders,
        COUNT(DISTINCT o.customer_id)           AS active_customers
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    GROUP BY strftime('%Y-%m', o.order_date)
)
SELECT
    month, revenue, orders, active_customers,
    LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
                  / LAG(revenue) OVER (ORDER BY month), 2) AS mom_growth_pct
FROM monthly
ORDER BY month;

-- Q2 — Top 10 products by revenue with rank and % of total -------------------
WITH product_rev AS (
    SELECT
        p.product_id, p.name, c.name AS category,
        SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items oi
    JOIN products p   ON p.product_id  = oi.product_id
    JOIN categories c ON c.category_id = p.category_id
    GROUP BY p.product_id, p.name, c.name
)
SELECT
    product_id, name, category, revenue,
    RANK() OVER (ORDER BY revenue DESC)                            AS revenue_rank,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 2)               AS pct_of_total
FROM product_rev
ORDER BY revenue_rank
LIMIT 10;

-- Q3 — Category revenue with running total and share -------------------------
WITH category_rev AS (
    SELECT c.name AS category, SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items oi
    JOIN products   p ON p.product_id  = oi.product_id
    JOIN categories c ON c.category_id = p.category_id
    GROUP BY c.name
)
SELECT
    category, revenue,
    SUM(revenue) OVER (ORDER BY revenue DESC
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 2)                     AS share_pct
FROM category_rev
ORDER BY revenue DESC;

-- Q4 — Customer lifetime value, deciled ----------------------------------------
WITH cust AS (
    SELECT
        c.customer_id, c.country,
        COUNT(DISTINCT o.order_id)                AS orders,
        SUM(oi.quantity * oi.unit_price)          AS revenue
    FROM customers c
    JOIN orders o      ON o.customer_id = c.customer_id
    JOIN order_items oi ON oi.order_id  = o.order_id
    GROUP BY c.customer_id, c.country
),
deciled AS (
    SELECT
        customer_id, country, orders, revenue,
        NTILE(10) OVER (ORDER BY revenue DESC) AS decile
    FROM cust
)
SELECT
    decile,
    COUNT(*)                 AS customers_in_decile,
    ROUND(MIN(revenue), 2)   AS min_revenue,
    ROUND(MAX(revenue), 2)   AS max_revenue,
    ROUND(AVG(revenue), 2)   AS avg_revenue,
    ROUND(SUM(revenue), 2)   AS total_revenue
FROM deciled
GROUP BY decile
ORDER BY decile;

-- Q5 — RFM segmentation --------------------------------------------------------
--  Recency  = days since last order  (lower = better, so rank ASC on recency)
--  Frequency = number of orders
--  Monetary  = total spend
WITH base AS (
    SELECT
        c.customer_id,
        julianday('2026-09-01') - julianday(MAX(o.order_date)) AS recency_days,
        COUNT(DISTINCT o.order_id)                             AS frequency,
        SUM(oi.quantity * oi.unit_price)                       AS monetary
    FROM customers c
    JOIN orders o      ON o.customer_id = c.customer_id
    JOIN order_items oi ON oi.order_id  = o.order_id
    GROUP BY c.customer_id
),
scored AS (
    SELECT
        customer_id, recency_days, frequency, monetary,
        6 - NTILE(5) OVER (ORDER BY recency_days ASC)  AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)         AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)          AS m_score
    FROM base
)
SELECT
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 4 AND f_score >= 3                  THEN 'Loyal'
        WHEN r_score >= 4 AND f_score <= 2                  THEN 'New / Recent'
        WHEN r_score <= 2 AND f_score >= 4                  THEN 'At Risk'
        WHEN r_score <= 2 AND m_score >= 4                  THEN 'Cant Lose Them'
        WHEN r_score <= 2 AND f_score <= 2                  THEN 'Hibernating'
        ELSE 'Needs Attention'
    END                        AS segment,
    COUNT(*)                   AS customers,
    ROUND(AVG(monetary), 2)    AS avg_monetary,
    ROUND(AVG(frequency), 2)   AS avg_frequency,
    ROUND(AVG(recency_days),1) AS avg_recency_days
FROM scored
GROUP BY segment
ORDER BY avg_monetary DESC;

-- Q6 — Cohort retention by signup month ---------------------------------------
WITH firstm AS (
    SELECT customer_id, strftime('%Y-%m', signup_date) AS cohort_month
    FROM customers
),
activity AS (
    SELECT
        f.cohort_month,
        (CAST(strftime('%Y', o.order_date) AS INTEGER) * 12
             + CAST(strftime('%m', o.order_date) AS INTEGER))
        - (CAST(substr(f.cohort_month, 1, 4) AS INTEGER) * 12
             + CAST(substr(f.cohort_month, 6, 2) AS INTEGER)) AS months_since_signup,
        o.customer_id
    FROM orders o
    JOIN firstm f USING (customer_id)
)
SELECT
    cohort_month,
    COUNT(DISTINCT CASE WHEN months_since_signup = 0 THEN customer_id END) AS m0,
    COUNT(DISTINCT CASE WHEN months_since_signup = 1 THEN customer_id END) AS m1,
    COUNT(DISTINCT CASE WHEN months_since_signup = 3 THEN customer_id END) AS m3,
    COUNT(DISTINCT CASE WHEN months_since_signup = 6 THEN customer_id END) AS m6
FROM activity
GROUP BY cohort_month
ORDER BY cohort_month;

-- Q7 — Repeat purchase rate by country ----------------------------------------
WITH per_customer AS (
    SELECT c.country, c.customer_id,
           COUNT(DISTINCT o.order_id) AS orders
    FROM customers c
    LEFT JOIN orders o ON o.customer_id = c.customer_id
    GROUP BY c.country, c.customer_id
)
SELECT
    country,
    COUNT(*)                                                 AS customers,
    SUM(CASE WHEN orders >= 2 THEN 1 ELSE 0 END)             AS repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN orders >= 2 THEN 1 ELSE 0 END)
                / COUNT(*), 2)                               AS repeat_rate_pct
FROM per_customer
GROUP BY country
ORDER BY repeat_rate_pct DESC;

-- Q8 — Top-2 SKU per category (rank window) -----------------------------------
WITH ranked AS (
    SELECT
        c.name AS category, p.name AS product,
        SUM(oi.quantity * oi.unit_price) AS revenue,
        ROW_NUMBER() OVER (
            PARTITION BY c.name
            ORDER BY SUM(oi.quantity * oi.unit_price) DESC
        ) AS rn
    FROM order_items oi
    JOIN products   p ON p.product_id  = oi.product_id
    JOIN categories c ON c.category_id = p.category_id
    GROUP BY c.name, p.name
)
SELECT category, product, ROUND(revenue, 2) AS revenue
FROM ranked
WHERE rn <= 2
ORDER BY category, revenue DESC;

-- Q9 — Average basket size & margin by month ----------------------------------
WITH order_totals AS (
    SELECT
        o.order_id,
        strftime('%Y-%m', o.order_date)                       AS month,
        SUM(oi.quantity * oi.unit_price)                      AS gross,
        SUM(oi.quantity * (oi.unit_price - p.cost))           AS margin
    FROM orders o
    JOIN order_items oi ON oi.order_id  = o.order_id
    JOIN products    p ON p.product_id = oi.product_id
    GROUP BY o.order_id
)
SELECT
    month,
    COUNT(*)                                    AS orders,
    ROUND(AVG(gross), 2)                        AS avg_basket_value,
    ROUND(SUM(margin), 2)                       AS gross_margin,
    ROUND(100.0 * SUM(margin) / SUM(gross), 2)  AS margin_pct
FROM order_totals
GROUP BY month
ORDER BY month;

-- Q10 — Days between purchases per customer (LEAD/LAG) ------------------------
WITH ordered AS (
    SELECT
        customer_id, order_id, order_date,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_date
    FROM orders
)
SELECT
    customer_id,
    COUNT(*)                                                       AS orders,
    ROUND(AVG(julianday(order_date) - julianday(prev_date)), 1)    AS avg_days_between
FROM ordered
WHERE prev_date IS NOT NULL
GROUP BY customer_id
HAVING orders >= 3
ORDER BY avg_days_between ASC
LIMIT 15;
