-- =====================================================
-- Project: CineScope SQL Movie Analytics
-- Script: 03_talent_and_director_performance.sql
-- Description: Director & Actor Box-Office Performance, Window Functions & Hit Rates
-- =====================================================

USE cine_scope_db;

-- =====================================================
-- 1. Director Historical Box-Office Averages (Window Functions)
-- Evaluates director track record using PARTITION BY window functions.
-- =====================================================

SELECT DISTINCT
    d.director_id,
    d.director_name,
    COUNT(m.movie_id) OVER (PARTITION BY d.director_id) AS total_directed_movies,
    ROUND(AVG(m.budget) OVER (PARTITION BY d.director_id), 2) AS avg_director_budget,
    ROUND(AVG(COALESCE(m.domestic_revenue + m.international_revenue, m.revenue)) OVER (PARTITION BY d.director_id), 2) AS avg_director_revenue,
    ROUND(AVG(COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) - m.budget) OVER (PARTITION BY d.director_id), 2) AS avg_director_profit,
    ROUND(AVG(m.imdb_rating) OVER (PARTITION BY d.director_id), 2) AS avg_director_imdb_rating,
    ROUND(
        AVG(((COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) - m.budget) / NULLIF(m.budget, 0)) * 100) OVER (PARTITION BY d.director_id),
        2
    ) AS avg_director_roi_pct
FROM directors d
JOIN movie_directors md ON d.director_id = md.director_id
JOIN movies m ON md.movie_id = m.movie_id
ORDER BY avg_director_revenue DESC;


-- =====================================================
-- 2. Lead Actor / Talent Performance & Career Box-Office Averages
-- Calculates career box-office averages per actor using Window Functions.
-- =====================================================

SELECT DISTINCT
    a.actor_id,
    a.actor_name,
    COUNT(m.movie_id) OVER (PARTITION BY a.actor_id) AS total_starring_movies,
    ROUND(AVG(m.budget) OVER (PARTITION BY a.actor_id), 2) AS avg_actor_movie_budget,
    ROUND(AVG(COALESCE(m.domestic_revenue + m.international_revenue, m.revenue)) OVER (PARTITION BY a.actor_id), 2) AS avg_actor_movie_revenue,
    ROUND(AVG(m.imdb_rating) OVER (PARTITION BY a.actor_id), 2) AS avg_actor_imdb_rating,
    ROUND(
        AVG(((COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) - m.budget) / NULLIF(m.budget, 0)) * 100) OVER (PARTITION BY a.actor_id),
        2
    ) AS avg_actor_roi_pct
FROM actors a
JOIN movie_actors ma ON a.actor_id = ma.actor_id
JOIN movies m ON ma.movie_id = m.movie_id
ORDER BY avg_actor_movie_revenue DESC;


-- =====================================================
-- 3. Talent Consistency Score & Hit-Rate Percentage
-- Hit Rate %: Percentage of starring movies achieving ROI >= 100% or IMDb Rating >= 8.0
-- Consistency Score: Standard deviation of ratings / ROI stability evaluation
-- =====================================================

WITH actor_movie_stats AS (
    SELECT
        a.actor_id,
        a.actor_name,
        m.movie_id,
        m.imdb_rating,
        ((COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) - m.budget) / NULLIF(m.budget, 0)) * 100 AS roi_pct,
        CASE WHEN ((COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) - m.budget) / NULLIF(m.budget, 0)) >= 1.0 THEN 1 ELSE 0 END AS is_hit
    FROM actors a
    JOIN movie_actors ma ON a.actor_id = ma.actor_id
    JOIN movies m ON ma.movie_id = m.movie_id
)
SELECT
    actor_id,
    actor_name,
    COUNT(movie_id) AS total_projects,
    SUM(is_hit) AS hit_count,
    ROUND((SUM(is_hit) / COUNT(movie_id)) * 100, 2) AS hit_rate_percentage,
    ROUND(AVG(imdb_rating), 2) AS mean_imdb_rating,
    ROUND(COALESCE(STDDEV_SAMP(imdb_rating), 0), 2) AS rating_std_dev,
    ROUND(
        CASE 
            WHEN COALESCE(STDDEV_SAMP(imdb_rating), 0) = 0 THEN 100.0
            ELSE (AVG(imdb_rating) / STDDEV_SAMP(imdb_rating)) * 10 
        END, 
        2
    ) AS consistency_score
FROM actor_movie_stats
GROUP BY actor_id, actor_name
ORDER BY hit_rate_percentage DESC, consistency_score DESC;


-- =====================================================
-- 4. Director-Actor Power Duos Analytics
-- Measures box office performance when specific director-actor pairs collaborate.
-- =====================================================

SELECT
    d.director_name,
    a.actor_name,
    COUNT(m.movie_id) AS collaborations,
    SUM(COALESCE(m.domestic_revenue + m.international_revenue, m.revenue)) AS total_duo_revenue,
    ROUND(AVG(m.imdb_rating), 2) AS avg_duo_rating,
    ROUND(AVG(((COALESCE(m.domestic_revenue + m.international_revenue, m.revenue) - m.budget) / NULLIF(m.budget, 0)) * 100), 2) AS avg_duo_roi_pct
FROM movies m
JOIN movie_directors md ON m.movie_id = md.movie_id
JOIN directors d ON md.director_id = d.director_id
JOIN movie_actors ma ON m.movie_id = ma.movie_id
JOIN actors a ON ma.actor_id = a.actor_id
GROUP BY d.director_id, d.director_name, a.actor_id, a.actor_name
ORDER BY total_duo_revenue DESC;
