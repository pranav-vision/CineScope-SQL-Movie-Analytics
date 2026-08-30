#!/usr/bin/env python3
"""
=====================================================
CineScope SQL Movie Analytics - FastAPI Service
File: api/main.py
Description: Production FastAPI backend REST service with CORS middleware,
             healthchecks, executive KPI metrics, top director analytics,
             and multi-format dataset upload endpoints.
=====================================================
"""

import sys
import os
import json
import logging
from typing import Dict, List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.db_manager import DatabaseManager
from scripts.file_parser import MultiFormatFileParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CineScopeFastAPI")

# Initialize FastAPI App
app = FastAPI(
    title="CineScope SQL — Executive Movie Analytics API",
    description="Enterprise REST API for Movie Portfolio Analytics, Risk Assessment, and Data Ingestion",
    version="1.0.0"
)

# Enable CORS for cross-origin frontend dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Engine Instance
db = DatabaseManager()


# Response Schemas
class HealthResponse(BaseModel):
    status: str
    database: str
    engine: str
    is_mysql: bool


class ExecutiveSummaryMetrics(BaseModel):
    total_movies: int
    total_budget: float
    total_revenue: float
    total_net_profit: float
    overall_roi_pct: float
    total_domestic: float
    total_international: float
    avg_rating: float


class DirectorMetric(BaseModel):
    talent_name: str
    total_projects: int
    total_revenue: float
    avg_rating: float
    avg_roi_pct: float


class UploadResponse(BaseModel):
    success: bool
    upload_id: int
    filename: str
    total_movies: int
    message: str


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Database connectivity and engine health check endpoint."""
    try:
        with db.engine.connect() as conn:
            conn.execute(db.engine.dialect.has_table and db.engine.dialect.has_table(conn, "dim_movies") and db.engine.dialect.has_table(conn, "dim_movies") or db.engine.dialect.has_table(conn, "dim_movies"))
        
        engine_type = "MySQL (Enterprise Relational DB)" if db.is_mysql else "SQLite (Local Fallback DB)"
        return {
            "status": "healthy",
            "database": "connected",
            "engine": engine_type,
            "is_mysql": db.is_mysql
        }
    except Exception as e:
        logger.error(f"Healthcheck failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")


@app.get("/api/v1/metrics/executive-summary", response_model=ExecutiveSummaryMetrics, tags=["Metrics"])
def get_executive_summary(upload_id: Optional[int] = Query(None, description="Optional Filter by Upload ID")):
    """Returns top-level executive portfolio KPI metrics."""
    try:
        data = db.get_analytics(upload_id=upload_id)
        s = data["summary"]
        return {
            "total_movies": int(s.get("total_movies", 0)),
            "total_budget": float(s.get("total_budget", 0.0)),
            "total_revenue": float(s.get("total_revenue", 0.0)),
            "total_net_profit": float(s.get("total_net_profit", 0.0)),
            "overall_roi_pct": float(s.get("overall_roi_pct", 0.0)),
            "total_domestic": float(s.get("total_domestic", 0.0)),
            "total_international": float(s.get("total_international", 0.0)),
            "avg_rating": float(s.get("avg_rating", 0.0))
        }
    except Exception as e:
        logger.error(f"Error fetching executive summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/top-directors", response_model=List[DirectorMetric], tags=["Analytics"])
def get_top_directors(upload_id: Optional[int] = Query(None, description="Optional Filter by Upload ID")):
    """Returns top 10 directors ranked by total box-office revenue."""
    try:
        data = db.get_analytics(upload_id=upload_id)
        talent_df = data["talent"]
        if talent_df.empty:
            return []
        
        directors_df = talent_df[talent_df["talent_type"] == "Director"].head(10)
        records = directors_df.to_dict(orient="records")
        return [
            {
                "talent_name": str(r["talent_name"]),
                "total_projects": int(r["total_projects"]),
                "total_revenue": float(r["total_revenue"]),
                "avg_rating": float(r.get("avg_rating", 0.0)),
                "avg_roi_pct": float(r.get("avg_roi_pct", 0.0))
            }
            for r in records
        ]
    except Exception as e:
        logger.error(f"Error fetching top directors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analytics/upload", response_model=UploadResponse, tags=["Ingestion"])
async def upload_dataset(file: UploadFile = File(...)):
    """Uploads, parses (CSV/Excel/JSON), normalizes, and ingests a movie dataset."""
    filename = file.filename or "uploaded_dataset.csv"
    file_ext = filename.split(".")[-1].lower()

    if file_ext not in ["csv", "xlsx", "xls", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported format. Only CSV, Excel (.xlsx/.xls), and JSON are supported.")

    try:
        content = await file.read()
        saved_path = MultiFormatFileParser.save_uploaded_file(content, filename)
        cleaned_df = MultiFormatFileParser.parse_file(saved_path, file_ext)
        total_movies = len(cleaned_df)

        upload_id = db.log_dataset_upload(filename, saved_path, file_ext.upper(), total_movies)
        db.insert_normalized_dataset(cleaned_df, upload_id)

        return {
            "success": True,
            "upload_id": upload_id,
            "filename": filename,
            "total_movies": total_movies,
            "message": f"Successfully loaded {total_movies} records under Upload #{upload_id}"
        }
    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Data ingestion failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
