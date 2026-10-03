#!/usr/bin/env python3
"""
=====================================================
CineScope SQL Movie Analytics - Database Manager Engine
File: scripts/db_manager.py
Description: Manages MySQL & fallback SQLite connections,
              dynamic DB creation, upload history tracking,
              relational table normalization, and analytics queries.
=====================================================
"""

import os
import sys
import logging
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("CineScopeDBManager")

# Connection Configs
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DB = os.getenv("MYSQL_DB", "cine_scope_db")

MYSQL_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
SQLITE_FALLBACK_URI = "sqlite:///cinescope_analytics.db"


class DatabaseManager:

    def __init__(self, db_uri: str = None):
        self.db_uri = db_uri or MYSQL_URI
        self.is_mysql = "mysql" in self.db_uri
        self.engine = self._connect_or_fallback()
        self.init_tables()

    def _connect_or_fallback(self):
        """Attempts connection to MySQL; automatically creates DB or falls back to SQLite."""
        if self.is_mysql:
            try:
                # 1. Try connecting to MySQL server root to ensure database exists
                server_uri = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}"
                temp_engine = create_engine(server_uri)
                with temp_engine.connect() as conn:
                    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}`"))
                    conn.commit()
                
                engine = create_engine(self.db_uri)
                with engine.connect() as conn:
                    # FIXED: Wrapped query inside text() for SQLAlchemy 2.0 compatibility
                    conn.execute(text("SELECT 1"))
                logger.info(f"[SUCCESS] Connected to MySQL database '{MYSQL_DB}' successfully.")
                return engine
            except Exception as e:
                logger.warning(f"[WARNING] Could not connect to MySQL at {self.db_uri}: {e}")
                logger.warning("[FALLBACK] Switching to local SQLite database engine (cinescope_analytics.db)...")
                self.is_mysql = False
                return create_engine(SQLITE_FALLBACK_URI)
        else:
            return create_engine(self.db_uri)

    def init_tables(self):
        """Initializes dataset upload history and relational tables."""
        pk_auto = "INT AUTO_INCREMENT PRIMARY KEY" if self.is_mysql else "INTEGER PRIMARY KEY AUTOINCREMENT"
        ts_type = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if self.is_mysql else "DATETIME DEFAULT CURRENT_TIMESTAMP"

        with self.engine.begin() as conn:
            # 1. Dataset Upload History Table
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS dataset_upload_history (
                    upload_id {pk_auto},
                    file_name VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_type VARCHAR(50) NOT NULL,
                    uploaded_at {ts_type},
                    total_movies INT DEFAULT 0,
                    status VARCHAR(50) DEFAULT 'PROCESSED'
                );
            """))

            # 2. Dim Movies
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS dim_movies (
                    movie_id {pk_auto},
                    title VARCHAR(255) NOT NULL,
                    release_year INT,
                    release_date VARCHAR(20),
                    duration_minutes INT,
                    language VARCHAR(100),
                    country VARCHAR(100),
                    CONSTRAINT uq_title_year UNIQUE (title, release_year)
                );
            """))

            # 3. Dim Talent
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS dim_talent (
                    talent_id {pk_auto},
                    talent_name VARCHAR(255) NOT NULL,
                    talent_type VARCHAR(100) DEFAULT 'Talent',
                    CONSTRAINT uq_talent_name UNIQUE (talent_name)
                );
            """))

            # 4. Bridge Movie Cast
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS bridge_movie_cast (
                    movie_id INT,
                    talent_id INT,
                    role_type VARCHAR(100) DEFAULT 'Lead',
                    PRIMARY KEY (movie_id, talent_id, role_type)
                );
            """))

            # 5. Fact Movie Financials
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS fact_movie_financials (
                    financial_id {pk_auto},
                    movie_id INT,
                    upload_id INT,
                    budget DECIMAL(15, 2),
                    revenue DECIMAL(15, 2),
                    domestic_revenue DECIMAL(15, 2),
                    international_revenue DECIMAL(15, 2),
                    net_profit DECIMAL(15, 2),
                    roi_percentage DECIMAL(10, 2)
                );
            """))

            # 6. Fact Audience Ratings
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS fact_audience_ratings (
                    rating_id {pk_auto},
                    movie_id INT,
                    upload_id INT,
                    imdb_rating DECIMAL(3, 1),
                    vote_count INT,
                    sentiment_tier VARCHAR(100)
                );
            """))

    def log_dataset_upload(self, file_name: str, file_path: str, file_type: str, total_movies: int) -> int:
        """Logs a new file upload in dataset_upload_history and returns its upload_id."""
        with self.engine.begin() as conn:
            stmt = text("""
                INSERT INTO dataset_upload_history (file_name, file_path, file_type, total_movies, status)
                VALUES (:name, :path, :type, :total, 'PROCESSED')
            """)
            conn.execute(stmt, {
                "name": file_name,
                "path": file_path,
                "type": file_type,
                "total": total_movies
            })
            
            # Fetch last inserted ID
            upload_id = conn.execute(text("SELECT MAX(upload_id) FROM dataset_upload_history")).scalar()
            return upload_id or 1

    def get_upload_history(self) -> pd.DataFrame:
        """Retrieves all uploaded datasets history."""
        query = "SELECT upload_id, file_name, file_type, uploaded_at, total_movies, status FROM dataset_upload_history ORDER BY upload_id DESC"
        return pd.read_sql_query(query, self.engine)

    def insert_normalized_dataset(self, df: pd.DataFrame, upload_id: int):
        """Normalizes parsed dataframe into relational dimensions and facts."""
        ign = "IGNORE" if self.is_mysql else "OR IGNORE"

        with self.engine.begin() as conn:
            for idx, row in df.iterrows():
                title = str(row["title"]).strip()
                rel_year = int(row.get("release_year", 2000))
                rel_date = str(row.get("release_date", ""))[:10] if pd.notna(row.get("release_date")) else None
                duration = int(row.get("duration_minutes", 0))
                lang = str(row.get("language", "English"))
                country = str(row.get("country", "USA"))

                # 1. Insert / Get Movie
                conn.execute(text(f"""
                    INSERT {ign} INTO dim_movies (title, release_year, release_date, duration_minutes, language, country)
                    VALUES (:t, :y, :d, :dur, :l, :c)
                """), {"t": title, "y": rel_year, "d": rel_date, "dur": duration, "l": lang, "c": country})

                movie_id = conn.execute(
                    text("SELECT movie_id FROM dim_movies WHERE title = :t AND release_year = :y"),
                    {"t": title, "y": rel_year}
                ).scalar()

                if not movie_id:
                    continue

                # 2. Financials
                budget = float(row.get("budget", 0.0))
                revenue = float(row.get("revenue", 0.0))
                dom_rev = float(row.get("domestic_revenue", revenue * 0.4))
                int_rev = float(row.get("international_revenue", revenue * 0.6))
                net_profit = revenue - budget
                roi_pct = ((revenue - budget) / budget * 100) if budget > 0 else 0.0

                conn.execute(text("""
                    INSERT INTO fact_movie_financials (movie_id, upload_id, budget, revenue, domestic_revenue, international_revenue, net_profit, roi_percentage)
                    VALUES (:m_id, :u_id, :b, :r, :dr, :ir, :np, :roi)
                """), {
                    "m_id": movie_id, "u_id": upload_id, "b": budget, "r": revenue,
                    "dr": dom_rev, "ir": int_rev, "np": net_profit, "roi": roi_pct
                })

                # 3. Ratings
                rating = float(row.get("imdb_rating", 0.0))
                votes = int(row.get("vote_count", 0))
                tier = "Masterpiece (8.5+)" if rating >= 8.5 else "Acclaimed (8.0-8.4)" if rating >= 8.0 else "Positive (7.0-7.9)" if rating >= 7.0 else "Mixed (<7.0)"

                conn.execute(text("""
                    INSERT INTO fact_audience_ratings (movie_id, upload_id, imdb_rating, vote_count, sentiment_tier)
                    VALUES (:m_id, :u_id, :rat, :v, :st)
                """), {"m_id": movie_id, "u_id": upload_id, "rat": rating, "v": votes, "st": tier})

                # 4. Directors & Actors Talent Normalization
                directors = [d.strip() for d in str(row.get("directors", "")).split(",") if d.strip() and d.lower() != "nan"]
                for d_name in directors:
                    conn.execute(text(f"INSERT {ign} INTO dim_talent (talent_name, talent_type) VALUES (:t_name, 'Director')"), {"t_name": d_name})
                    t_id = conn.execute(text("SELECT talent_id FROM dim_talent WHERE talent_name = :t_name"), {"t_name": d_name}).scalar()
                    if t_id:
                        conn.execute(text(f"INSERT {ign} INTO bridge_movie_cast (movie_id, talent_id, role_type) VALUES (:m, :t, 'Director')"), {"m": movie_id, "t": t_id})

                actors = [a.strip() for a in str(row.get("actors", "")).split(",") if a.strip() and a.lower() != "nan"]
                for a_name in actors:
                    conn.execute(text(f"INSERT {ign} INTO dim_talent (talent_name, talent_type) VALUES (:t_name, 'Actor')"), {"t_name": a_name})
                    t_id = conn.execute(text("SELECT talent_id FROM dim_talent WHERE talent_name = :t_name"), {"t_name": a_name}).scalar()
                    if t_id:
                        conn.execute(text(f"INSERT {ign} INTO bridge_movie_cast (movie_id, talent_id, role_type) VALUES (:m, :t, 'Lead Actor')"), {"m": movie_id, "t": t_id})

    def get_analytics(self, upload_id: int = None) -> dict:
        """Runs executive analytical queries filtered by upload_id."""
        filter_clause = f"WHERE f.upload_id = {upload_id}" if upload_id else ""

        with self.engine.connect() as conn:
            # Summary KPI
            summary_q = f"""
                SELECT
                    COUNT(DISTINCT f.movie_id) AS total_movies,
                    COALESCE(SUM(f.budget), 0) AS total_budget,
                    COALESCE(SUM(f.revenue), 0) AS total_revenue,
                    COALESCE(SUM(f.net_profit), 0) AS total_net_profit,
                    COALESCE(ROUND((SUM(f.net_profit) / NULLIF(SUM(f.budget), 0)) * 100, 2), 0) AS overall_roi_pct,
                    COALESCE(SUM(f.domestic_revenue), 0) AS total_domestic,
                    COALESCE(SUM(f.international_revenue), 0) AS total_international,
                    COALESCE(ROUND(AVG(r.imdb_rating), 2), 0) AS avg_rating
                FROM fact_movie_financials f
                LEFT JOIN fact_audience_ratings r ON f.movie_id = r.movie_id AND f.upload_id = r.upload_id
                {filter_clause};
            """
            summary = pd.read_sql_query(summary_q, conn).to_dict(orient="records")[0]

            # Movies Financials Table
            movies_q = f"""
                SELECT
                    m.title,
                    m.release_year,
                    f.budget,
                    f.revenue,
                    f.net_profit,
                    f.roi_percentage,
                    r.imdb_rating,
                    CASE
                        WHEN f.roi_percentage >= 400 THEN 'Blockbuster (4x+)'
                        WHEN f.roi_percentage >= 100 THEN 'Profitable (1x-4x)'
                        WHEN f.roi_percentage >= 0 THEN 'Broke Even (0x-1x)'
                        ELSE 'Flop (<0x)'
                    END AS profitability_tier
                FROM fact_movie_financials f
                JOIN dim_movies m ON f.movie_id = m.movie_id
                LEFT JOIN fact_audience_ratings r ON f.movie_id = r.movie_id AND f.upload_id = r.upload_id
                {filter_clause}
                ORDER BY f.revenue DESC;
            """
            movies = pd.read_sql_query(movies_q, conn)

            # Talent (Directors & Actors) Performance
            talent_q = f"""
                SELECT
                    t.talent_name,
                    t.talent_type,
                    COUNT(DISTINCT f.movie_id) AS total_projects,
                    SUM(f.revenue) AS total_revenue,
                    ROUND(AVG(r.imdb_rating), 2) AS avg_rating,
                    ROUND(AVG(f.roi_percentage), 2) AS avg_roi_pct
                FROM dim_talent t
                JOIN bridge_movie_cast b ON t.talent_id = b.talent_id
                JOIN fact_movie_financials f ON b.movie_id = f.movie_id
                LEFT JOIN fact_audience_ratings r ON f.movie_id = r.movie_id AND f.upload_id = r.upload_id
                {filter_clause}
                GROUP BY t.talent_id, t.talent_name, t.talent_type
                ORDER BY total_revenue DESC;
            """
            talent = pd.read_sql_query(talent_q, conn)

            # Time Series YoY
            time_series_q = f"""
                SELECT
                    m.release_year,
                    SUM(f.budget) AS budget,
                    SUM(f.revenue) AS revenue
                FROM fact_movie_financials f
                JOIN dim_movies m ON f.movie_id = m.movie_id
                {filter_clause}
                GROUP BY m.release_year
                ORDER BY m.release_year ASC;
            """
            time_series = pd.read_sql_query(time_series_q, conn)

            return {
                "summary": summary,
                "movies": movies,
                "talent": talent,
                "time_series": time_series
            }