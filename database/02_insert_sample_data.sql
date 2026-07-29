-- ============================================
-- Project: CineScope SQL Movie Analytics
-- Sample Movie Data
-- ============================================

USE cine_scope_db;

-- ============================================
-- Insert Genres
-- ============================================

INSERT INTO genres (genre_name)
VALUES
    ('Action'),
    ('Adventure'),
    ('Animation'),
    ('Comedy'),
    ('Crime'),
    ('Drama'),
    ('Fantasy'),
    ('Science Fiction'),
    ('Thriller');

-- ============================================
-- Insert Directors
-- ============================================

INSERT INTO directors (director_name)
VALUES
    ('Christopher Nolan'),
    ('James Cameron'),
    ('Steven Spielberg'),
    ('Peter Jackson'),
    ('Quentin Tarantino'),
    ('Bong Joon-ho'),
    ('George Miller'),
    ('Denis Villeneuve');

-- ============================================
-- Insert Movies
-- ============================================

INSERT INTO movies
(
    title,
    release_year,
    duration_minutes,
    language,
    country,
    budget,
    revenue,
    imdb_rating,
    vote_count
)
VALUES
(
    'Inception',
    2010,
    148,
    'English',
    'USA',
    160000000,
    839000000,
    8.8,
    2600000
),
(
    'Interstellar',
    2014,
    169,
    'English',
    'USA',
    165000000,
    731000000,
    8.7,
    2300000
),
(
    'Avatar',
    2009,
    162,
    'English',
    'USA',
    237000000,
    2920000000,
    7.9,
    1400000
),
(
    'Titanic',
    1997,
    195,
    'English',
    'USA',
    200000000,
    2260000000,
    7.9,
    1300000
),
(
    'Jurassic Park',
    1993,
    127,
    'English',
    'USA',
    63000000,
    1046000000,
    8.2,
    1100000
),
(
    'The Lord of the Rings: The Return of the King',
    2003,
    201,
    'English',
    'New Zealand',
    94000000,
    1146000000,
    9.0,
    2000000
),
(
    'Pulp Fiction',
    1994,
    154,
    'English',
    'USA',
    8000000,
    214000000,
    8.9,
    2300000
),
(
    'Parasite',
    2019,
    132,
    'Korean',
    'South Korea',
    11400000,
    262000000,
    8.5,
    1000000
),
(
    'Mad Max: Fury Road',
    2015,
    120,
    'English',
    'Australia',
    150000000,
    380000000,
    8.1,
    1100000
),
(
    'Dune',
    2021,
    155,
    'English',
    'USA',
    165000000,
    407000000,
    8.0,
    900000
);

-- ============================================
-- Insert Movie-Genre Relationships
-- ============================================

INSERT INTO movie_genres (movie_id, genre_id)
VALUES
    (1, 1),
    (1, 7),
    (1, 8),

    (2, 6),
    (2, 7),
    (2, 8),

    (3, 1),
    (3, 2),
    (3, 7),
    (3, 8),

    (4, 6),
    (4, 7),

    (5, 1),
    (5, 2),
    (5, 8),

    (6, 1),
    (6, 2),
    (6, 6),
    (6, 7),

    (7, 5),
    (7, 6),
    (7, 9),

    (8, 5),
    (8, 6),
    (8, 9),

    (9, 1),
    (9, 2),
    (9, 8),

    (10, 2),
    (10, 6),
    (10, 8);

-- ============================================
-- Insert Movie-Director Relationships
-- ============================================

INSERT INTO movie_directors (movie_id, director_id)
VALUES
    (1, 1),
    (2, 1),
    (3, 2),
    (4, 2),
    (5, 3),
    (6, 4),
    (7, 5),
    (8, 6),
    (9, 7),
    (10, 8);