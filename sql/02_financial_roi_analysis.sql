-- =====================================================
-- Project: CineScope SQL Movie Analytics
-- Script: 02_financial_roi_analysis.sql
-- Description: Financial Risk, Profitability & ROI Analysis
-- =====================================================

USE cine_scope_db;

-- =====================================================
-- 1. Individual Movie ROI & Net Profit Calculation
-- ROI Formula: ((Domestic_Revenue + International_Revenue) - Budget) / Budget * 100
-- Note: COALESCE handles split revenue or total revenue fallback cleanly.
-- =====================================================

SELECT
    movie_id,
    title,
    release_year,
    budget,
    COALESCE(domestic_revenue + international_revenue, revenue) AS total_revenue,
    (COALESCE(domestic_revenue + international_revenue, revenue) - budget) AS net_profit,
    ROUND(
        ((COALESCE(domestic_revenue + international_revenue, revenue) - budget) / NULLIF(budget, 0)) * 100, 
        2
    ) AS roi_percentage
FROM movies
ORDER BY roi_percentage DESC;


-- =====================================================
-- 2. Genre Financial Ranking & Risk Analysis (CTEs & DENSE_RANK)
-- Ranks genres by total global revenue and average ROI % to identify high-performing & risky genres.
-- =====================================================

WITH genre_financial_summary AS (
    SELECT
        g.genre_name,
        COUNT(m.movie_id) AS total_movies,
        SUM(m.budget) AS total_genre_budget,
        SUM(COALESCE(m.domestic_revenue + m.international_revenue, m.revenue)) AS total_genre_revenue,
        SUM(COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) - m.budget) AS total_genre_profit,
        ROUND(
            AVG(((COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) - m.budget) / NULLIF(m.budget, 0)) * 100),
            2
        ) AS avg_genre_roi_pct
    FROM genres g
    JOIN movie_genres mg ON g.genre_id = mg.genre_id
    JOIN movies m ON mg.movie_id = m.movie_id
    GROUP BY g.genre_name
)
SELECT
    genre_name,
    total_movies,
    total_genre_budget,
    total_genre_revenue,
    total_genre_profit,
    avg_genre_roi_pct,
    DENSE_RANK() OVER (ORDER BY total_genre_revenue DESC) AS revenue_rank,
    DENSE_RANK() OVER (ORDER BY avg_genre_roi_pct DESC) AS roi_rank,
    CASE
        WHEN avg_genre_roi_pct >= 500 THEN 'Low Risk - High Yield'
        WHEN avg_genre_roi_pct >= 200 THEN 'Moderate Risk - Stable'
        ELSE 'High Risk - Low Margin'
    END AS risk_tier
FROM genre_financial_summary
ORDER BY roi_rank ASC;


-- =====================================================
-- 3. Profitability Tier Classification (Conditional Logic)
-- Classifies movies into strategic commercial tiers based on ROI multiplier.
-- =====================================================

SELECT
    m.title,
    m.release_year,
    m.budget,
    COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) AS total_revenue,
    ROUND(((COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) - m.budget) / NULLIF(m.budget, 0)) * 100, 2) AS roi_pct,
    CASE
        WHEN ((COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) - m.budget) / NULLIF(m.budget, 0)) >= 4.0 THEN 'Blockbuster (4x+ ROI)'
        WHEN ((COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) - m.budget) / NULLIF(m.budget, 0)) >= 1.0 THEN 'Profitable (1x-4x ROI)'
        WHEN ((COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) - m.budget) / NULLIF(m.budget, 0)) >= 0.0 THEN 'Broke Even (0x-1x ROI)'
        ELSE 'Box Office Flop (<0x ROI)'
    END AS profitability_tier
FROM movies m
ORDER BY roi_pct DESC;


-- =====================================================
-- 4. Executive Portfolio ROI & Risk Summary
-- Overall aggregate portfolio metrics for executive dashboard reporting.
-- =====================================================

SELECT
    COUNT(*) AS total_portfolio_movies,
    SUM(budget) AS total_invested_budget,
    SUM(COALESCE(domestic_revenue + international_revenue, revenue)) AS total_portfolio_revenue,
    SUM(COALESCE(domestic_revenue + international_revenue, revenue) - budget) AS total_net_profit,
    ROUND(
        ((SUM(COALESCE(domestic_revenue + international_revenue, revenue)) - SUM(budget)) / NULLIF(SUM(budget), 0)) * 100,
        2
    ) AS overall_portfolio_roi_pct,
    SUM(CASE WHEN (COALESCE(domestic_revenue + international_revenue, revenue) - budget) >= budget * 4 THEN 1 ELSE 0 END) AS blockbuster_count,
    SUM(CASE WHEN (COALESCE(domestic_revenue + international_revenue, revenue) - budget) < 0 THEN 1 ELSE 0 END) AS flop_count
FROM movies;
