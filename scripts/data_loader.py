#!/usr/bin/env python3
"""
=====================================================
CineScope SQL Movie Analytics - Data Ingestion Pipeline
File: scripts/data_loader.py
Description: Cleans, normalizes, validates, and loads raw TMDb / IMDb CSV 
             datasets into MySQL (cine_scope_db).
=====================================================
"""

import os
import sys
import re
import argparse
import logging
from typing import List, Dict, Tuple
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CineScopeDataLoader")

# Default Connection Config
DEFAULT_DB_URI = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://root:password@localhost:3306/cine_scope_db"
)


def clean_currency(value) -> float:
    """Strips currency symbols ($), commas, and spaces, converting to float."""
    if pd.isna(value) or value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    
    cleaned_str = re.sub(r"[^\d.]", "", str(value))
    try:
        return float(cleaned_str) if cleaned_str else 0.0
    except ValueError:
        return 0.0


def validate_and_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Performs data validation, deduplication, and normalization."""
    logger.info("Starting data cleaning and validation...")
    initial_count = len(df)

    # 1. Clean numeric and currency fields
    currency_cols = ["budget", "revenue", "domestic_revenue", "international_revenue"]
    for col in currency_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_currency)
        else:
            df[col] = 0.0

    # 2. Derive split revenue if missing
    df["revenue"] = df.apply(
        lambda r: r["revenue"] if r["revenue"] > 0 else (r["domestic_revenue"] + r["international_revenue"]),
        axis=1
    )

    # 3. Clean numeric ratings & counts
    df["imdb_rating"] = pd.to_numeric(df.get("imdb_rating", 0.0), errors="coerce").fillna(0.0)
    df["vote_count"] = pd.to_numeric(df.get("vote_count", 0), errors="coerce").fillna(0)
    df["duration_minutes"] = pd.to_numeric(df.get("duration_minutes", 0), errors="coerce").fillna(0)

    # 4. Handle release dates and years
    if "release_date" in df.columns:
        df["release_date"] = pd.to_datetime(df["release_date"], format="mixed", errors="coerce")
        df["release_year"] = df["release_date"].dt.year.fillna(df.get("release_year", 2000)).astype(int)
    else:
        df["release_date"] = pd.NaT
        df["release_year"] = pd.to_numeric(df.get("release_year", 2000), errors="coerce").fillna(2000).astype(int)

    # 5. Validation Check: Filter out rows with zero budget or empty titles
    df["title"] = df["title"].astype(str)
    df = df[df["title"].str.strip().astype(bool)]
    df = df[df["budget"] > 0]
    
    # 6. Deduplicate by title and release_year
    df = df.drop_duplicates(subset=["title", "release_year"], keep="first")

    filtered_count = len(df)
    logger.info(f"Cleaned dataset: {filtered_count} valid records out of {initial_count} raw rows.")
    return df


def process_entities_and_load(df: pd.DataFrame, engine, dry_run: bool = False):
    """Parses multi-valued attributes (genres, directors, actors) and loads into database."""
    if dry_run:
        logger.info("[DRY-RUN MODE] Data validation passed successfully. Database insertion skipped.")
        print("\nCleaned Sample Preview:")
        print(df[["title", "release_year", "budget", "revenue", "imdb_rating"]].head(5))
        return

    logger.info(f"Connecting to database via SQLAlchemy engine...")

    with engine.begin() as conn:
        for idx, row in df.iterrows():
            # Insert or get Movie
            movie_stmt = text("""
                INSERT INTO movies (title, release_year, release_date, duration_minutes, language, country, budget, revenue, domestic_revenue, international_revenue, imdb_rating, vote_count)
                VALUES (:title, :release_year, :release_date, :duration_minutes, :language, :country, :budget, :revenue, :domestic_revenue, :international_revenue, :imdb_rating, :vote_count)
                ON DUPLICATE KEY UPDATE budget = VALUES(budget), revenue = VALUES(revenue), imdb_rating = VALUES(imdb_rating);
            """)
            
            rel_date_str = row["release_date"].strftime("%Y-%m-%d") if pd.notna(row["release_date"]) else None
            
            res = conn.execute(movie_stmt, {
                "title": row["title"],
                "release_year": int(row["release_year"]),
                "release_date": rel_date_str,
                "duration_minutes": int(row["duration_minutes"]),
                "language": str(row.get("language", "English")),
                "country": str(row.get("country", "USA")),
                "budget": float(row["budget"]),
                "revenue": float(row["revenue"]),
                "domestic_revenue": float(row["domestic_revenue"]),
                "international_revenue": float(row["international_revenue"]),
                "imdb_rating": float(row["imdb_rating"]),
                "vote_count": int(row["vote_count"])
            })
            
            # Fetch inserted/existing movie_id
            movie_id = conn.execute(
                text("SELECT movie_id FROM movies WHERE title = :title AND release_year = :release_year"),
                {"title": row["title"], "release_year": int(row["release_year"])}
            ).scalar()

            # Process Genres
            if "genres" in row and pd.notna(row["genres"]):
                genres_list = [g.strip() for g in str(row["genres"]).split(",") if g.strip()]
                for genre_name in genres_list:
                    conn.execute(
                        text("INSERT IGNORE INTO genres (genre_name) VALUES (:name)"),
                        {"name": genre_name}
                    )
                    genre_id = conn.execute(
                        text("SELECT genre_id FROM genres WHERE genre_name = :name"),
                        {"name": genre_name}
                    ).scalar()
                    conn.execute(
                        text("INSERT IGNORE INTO movie_genres (movie_id, genre_id) VALUES (:m_id, :g_id)"),
                        {"m_id": movie_id, "g_id": genre_id}
                    )

            # Process Directors
            if "directors" in row and pd.notna(row["directors"]):
                directors_list = [d.strip() for d in str(row["directors"]).split(",") if d.strip()]
                for director_name in directors_list:
                    conn.execute(
                        text("INSERT IGNORE INTO directors (director_name) VALUES (:name)"),
                        {"name": director_name}
                    )
                    director_id = conn.execute(
                        text("SELECT director_id FROM directors WHERE director_name = :name"),
                        {"name": director_name}
                    ).scalar()
                    conn.execute(
                        text("INSERT IGNORE INTO movie_directors (movie_id, director_id) VALUES (:m_id, :d_id)"),
                        {"m_id": movie_id, "d_id": director_id}
                    )

            # Process Actors
            if "actors" in row and pd.notna(row["actors"]):
                actors_list = [a.strip() for a in str(row["actors"]).split(",") if a.strip()]
                for actor_name in actors_list:
                    conn.execute(
                        text("INSERT IGNORE INTO actors (actor_name) VALUES (:name)"),
                        {"name": actor_name}
                    )
                    actor_id = conn.execute(
                        text("SELECT actor_id FROM actors WHERE actor_name = :name"),
                        {"name": actor_name}
                    ).scalar()
                    conn.execute(
                        text("INSERT IGNORE INTO movie_actors (movie_id, actor_id, role_type) VALUES (:m_id, :a_id, 'Lead')"),
                        {"m_id": movie_id, "a_id": actor_id}
                    )

    logger.info("[SUCCESS] Database ingestion successfully completed!")


def main():
    parser = argparse.ArgumentParser(description="CineScope Data Ingestion & ETL Script")
    parser.add_argument("--csv", type=str, default="data/sample_movies_raw.csv", help="Path to raw CSV file")
    parser.add_argument("--db-uri", type=str, default=DEFAULT_DB_URI, help="SQLAlchemy Database URI")
    parser.add_argument("--dry-run", action="store_true", help="Validate and clean data without writing to database")
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        logger.error(f"Target CSV file not found: {args.csv}")
        sys.exit(1)

    logger.info(f"Loading raw CSV data from {args.csv}...")
    df_raw = pd.read_csv(args.csv)
    
    df_clean = validate_and_clean_data(df_raw)
    
    engine = None
    if not args.dry_run:
        try:
            engine = create_engine(args.db_uri)
        except Exception as e:
            logger.warning(f"Could not connect to MySQL database at {args.db_uri}: {e}")
            logger.warning("Switching to --dry-run mode for local verification...")
            args.dry_run = True

    process_entities_and_load(df_clean, engine, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
