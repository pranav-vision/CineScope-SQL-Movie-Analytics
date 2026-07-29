-- ============================================
-- Project: CineScope SQL Movie Analytics
-- Database Creation and Table Schema
-- ============================================

-- Create the database
CREATE DATABASE IF NOT EXISTS cine_scope_db;

-- Select the database
USE cine_scope_db;

-- ============================================
-- Table 1: Movies
-- ============================================

CREATE TABLE movies (
    movie_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    release_year YEAR,
    duration_minutes INT,
    language VARCHAR(100),
    country VARCHAR(100),
    budget DECIMAL(15, 2),
    revenue DECIMAL(15, 2),
    imdb_rating DECIMAL(3, 1),
    vote_count INT
);

-- ============================================
-- Table 2: Genres
-- ============================================

CREATE TABLE genres (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name VARCHAR(100) NOT NULL UNIQUE
);

-- ============================================
-- Table 3: Movie-Genre Relationship
-- ============================================

CREATE TABLE movie_genres (
    movie_id INT,
    genre_id INT,

    PRIMARY KEY (movie_id, genre_id),

    FOREIGN KEY (movie_id)
        REFERENCES movies(movie_id)
        ON DELETE CASCADE,

    FOREIGN KEY (genre_id)
        REFERENCES genres(genre_id)
        ON DELETE CASCADE
);

-- ============================================
-- Table 4: Directors
-- ============================================

CREATE TABLE directors (
    director_id INT AUTO_INCREMENT PRIMARY KEY,
    director_name VARCHAR(255) NOT NULL
);

-- ============================================
-- Table 5: Movie-Director Relationship
-- ============================================

CREATE TABLE movie_directors (
    movie_id INT,
    director_id INT,

    PRIMARY KEY (movie_id, director_id),

    FOREIGN KEY (movie_id)
        REFERENCES movies(movie_id)
        ON DELETE CASCADE,

    FOREIGN KEY (director_id)
        REFERENCES directors(director_id)
        ON DELETE CASCADE
);
