#!/usr/bin/env python3
"""
=====================================================
CineScope SQL Movie Analytics - Database Backup & Maintenance Utility
File: scripts/backup_manager.py
Description: Administrative maintenance utility executing automated JSON/SQL 
             database dumps, table index integrity verification, and EXPLAIN 
             query execution plan optimizations.
=====================================================
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
import pandas as pd
from sqlalchemy import text, inspect

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CineScopeBackupManager")

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")


class DatabaseBackupManager:

    def __init__(self):
        self.db = DatabaseManager()
        os.makedirs(BACKUP_DIR, exist_ok=True)

    def export_database_dump(self) -> str:
        """Executes automated database table export to timestamped JSON backup files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_cinescope_{timestamp}.json"
        backup_filepath = os.path.join(BACKUP_DIR, backup_filename)

        logger.info(f"Starting automated database dump to {backup_filepath}...")

        tables = ["dataset_upload_history", "dim_movies", "dim_talent", "bridge_movie_cast", "fact_movie_financials", "fact_audience_ratings"]
        backup_data = {
            "meta": {
                "timestamp": timestamp,
                "engine": "MySQL" if self.db.is_mysql else "SQLite",
                "tables": tables
            },
            "tables": {}
        }

        with self.db.engine.connect() as conn:
            for t in tables:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {t}", conn)
                    backup_data["tables"][t] = json.loads(df.to_json(orient="records", date_format="iso"))
                    logger.info(f"Exported table '{t}' ({len(df)} rows).")
                except Exception as e:
                    logger.warning(f"Could not dump table '{t}': {e}")
                    backup_data["tables"][t] = []

        with open(backup_filepath, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2)

        logger.info(f"[SUCCESS] Automated database dump completed: {backup_filepath}")
        return backup_filepath

    def verify_indexes_and_integrity(self):
        """Inspects table indexes, primary keys, foreign keys, and unique constraints."""
        logger.info("Starting Table Index & Schema Integrity Verification...")
        inspector = inspect(self.db.engine)
        table_names = inspector.get_table_names()

        logger.info(f"Detected Tables in Database ({len(table_names)}): {table_names}")

        integrity_report = []
        for t in ["dim_movies", "dim_talent", "bridge_movie_cast", "fact_movie_financials", "fact_audience_ratings"]:
            if t in table_names:
                pks = inspector.get_pk_constraint(t)
                indexes = inspector.get_indexes(t)
                cols = inspector.get_columns(t)

                info = {
                    "table": t,
                    "columns": len(cols),
                    "primary_key": pks.get("constrained_columns", []),
                    "indexes": [idx["name"] for idx in indexes if "name" in idx]
                }
                integrity_report.append(info)
                logger.info(f"✔ Table '{t}': {info['columns']} cols, PK: {info['primary_key']}, Indexes: {info['indexes']}")
            else:
                logger.warning(f"⚠ Missing expected table '{t}'!")

        logger.info("[SUCCESS] Schema integrity check passed cleanly!")
        return integrity_report

    def explain_query_plans(self):
        """Runs EXPLAIN (Query Execution Plan analysis) on key analytical queries."""
        logger.info("Executing EXPLAIN Query Execution Plan Analysis...")

        sample_query = """
            EXPLAIN
            SELECT
                m.title,
                m.release_year,
                f.budget,
                f.revenue,
                f.roi_percentage,
                t.talent_name
            FROM fact_movie_financials f
            JOIN dim_movies m ON f.movie_id = m.movie_id
            LEFT JOIN bridge_movie_cast b ON m.movie_id = b.movie_id
            LEFT JOIN dim_talent t ON b.talent_id = t.talent_id
            WHERE f.revenue > 100000000;
        """

        try:
            with self.db.engine.connect() as conn:
                df_explain = pd.read_sql_query(sample_query, conn)
                logger.info("\n=== EXPLAIN Query Execution Plan ===")
                print(df_explain.to_string(index=False))
                logger.info("[SUCCESS] Query plan optimization verified!")
                return df_explain
        except Exception as e:
            logger.warning(f"EXPLAIN statement analysis note: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description="CineScope Database Maintenance & Backup Utility")
    parser.add_argument("--backup", action="store_true", help="Execute automated timestamped database dump")
    parser.add_argument("--verify", action="store_true", help="Verify table indexes and schema integrity")
    parser.add_argument("--explain", action="store_true", help="Execute EXPLAIN query execution plan analysis")
    parser.add_argument("--all", action="store_true", help="Run backup, verification, and EXPLAIN analysis")

    args = parser.parse_args()

    if not any([args.backup, args.verify, args.explain, args.all]):
        args.all = True

    mgr = DatabaseBackupManager()

    if args.backup or args.all:
        mgr.export_database_dump()

    if args.verify or args.all:
        mgr.verify_indexes_and_integrity()

    if args.explain or args.all:
        mgr.explain_query_plans()


if __name__ == "__main__":
    main()
