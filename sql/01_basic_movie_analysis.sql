-- =====================================================
-- Project: CineScope SQL Movie Analytics
-- File: Basic Movie Analysis
-- =====================================================

USE cine_scope_db;

-- =====================================================
-- 1. Display all movie records
-- =====================================================

SELECT *
FROM movies;


-- =====================================================
-- 2. Display selected movie information
-- =====================================================

SELECT
    title,
    release_year,
    imdb_rating,
    revenue
FROM movies;


-- =====================================================
-- 3. Find movies with an IMDb rating of 8.5 or higher
-- =====================================================

SELECT
    title,
    imdb_rating
FROM movies
WHERE imdb_rating >= 8.5
ORDER BY imdb_rating DESC;


-- =====================================================
-- 4. Find movies released after 2010
-- =====================================================

SELECT
    title,
    release_year
FROM movies
WHERE release_year > 2010
ORDER BY release_year;


-- =====================================================
-- 5. Find movies released between 2000 and 2020
-- =====================================================

SELECT
    title,
    release_year
FROM movies
WHERE release_year BETWEEN 2000 AND 2020
ORDER BY release_year;


-- =====================================================
-- 6. Find movies from selected countries
-- =====================================================

SELECT
    title,
    country
FROM movies
WHERE country IN ('USA', 'Australia', 'South Korea');


-- =====================================================
-- 7. Find movies with titles containing "The"
-- =====================================================

SELECT
    title
FROM movies
WHERE title LIKE '%The%';


-- =====================================================
-- 8. Display unique languages
-- =====================================================

SELECT DISTINCT
    language
FROM movies
ORDER BY language;


-- =====================================================
-- 9. Find the top 5 highest-rated movies
-- =====================================================

SELECT
    title,
    imdb_rating
FROM movies
ORDER BY imdb_rating DESC
LIMIT 5;


-- =====================================================
-- 10. Find the top 5 highest-revenue movies
-- =====================================================

SELECT
    title,
    revenue
FROM movies
ORDER BY revenue DESC
LIMIT 5;


-- =====================================================
-- 11. Calculate the total number of movies
-- =====================================================

SELECT
    COUNT(*) AS total_movies
FROM movies;


-- =====================================================
-- 12. Calculate the average IMDb rating
-- =====================================================

SELECT
    ROUND(AVG(imdb_rating), 2) AS average_imdb_rating
FROM movies;


-- =====================================================
-- 13. Find the highest and lowest IMDb ratings
-- =====================================================

SELECT
    MAX(imdb_rating) AS highest_rating,
    MIN(imdb_rating) AS lowest_rating
FROM movies;


-- =====================================================
-- 14. Calculate total movie revenue
-- =====================================================

SELECT
    SUM(revenue) AS total_revenue
FROM movies;


-- =====================================================
-- 15. Calculate average movie budget
-- =====================================================

SELECT
    ROUND(AVG(budget), 2) AS average_budget
FROM movies;


-- =====================================================
-- 16. Count movies by language
-- =====================================================

SELECT
    language,
    COUNT(*) AS total_movies
FROM movies
GROUP BY language
ORDER BY total_movies DESC;


-- =====================================================
-- 17. Calculate average rating by country
-- =====================================================

SELECT
    country,
    ROUND(AVG(imdb_rating), 2) AS average_rating
FROM movies
GROUP BY country
ORDER BY average_rating DESC;


-- =====================================================
-- 18. Find countries with more than one movie
-- =====================================================

SELECT
    country,
    COUNT(*) AS total_movies
FROM movies
GROUP BY country
HAVING COUNT(*) > 1
ORDER BY total_movies DESC;


-- =====================================================
-- 19. Find high-budget movies
-- =====================================================

SELECT
    title,
    budget
FROM movies
WHERE budget > 150000000
ORDER BY budget DESC;


-- =====================================================
-- 20. Calculate movie profit
-- Profit = Revenue - Budget
-- =====================================================

SELECT
    title,
    budget,
    revenue,
    (revenue - budget) AS profit
FROM movies
ORDER BY profit DESC;