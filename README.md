# CineScope SQL — Full-Stack Movie Analytics Platform

![Python](https://img.shields.io/badge/Python-Full--Stack-blue?style=for-the-badge&logo=python)
![MySQL](https://img.shields.io/badge/MySQL-SQLAlchemy%20%26%20PyMySQL-orange?style=for-the-badge&logo=mysql)
![Power BI](https://img.shields.io/badge/Analytics-Power%20BI%20%26%20Chart.js-yellow?style=for-the-badge&logo=powerbi)
![Formats](https://img.shields.io/badge/Ingestion-CSV%20%7C%20Excel%20%7C%20JSON-green?style=for-the-badge)

---

## 🎬 Project Overview & Core System Goal

**CineScope SQL** is an interactive, end-to-end MySQL-backed analytics platform designed for streaming platforms (e.g., Netflix, Amazon Prime Video) and production houses.

### Key Upgraded System Capabilities:
1. **Interactive Dashboard Home**: Primary landing screen featuring KPI summary metrics, financial ROI charts, territory split breakdown, talent box-office yields, and movie profitability tier distributions.
2. **Multi-Format Dataset Ingestion**: Drag-and-drop or upload new movie datasets in **CSV, Excel (`.xlsx` / `.xls`), or JSON** formats.
3. **Relational Data Normalization**: Parsed datasets are sanitized, normalized, and populated into relational schema tables (`dim_movies`, `dim_talent`, `bridge_movie_cast`, `fact_movie_financials`, `fact_audience_ratings`).
4. **Dataset Upload History & Management Hub**: Lists all previously uploaded datasets (upload timestamps, total rows, file format, status) with one-click dataset selection to re-run/trigger analytics on specific uploads.
5. **Persistent Navigation**: Quick navigation bar with a **"Back to Home / Dashboard"** button across all screens.
6. **SQL Query & Table Explorer**: Live interactive inspector for all database tables.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Multi-Format Ingestion
        A[CSV File] -->|scripts/file_parser.py| D[Schema Mapping & Normalization]
        B[Excel File .xlsx/.xls] -->|scripts/file_parser.py| D
        C[JSON File .json] -->|scripts/file_parser.py| D
    end

    D -->|Raw File Saved| E[data/upload_timestamp_file]
    D -->|Parsed DataFrame| F[scripts/db_manager.py]

    subgraph Relational MySQL Engine
        F -->|Log Upload| G[dataset_upload_history]
        F -->|Normalize & Insert| H[dim_movies]
        F -->|Normalize & Insert| I[dim_talent]
        F -->|Normalize & Insert| J[bridge_movie_cast]
        F -->|Normalize & Insert| K[fact_movie_financials]
        F -->|Normalize & Insert| L[fact_audience_ratings]
    end

    subgraph Web Platform UI
        G & H & I & J & K & L -->|Analytics API| M[Executive Dashboard Home]
        G -->|History API| N[Dataset History & File Management Hub]
        H & I & J & K & L -->|Table Inspector| O[SQL Query Explorer]
    end
```

---

## 🗄️ Relational Database Schema (ERD)

```mermaid
erDiagram
    dataset_upload_history {
        int upload_id PK
        string file_name
        string file_path
        string file_type
        timestamp uploaded_at
        int total_movies
        string status
    }

    dim_movies ||--o{ bridge_movie_cast : "has cast"
    dim_talent ||--o{ bridge_movie_cast : "performs in"
    dim_movies ||--o{ fact_movie_financials : "has financials"
    dim_movies ||--o{ fact_audience_ratings : "has ratings"
    dataset_upload_history ||--o{ fact_movie_financials : "tracks upload"
    dataset_upload_history ||--o{ fact_audience_ratings : "tracks upload"

    dim_movies {
        int movie_id PK
        string title
        int release_year
        date release_date
        int duration_minutes
        string language
        string country
    }

    dim_talent {
        int talent_id PK
        string talent_name
        string talent_type
    }

    bridge_movie_cast {
        int movie_id PK, FK
        int talent_id PK, FK
        string role_type
    }

    fact_movie_financials {
        int financial_id PK
        int movie_id FK
        int upload_id FK
        decimal budget
        decimal revenue
        decimal domestic_revenue
        decimal international_revenue
        decimal net_profit
        decimal roi_percentage
    }

    fact_audience_ratings {
        int rating_id PK
        int movie_id FK
        int upload_id FK
        decimal imdb_rating
        int vote_count
        string sentiment_tier
    }
```

---

## 🚀 Quickstart & Execution Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Web Analytics Platform
Run the platform server:
```bash
python app.py
```
Open your browser at: **`http://localhost:8500`**

---

## 📁 Repository Directory Layout

```text
CineScope-SQL-Movie-Analytics/
├── app.py                             # Full-Stack Platform Application & HTTP Server
├── scripts/
│   ├── db_manager.py                  # MySQL / Fallback engine, DB auto-creation & queries
│   ├── file_parser.py                 # Multi-format uploader parser (CSV, Excel, JSON)
│   └── data_loader.py                 # CLI Ingestion script
├── data/
│   ├── sample_movies_raw.csv          # Sample raw CSV file
│   ├── sample_movies.xlsx             # Sample raw Excel file
│   └── sample_movies.json             # Sample raw JSON file
├── database/
│   ├── 01_create_database.sql         # Core DDL schema
│   └── 02_insert_sample_data.sql      # Core sample data SQL script
├── sql/                               # Modular analytical SQL scripts (01 to 05)
├── dashboard/
│   └── dax_measures_and_model.md      # Power BI Star Schema & DAX calculation specs
├── documentation/
│   └── analytics_guide.md             # Technical analytics logic reference
├── requirements.txt                   # Dependency manifest
└── README.md                          # Main project documentation
```
