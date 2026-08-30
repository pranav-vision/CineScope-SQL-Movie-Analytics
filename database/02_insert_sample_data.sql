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
-- Insert Actors / Talent
-- ============================================

INSERT INTO actors (actor_name)
VALUES
    ('Leonardo DiCaprio'),
    ('Matthew McConaughey'),
    ('Sam Worthington'),
    ('Kate Winslet'),
    ('Sam Neill'),
    ('Elijah Wood'),
    ('John Travolta'),
    ('Song Kang-ho'),
    ('Tom Hardy'),
    ('Timothée Chalamet');

-- ============================================
-- Insert Movies
-- ============================================

INSERT INTO movies
(
    title,
    release_year,
    release_date,
    duration_minutes,
    language,
    country,
    budget,
    revenue,
    domestic_revenue,
    international_revenue,
    imdb_rating,
    vote_count
)
VALUES
(
    'Inception',
    2010,
    '2010-07-16',
    148,
    'English',
    'USA',
    160000000,
    839000000,
    292576195,
    546423805,
    8.8,
    2600000
),
(
    'Interstellar',
    2014,
    '2014-11-07',
    169,
    'English',
    'USA',
    165000000,
    731000000,
    188020017,
    542979983,
    8.7,
    2300000
),
(
    'Avatar',
    2009,
    '2009-12-18',
    162,
    'English',
    'USA',
    237000000,
    2920000000,
    785221649,
    2134778351,
    7.9,
    1400000
),
(
    'Titanic',
    1997,
    '1997-12-19',
    195,
    'English',
    'USA',
    200000000,
    2260000000,
    659363944,
    1600636056,
    7.9,
    1300000
),
(
    'Jurassic Park',
    1993,
    '1993-06-11',
    127,
    'English',
    'USA',
    63000000,
    1046000000,
    404214720,
    641785280,
    8.2,
    1100000
),
(
    'The Lord of the Rings: The Return of the King',
    2003,
    '2003-12-17',
    201,
    'English',
    'New Zealand',
    94000000,
    1146000000,
    377845905,
    768154095,
    9.0,
    2000000
),
(
    'Pulp Fiction',
    1994,
    '1994-10-14',
    154,
    'English',
    'USA',
    8000000,
    214000000,
    107928762,
    106071238,
    8.9,
    2300000
),
(
    'Parasite',
    2019,
    '2019-05-30',
    132,
    'Korean',
    'South Korea',
    11400000,
    262000000,
    53369749,
    208630251,
    8.5,
    1000000
),
(
    'Mad Max: Fury Road',
    2015,
    '2015-05-15',
    120,
    'English',
    'Australia',
    150000000,
    380000000,
    154064072,
    225935928,
    8.1,
    1100000
),
(
    'Dune',
    2021,
    '2021-10-22',
    155,
    'English',
    'USA',
    165000000,
    407000000,
    108327830,
    298672170,
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

-- ============================================
-- Insert Movie-Actor Relationships
-- ============================================

INSERT INTO movie_actors (movie_id, actor_id, role_type)
VALUES
    (1, 1, 'Lead'),    -- Leonardo DiCaprio in Inception
    (2, 2, 'Lead'),    -- Matthew McConaughey in Interstellar
    (3, 3, 'Lead'),    -- Sam Worthington in Avatar
    (4, 1, 'Lead'),    -- Leonardo DiCaprio in Titanic
    (4, 4, 'Co-Lead'), -- Kate Winslet in Titanic
    (5, 5, 'Lead'),    -- Sam Neill in Jurassic Park
    (6, 6, 'Lead'),    -- Elijah Wood in LOTR
    (7, 7, 'Lead'),    -- John Travolta in Pulp Fiction
    (8, 8, 'Lead'),    -- Song Kang-ho in Parasite
    (9, 9, 'Lead'),    -- Tom Hardy in Mad Max
    (10, 10, 'Lead');  -- Timothée Chalamet in Dune