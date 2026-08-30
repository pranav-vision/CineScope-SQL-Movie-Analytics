-- =====================================================
-- Project: CineScope SQL Movie Analytics
-- Script: 05_time_series_trends.sql
-- Description: Year-over-Year (YoY), Month-over-Month (MoM) Growth & Cumulative Box Office Running Totals
-- =====================================================

USE cine_scope_db;

-- =====================================================
-- 1. Year-over-Year (YoY) Revenue Growth Analysis (LAG Window Function)
-- Tracks annual box office totals and percentage change over the prior year.
-- =====================================================

WITH yearly_revenue_summary AS (
    SELECT
        release_year,
        COUNT(movie_id) AS movies_released,
        SUM(budget) AS total_annual_budget,
        SUM(COALESCE(domestic_revenue + international_revenue, revenue)) AS total_annual_revenue
    FROM movies
    GROUP BY release_year
)
SELECT
    release_year,
    movies_released,
    total_annual_budget,
    total_annual_revenue,
    LAG(total_annual_revenue, 1) OVER (ORDER BY release_year) AS prior_year_revenue,
    (total_annual_revenue - LAG(total_annual_revenue, 1) OVER (ORDER BY release_year)) AS yoy_revenue_change,
    ROUND(
        (
            (total_annual_revenue - LAG(total_annual_revenue, 1) OVER (ORDER BY release_year)) / 
            NULLIF(LAG(total_annual_revenue, 1) OVER (ORDER BY release_year), 0)
        ) * 100,
        2
    ) AS yoy_growth_percentage
FROM yearly_revenue_summary
ORDER BY release_year ASC;


-- =====================================================
-- 2. Month-over-Month (MoM) Revenue Growth Analysis
-- Analyzes monthly release trends and month-on-month growth.
-- =====================================================

WITH monthly_revenue_summary AS (
    SELECT
        YEAR(release_date) AS release_yr,
        MONTH(release_date) AS release_mo,
        DATE_FORMAT(release_date, '%Y-%m') AS year_month,
        COUNT(movie_id) AS movies_released,
        SUM(COALESCE(domestic_revenue + international_revenue, revenue)) AS monthly_revenue
    FROM movies
    WHERE release_date IS NOT NULL
    GROUP BY YEAR(release_date), MONTH(release_date), DATE_FORMAT(release_date, '%Y-%m')
)
SELECT
    year_month,
    release_yr,
    release_mo,
    movies_released,
    monthly_revenue,
    LAG(monthly_revenue, 1) OVER (ORDER BY release_yr, release_mo) AS prior_month_revenue,
    ROUND(
        (
            (monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY release_yr, release_mo)) / 
            NULLIF(LAG(monthly_revenue, 1) OVER (ORDER BY release_yr, release_mo), 0)
        ) * 100,
        2
    ) AS mom_growth_percentage
FROM monthly_revenue_summary
ORDER BY release_yr ASC, release_mo ASC;


-- =====================================================
-- 3. Cumulative Box Office Gross Running Total (Window SUM)
-- Calculates the cumulative historical running total gross revenue across release years.
-- =====================================================

WITH yearly_totals AS (
    SELECT
        release_year,
        SUM(COALESCE(domestic_revenue + international_revenue, revenue)) AS annual_revenue,
        SUM(budget) AS annual_budget
    FROM movies
    GROUP BY release_year
)
SELECT
    release_year,
    annual_revenue,
    SUM(annual_revenue) OVER (
        ORDER BY release_year 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_running_total_revenue,
    SUM(annual_budget) OVER (
        ORDER BY release_year 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_running_total_budget
FROM yearly_totals
ORDER BY release_year ASC;


-- =====================================================
-- 4. Decade Evolution & Long-Term Trend Aggregation
-- Aggregates movie analytics by decade (e.g. 1990s, 2000s, 2010s, 2020s).
-- =====================================================

SELECT
    CONCAT(FLOOR(release_year / 10) * 10, 's') AS decade,
    COUNT(*) AS total_movies,
    SUM(budget) AS total_decade_budget,
    SUM(COALESCE(domestic_revenue + international_revenue, revenue)) AS total_decade_revenue,
    ROUND(AVG(imdb_rating), 2) AS avg_decade_rating,
    ROUND(
        ((SUM(COALESCE(domestic_revenue + international_revenue, revenue)) - SUM(budget)) / NULLIF(SUM(budget), 0)) * 100,
        2
    ) AS decade_overall_roi_pct
FROM movies
GROUP BY CONCAT(FLOOR(release_year / 10) * 10, 's')
ORDER BY decade ASC;
