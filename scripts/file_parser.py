#!/usr/bin/env python3
"""
=====================================================
CineScope SQL Movie Analytics - File Parser Engine
File: scripts/file_parser.py
Description: Multi-format file uploader parser for CSV, Excel (.xlsx/.xls), 
             and JSON files. Supports single-sheet flat files and 
             multi-sheet Relational Datasets (dim_movies, dim_talent, 
             bridge_movie_cast, fact_movie_financials, fact_audience_ratings).
=====================================================
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Tuple, Dict
import pandas as pd

logger = logging.getLogger("CineScopeFileParser")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def clean_currency_val(val) -> float:
    """Strips currency symbols ($), commas, and spaces, returning float."""
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = re.sub(r"[^\d.]", "", str(val))
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


class MultiFormatFileParser:

    @staticmethod
    def save_uploaded_file(uploaded_file, filename: str) -> str:
        """Saves the uploaded file to data/ directory with a timestamp prefix."""
        os.makedirs(DATA_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_name = re.sub(r"[^\w\-.]", "_", filename)
        saved_filename = f"upload_{timestamp}_{sanitized_name}"
        saved_filepath = os.path.join(DATA_DIR, saved_filename)

        with open(saved_filepath, "wb") as f:
            if isinstance(uploaded_file, bytes):
                f.write(uploaded_file)
            elif hasattr(uploaded_file, "getbuffer"):
                f.write(uploaded_file.getbuffer())
            elif hasattr(uploaded_file, "read"):
                f.write(uploaded_file.read())
            else:
                f.write(uploaded_file)

        return saved_filepath

    @staticmethod
    def parse_file(file_path: str, file_type: str) -> pd.DataFrame:
        """Reads CSV, Excel (single/multi-sheet), or JSON files into a normalized DataFrame."""
        file_ext = file_type.lower().strip(".")

        if file_ext == "csv":
            df = pd.read_csv(file_path)
            return MultiFormatFileParser.normalize_schema(df)

        elif file_ext in ["xlsx", "xls"]:
            excel_sheets = pd.read_excel(file_path, sheet_name=None)
            if isinstance(excel_sheets, dict) and len(excel_sheets) > 1:
                df = MultiFormatFileParser.merge_relational_sheets(excel_sheets)
                return MultiFormatFileParser.normalize_schema(df)
            else:
                df = pd.read_excel(file_path)
                return MultiFormatFileParser.normalize_schema(df)

        elif file_ext == "json":
            try:
                df = pd.read_json(file_path)
            except Exception:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    data = data.get("movies", data.get("data", [data]))
                df = pd.DataFrame(data)
            return MultiFormatFileParser.normalize_schema(df)

        else:
            raise ValueError(f"Unsupported file format: {file_type}")

    @staticmethod
    def merge_relational_sheets(sheets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Merges multi-sheet relational blueprint (dim_movies, dim_talent, bridge_movie_cast, fact_movie_financials, fact_audience_ratings)."""
        logger.info(f"Parsing multi-sheet Excel relational dataset: {list(sheets.keys())}")
        
        # Clean sheet names
        clean_sheets = {str(k).lower().strip(): v for k, v in sheets.items()}

        df_movies = clean_sheets.get("dim_movies", pd.DataFrame())
        df_talent = clean_sheets.get("dim_talent", pd.DataFrame())
        df_bridge = clean_sheets.get("bridge_movie_cast", pd.DataFrame())
        df_fin = clean_sheets.get("fact_movie_financials", pd.DataFrame())
        df_ratings = clean_sheets.get("fact_audience_ratings", pd.DataFrame())

        if df_movies.empty:
            # Fallback to first available sheet
            first_key = list(sheets.keys())[0]
            return sheets[first_key]

        merged = df_movies.copy()

        # Merge Financials
        if not df_fin.empty and "movie_id" in df_fin.columns:
            merged = pd.merge(merged, df_fin, on="movie_id", how="left")

        # Merge Ratings
        if not df_ratings.empty and "movie_id" in df_ratings.columns:
            merged = pd.merge(merged, df_ratings, on="movie_id", how="left")

        # Merge Directors & Actors from Talent and Bridge
        if not df_bridge.empty and not df_talent.empty and "movie_id" in df_bridge.columns and "person_id" in df_talent.columns:
            cast_merged = pd.merge(df_bridge, df_talent, on="person_id", how="left")
            
            # Extract Directors
            directors_df = cast_merged[cast_merged["role_in_movie"].str.lower().str.contains("director", na=False)]
            directors_grouped = directors_df.groupby("movie_id")["full_name"].apply(lambda names: ", ".join(names.dropna().unique())).reset_index()
            directors_grouped.columns = ["movie_id", "directors"]
            merged = pd.merge(merged, directors_grouped, on="movie_id", how="left")

            # Extract Actors
            actors_df = cast_merged[cast_merged["role_in_movie"].str.lower().str.contains("actor|star|lead", na=False)]
            actors_grouped = actors_df.groupby("movie_id")["full_name"].apply(lambda names: ", ".join(names.dropna().unique())).reset_index()
            actors_grouped.columns = ["movie_id", "actors"]
            merged = pd.merge(merged, actors_grouped, on="movie_id", how="left")

        return merged

    @staticmethod
    def normalize_schema(df: pd.DataFrame) -> pd.DataFrame:
        """Flexible column name mapping and cleaning for single-table and relational datasets."""
        col_map = {}
        for col in df.columns:
            clean_col = str(col).lower().strip().replace(" ", "_")
            if clean_col in ["title", "movie_title", "film_title", "name", "movie"]:
                col_map[col] = "title"
            elif clean_col in ["release_year", "year", "year_released"]:
                col_map[col] = "release_year"
            elif clean_col in ["release_date", "date", "released"]:
                col_map[col] = "release_date"
            elif clean_col in ["duration_minutes", "runtime_minutes", "duration", "runtime", "length"]:
                col_map[col] = "duration_minutes"
            elif clean_col in ["language", "original_language", "lang"]:
                col_map[col] = "language"
            elif clean_col in ["country", "location", "origin_country"]:
                col_map[col] = "country"
            elif clean_col in ["budget", "production_budget", "production_budget_usd", "cost"]:
                col_map[col] = "budget"
            elif clean_col in ["revenue", "gross", "world_gross", "global_revenue", "box_office"]:
                col_map[col] = "revenue"
            elif clean_col in ["domestic_revenue", "domestic_revenue_usd", "domestic_gross", "us_gross"]:
                col_map[col] = "domestic_revenue"
            elif clean_col in ["international_revenue", "international_revenue_usd", "overseas_gross", "int_gross"]:
                col_map[col] = "international_revenue"
            elif clean_col in ["streaming_rights_revenue_usd", "streaming_revenue"]:
                col_map[col] = "streaming_revenue"
            elif clean_col in ["imdb_rating", "rating", "imdb_score", "score"]:
                col_map[col] = "imdb_rating"
            elif clean_col in ["vote_count", "votes", "num_votes"]:
                col_map[col] = "vote_count"
            elif clean_col in ["genres", "primary_genre", "genre"]:
                col_map[col] = "genres"
            elif clean_col in ["directors", "director"]:
                col_map[col] = "directors"
            elif clean_col in ["actors", "actor", "cast", "stars"]:
                col_map[col] = "actors"

        df = df.rename(columns=col_map)

        if "title" not in df.columns:
            raise KeyError("Uploaded dataset must contain a 'title' or 'movie' column.")

        # Clean Currency & Financials
        fin_cols = ["budget", "revenue", "domestic_revenue", "international_revenue", "streaming_revenue"]
        for c in fin_cols:
            if c in df.columns:
                df[c] = df[c].apply(clean_currency_val)
            else:
                df[c] = 0.0

        # Calculate Total Revenue if split revenue columns exist
        df["revenue"] = df.apply(
            lambda r: r["revenue"] if r["revenue"] > 0 else (r["domestic_revenue"] + r["international_revenue"] + r.get("streaming_revenue", 0.0)),
            axis=1
        )

        df["imdb_rating"] = pd.to_numeric(df.get("imdb_rating", 7.5), errors="coerce").fillna(7.5)
        df["vote_count"] = pd.to_numeric(df.get("vote_count", 1000), errors="coerce").fillna(1000)
        df["duration_minutes"] = pd.to_numeric(df.get("duration_minutes", 120), errors="coerce").fillna(120)

        # Bulletproof Release Date and Year Handling
        if "release_date" in df.columns and pd.notna(df["release_date"]).any():
            parsed_dates = pd.to_datetime(df["release_date"], format="mixed", errors="coerce")
            df["release_date"] = parsed_dates
            derived_years = parsed_dates.dt.year
            if "release_year" in df.columns:
                df["release_year"] = pd.to_numeric(df["release_year"], errors="coerce").fillna(derived_years).fillna(2000).astype(int)
            else:
                df["release_year"] = derived_years.fillna(2000).astype(int)
        elif "release_year" in df.columns:
            df["release_year"] = pd.to_numeric(df["release_year"], errors="coerce").fillna(2000).astype(int)
            df["release_date"] = pd.NaT
        else:
            df["release_date"] = pd.NaT
            df["release_year"] = 2000

        df["title"] = df["title"].astype(str)
        df = df[df["title"].str.strip().astype(bool)]
        df = df.drop_duplicates(subset=["title", "release_year"], keep="first")

        return df
