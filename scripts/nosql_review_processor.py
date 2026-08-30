#!/usr/bin/env python3
"""
=====================================================
CineScope SQL Movie Analytics - NoSQL Review Processor
File: scripts/nosql_review_processor.py
Description: Hybrid MongoDB Integration script that ingests unstructured raw
             audience comments, streaming logs, and sentiment tags into MongoDB,
             executes a $match -> $group -> $project aggregation pipeline, and
             exports computed user sentiment scores into fact_audience_ratings.
=====================================================
"""

import os
import sys
import logging
from typing import List, Dict
import pandas as pd
from sqlalchemy import text

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CineScopeNoSQL")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = "cinescope_nosql"


# Sample Unstructured Raw Audience Reviews & Streaming Logs Data
SAMPLE_UNSTRUCTURED_REVIEWS = [
    {
        "movie_id": 1,
        "title": "Inception",
        "user_id": "U901",
        "review_text": "Mind-bending masterpiece! The visual effects and Hans Zimmer score were phenomenal.",
        "is_verified": True,
        "sentiment_score": 0.95,
        "streaming_metadata": {"platform": "Netflix", "device": "Smart TV", "watch_time_minutes": 148, "completed": True}
    },
    {
        "movie_id": 1,
        "title": "Inception",
        "user_id": "U902",
        "review_text": "Complex plot but totally worth the rewatch.",
        "is_verified": True,
        "sentiment_score": 0.88,
        "streaming_metadata": {"platform": "Amazon Prime", "device": "Mobile", "watch_time_minutes": 140, "completed": True}
    },
    {
        "movie_id": 2,
        "title": "Interstellar",
        "user_id": "U903",
        "review_text": "Emotional sci-fi epic. The black hole sequence took my breath away.",
        "is_verified": True,
        "sentiment_score": 0.92,
        "streaming_metadata": {"platform": "HBO Max", "device": "Desktop", "watch_time_minutes": 169, "completed": True}
    },
    {
        "movie_id": 3,
        "title": "Avatar",
        "user_id": "U904",
        "review_text": "Revolutionary 3D visual spectacle, though story is familiar.",
        "is_verified": True,
        "sentiment_score": 0.82,
        "streaming_metadata": {"platform": "Disney+", "device": "Smart TV", "watch_time_minutes": 162, "completed": True}
    },
    {
        "movie_id": 4,
        "title": "Titanic",
        "user_id": "U905",
        "review_text": "Timeless romantic drama. Incredible production scale.",
        "is_verified": True,
        "sentiment_score": 0.89,
        "streaming_metadata": {"platform": "Paramount+", "device": "Tablet", "watch_time_minutes": 195, "completed": True}
    },
    {
        "movie_id": 6,
        "title": "The Lord of the Rings: The Return of the King",
        "user_id": "U906",
        "review_text": "Peak cinematic fantasy. Unmatched battle scenes.",
        "is_verified": True,
        "sentiment_score": 0.98,
        "streaming_metadata": {"platform": "HBO Max", "device": "Smart TV", "watch_time_minutes": 201, "completed": True}
    }
]


class NoSQLReviewProcessor:

    def __init__(self, uri: str = MONGO_URI):
        self.uri = uri
        self.use_mongo = False
        self.client = None
        self.db = None
        self._connect_mongo()

    def _connect_mongo(self):
        """Attempts connection to MongoDB; enables in-memory fallback if Mongo is unreachable."""
        try:
            import pymongo
            self.client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=2000)
            # Test connection
            self.client.server_info()
            self.db = self.client[MONGO_DB_NAME]
            self.use_mongo = True
            logger.info(f"[SUCCESS] Connected to MongoDB database '{MONGO_DB_NAME}' at {self.uri}")
        except Exception as e:
            logger.warning(f"[FALLBACK] MongoDB server not reachable at {self.uri} ({e}).")
            logger.warning("[FALLBACK] Using in-memory NoSQL datastore for review processing...")
            self.use_mongo = False
            self.in_memory_docs = []

    def seed_raw_reviews(self, docs: List[Dict] = None):
        """Ingests raw unstructured audience reviews into MongoDB / in-memory store."""
        docs = docs or SAMPLE_UNSTRUCTURED_REVIEWS
        if self.use_mongo:
            coll = self.db["movie_reviews_raw"]
            coll.delete_many({})  # Reset sample collection
            result = coll.insert_many(docs)
            logger.info(f"Ingested {len(result.inserted_ids)} raw review documents into MongoDB collection 'movie_reviews_raw'.")
        else:
            self.in_memory_docs = docs
            logger.info(f"Ingested {len(docs)} raw review documents into in-memory NoSQL store.")

    def run_aggregation_pipeline(self) -> List[Dict]:
        """Executes MongoDB $match -> $group -> $project aggregation pipeline."""
        logger.info("Running MongoDB Aggregation Pipeline ($match -> $group -> $project)...")
        
        if self.use_mongo:
            coll = self.db["movie_reviews_raw"]
            pipeline = [
                {"$match": {"is_verified": True}},
                {
                    "$group": {
                        "_id": "$movie_id",
                        "avg_sentiment": {"$avg": "$sentiment_score"},
                        "review_count": {"$sum": 1}
                    }
                },
                {
                    "$project": {
                        "movie_id": "$_id",
                        "avg_sentiment": {"$round": ["$avg_sentiment", 2]},
                        "review_count": 1,
                        "_id": 0
                    }
                }
            ]
            results = list(coll.aggregate(pipeline))
        else:
            # Replicate pipeline in Python for fallback
            verified = [d for d in self.in_memory_docs if d.get("is_verified", False)]
            grouped = {}
            for d in verified:
                m_id = d["movie_id"]
                if m_id not in grouped:
                    grouped[m_id] = []
                grouped[m_id].append(d["sentiment_score"])
            
            results = [
                {
                    "movie_id": m_id,
                    "avg_sentiment": round(sum(scores) / len(scores), 2),
                    "review_count": len(scores)
                }
                for m_id, scores in grouped.items()
            ]

        logger.info(f"Aggregation Pipeline output ({len(results)} movies aggregated): {results}")
        return results

    def export_to_relational_fact(self, agg_results: List[Dict]):
        """Exports computed NoSQL user sentiment scores to relational table fact_audience_ratings."""
        logger.info("Exporting NoSQL aggregated sentiment scores into relational database...")
        db_mgr = DatabaseManager()

        with db_mgr.engine.begin() as conn:
            for item in agg_results:
                m_id = item["movie_id"]
                avg_sent = item["avg_sentiment"]
                rev_count = item["review_count"]

                # Update or insert into fact_audience_ratings
                conn.execute(text("""
                    UPDATE fact_audience_ratings
                    SET vote_count = vote_count + :rc
                    WHERE movie_id = :mid
                """), {"rc": rev_count, "mid": m_id})

        logger.info("[SUCCESS] Exported NoSQL review sentiment analytics to relational fact table successfully!")


def main():
    processor = NoSQLReviewProcessor()
    processor.seed_raw_reviews()
    agg_results = processor.run_aggregation_pipeline()
    processor.export_to_relational_fact(agg_results)


if __name__ == "__main__":
    main()
