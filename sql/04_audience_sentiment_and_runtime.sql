-- =====================================================
-- Project: CineScope SQL Movie Analytics
-- Script: 04_audience_sentiment_and_runtime.sql
-- Description: Runtime Bucket Correlation, Audience Sentiment Tiers & Multi-Genre Breakdown
-- =====================================================

USE cine_scope_db;

-- =====================================================
-- 1. Runtime Bucket Correlation Analysis
-- Buckets: <90m, 90-120m, 120-150m, 150m+
-- Correlates film length with financial yield and audience ratings.
-- =====================================================

SELECT
    CASE
        WHEN duration_minutes < 90 THEN 'Short (< 90m)'
        WHEN duration_minutes BETWEEN 90 AND 120 THEN 'Standard (90-120m)'
        WHEN duration_minutes BETWEEN 121 AND 150 THEN 'Feature (121-150m)'
        ELSE 'Epic (150m+)'
    END AS runtime_bucket,
    COUNT(*) AS movie_count,
    ROUND(AVG(budget), 2) AS avg_budget,
    ROUND(AVG(COALESCE(domestic_revenue + international_revenue, revenue)), 2) AS avg_global_revenue,
    ROUND(AVG(imdb_rating), 2) AS avg_imdb_rating,
    ROUND(AVG(vote_count), 0) AS avg_vote_count,
    ROUND(
        AVG(((COALESCE(domestic_revenue + international_revenue, revenue) - budget) / NULLIF(budget, 0)) * 100),
        2
    ) AS avg_roi_pct
FROM movies
GROUP BY
    CASE
        WHEN duration_minutes < 90 THEN 'Short (< 90m)'
        WHEN duration_minutes BETWEEN 90 AND 120 THEN 'Standard (90-120m)'
        WHEN duration_minutes BETWEEN 121 AND 150 THEN 'Feature (121-150m)'
        ELSE 'Epic (150m+)'
    END
ORDER BY avg_global_revenue DESC;


-- =====================================================
-- 2. Audience Sentiment Tiers & Box-Office Yield
-- Analyzes relationship between IMDb rating brackets and box-office outcomes.
-- =====================================================

SELECT
    CASE
        WHEN imdb_rating >= 8.5 THEN 'Masterpiece (8.5 - 10.0)'
        WHEN imdb_rating >= 8.0 THEN 'Highly Acclaimed (8.0 - 8.4)'
        WHEN imdb_rating >= 7.0 THEN 'Positive (7.0 - 7.9)'
        ELSE 'Mixed / Low (< 7.0)'
    END AS sentiment_tier,
    COUNT(*) AS movie_count,
    ROUND(AVG(COALESCE(domestic_revenue + international_revenue, revenue)), 2) AS avg_global_revenue,
    ROUND(AVG(budget), 2) AS avg_budget,
    ROUND(
        AVG(((COALESCE(domestic_revenue + international_revenue, revenue) - budget) / NULLIF(budget, 0)) * 100),
        2
    ) AS avg_roi_pct,
    SUM(COALESCE(domestic_revenue + international_revenue, revenue)) AS total_tier_revenue
FROM movies
GROUP BY
    CASE
        WHEN imdb_rating >= 8.5 THEN 'Masterpiece (8.5 - 10.0)'
        WHEN imdb_rating >= 8.0 THEN 'Highly Acclaimed (8.0 - 8.4)'
        WHEN imdb_rating >= 7.0 THEN 'Positive (7.0 - 7.9)'
        ELSE 'Mixed / Low (< 7.0)'
    END
ORDER BY avg_imdb_rating_order DESC;


-- Helper sorting order query (with numeric rank ordering):
SELECT
    CASE
        WHEN imdb_rating >= 8.5 THEN '1. Masterpiece (8.5 - 10.0)'
        WHEN imdb_rating >= 8.0 THEN '2. Highly Acclaimed (8.0 - 8.4)'
        WHEN imdb_rating >= 7.0 THEN '3. Positive (7.0 - 7.9)'
        ELSE '4. Mixed / Low (< 7.0)'
    END AS sentiment_tier,
    COUNT(*) AS movie_count,
    ROUND(AVG(COALESCE(domestic_revenue + international_revenue, revenue)), 2) AS avg_global_revenue,
    ROUND(AVG(budget), 2) AS avg_budget,
    ROUND(
        AVG(((COALESCE(domestic_revenue + international_revenue, revenue) - budget) / NULLIF(budget, 0)) * 100),
        2
    ) AS avg_roi_pct
FROM movies
GROUP BY sentiment_tier
ORDER BY sentiment_tier ASC;


-- =====================================================
-- 3. Multi-Genre Performance & Sentiment Breakdown
-- Evaluates individual genre tags across films with multi-genre associations.
-- =====================================================

SELECT
    g.genre_name,
    COUNT(m.movie_id) AS total_associated_movies,
    ROUND(AVG(m.duration_minutes), 1) AS avg_runtime_minutes,
    ROUND(AVG(m.imdb_rating), 2) AS avg_imdb_rating,
    ROUND(AVG(m.vote_count), 0) AS avg_vote_count,
    SUM(COALESCE(m.domestic_revenue + m.international_revenue, m.revenue)) AS total_genre_revenue,
    ROUND(AVG(COALESCE(m.domestic_revenue + m.international_revenue, m.revenue)), 2) AS avg_movie_revenue
FROM genres g
JOIN movie_genres mg ON g.genre_id = mg.genre_id
JOIN movies m ON mg.movie_id = m.movie_id
GROUP BY g.genre_id, g.genre_name
ORDER BY total_genre_revenue DESC;
