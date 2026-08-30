#!/usr/bin/env python3
"""
=====================================================
CineScope SQL Movie Analytics - Full-Stack Application
File: app.py
Description: Interactive MySQL-backed Analytics Platform with multi-format 
             file uploading (CSV, Excel, JSON), relational normalization, 
             upload history management, and persistent dashboard UI.
=====================================================
"""

import sys
import os
import json
import base64
import re
import webbrowser
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import pandas as pd

# Add root directory to module search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.db_manager import DatabaseManager
from scripts.file_parser import MultiFormatFileParser

PORT = 8500
db = DatabaseManager()


class CineScopePlatformHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PLATFORM.encode("utf-8"))

        elif path == "/api/history":
            history_df = db.get_upload_history()
            records = json.loads(history_df.to_json(orient="records", date_format="iso"))
            self.respond_json(records)

        elif path == "/api/analytics":
            upload_id = params.get("upload_id", [None])[0]
            if upload_id and upload_id.isdigit():
                upload_id = int(upload_id)
            else:
                upload_id = None
            
            data = db.get_analytics(upload_id=upload_id)
            resp = {
                "summary": data["summary"],
                "movies": json.loads(data["movies"].to_json(orient="records", date_format="iso")),
                "talent": json.loads(data["talent"].to_json(orient="records", date_format="iso")),
                "time_series": json.loads(data["time_series"].to_json(orient="records", date_format="iso"))
            }
            self.respond_json(resp)

        elif path == "/api/table":
            table_name = params.get("name", ["dim_movies"])[0]
            allowed_tables = ["dataset_upload_history", "dim_movies", "dim_talent", "bridge_movie_cast", "fact_movie_financials", "fact_audience_ratings"]
            if table_name not in allowed_tables:
                table_name = "dim_movies"
            
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 100", db.engine)
            records = json.loads(df.to_json(orient="records", date_format="iso"))
            self.respond_json(records)

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/upload":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            
            try:
                payload = json.loads(post_body.decode("utf-8"))
                filename = payload.get("filename", "uploaded_dataset.csv")
                file_type = payload.get("file_type", "csv").lower().strip(".")
                file_content_b64 = payload.get("content_b64", "")

                file_bytes = base64.b64decode(file_content_b64)
                
                # 1. Save file to data/
                saved_path = MultiFormatFileParser.save_uploaded_file(file_bytes, filename)
                
                # 2. Parse & Clean
                cleaned_df = MultiFormatFileParser.parse_file(saved_path, file_type)
                total_movies = len(cleaned_df)

                # 3. Log History
                upload_id = db.log_dataset_upload(filename, saved_path, file_type.upper(), total_movies)

                # 4. Insert into Relational Engine
                db.insert_normalized_dataset(cleaned_df, upload_id)

                self.respond_json({
                    "success": True,
                    "upload_id": upload_id,
                    "filename": filename,
                    "total_movies": total_movies,
                    "message": f"Successfully loaded {total_movies} records under Upload #{upload_id}"
                })

            except Exception as e:
                self.respond_json({"success": False, "error": str(e)}, status=400)

        else:
            self.send_error(404, "Not Found")

    def respond_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))


# Embedded Dark-Themed Executive Dashboard HTML Page
HTML_PLATFORM = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CineScope SQL — Movie Analytics Platform</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- FontAwesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #0b0f19; color: #e2e8f0; font-family: 'Segoe UI', system-ui, sans-serif; }
        .glass-card { background: rgba(17, 24, 39, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 0.75rem; }
        .gradient-text { background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .nav-btn.active { border-left: 4px solid #38bdf8; background: rgba(56, 189, 248, 0.1); color: #38bdf8; font-weight: 600; }
    </style>
</head>
<body class="min-h-screen flex flex-col md:flex-row">

    <!-- Sidebar Navigation -->
    <aside class="w-full md:w-64 bg-slate-900 border-r border-slate-800 p-5 flex flex-col justify-between shrink-0">
        <div>
            <div class="flex items-center space-x-3 mb-8">
                <i class="fa-solid fa-film text-sky-400 text-3xl"></i>
                <div>
                    <h1 class="text-lg font-bold text-white">CineScope <span class="gradient-text">SQL</span></h1>
                    <p class="text-xs text-slate-400">Movie Analytics Platform</p>
                </div>
            </div>

            <nav class="space-y-2">
                <button onclick="navTo('nav-home')" id="btn-nav-home" class="nav-btn active w-full text-left px-4 py-3 rounded-lg text-sm text-slate-300 hover:bg-slate-800 transition flex items-center space-x-3">
                    <i class="fa-solid fa-chart-pie w-5 text-sky-400"></i>
                    <span>Dashboard Home</span>
                </button>
                <button onclick="navTo('nav-upload')" id="btn-nav-upload" class="nav-btn w-full text-left px-4 py-3 rounded-lg text-sm text-slate-400 hover:bg-slate-800 transition flex items-center space-x-3">
                    <i class="fa-solid fa-cloud-arrow-up w-5 text-indigo-400"></i>
                    <span>Upload New Dataset</span>
                </button>
                <button onclick="navTo('nav-history')" id="btn-nav-history" class="nav-btn w-full text-left px-4 py-3 rounded-lg text-sm text-slate-400 hover:bg-slate-800 transition flex items-center space-x-3">
                    <i class="fa-solid fa-folder-tree w-5 text-emerald-400"></i>
                    <span>History & Files Hub</span>
                </button>
                <button onclick="navTo('nav-sql')" id="btn-nav-sql" class="nav-btn w-full text-left px-4 py-3 rounded-lg text-sm text-slate-400 hover:bg-slate-800 transition flex items-center space-x-3">
                    <i class="fa-solid fa-database w-5 text-amber-400"></i>
                    <span>SQL Table Explorer</span>
                </button>
            </nav>
        </div>

        <div class="mt-8 pt-4 border-t border-slate-800">
            <div class="text-xs text-slate-400 mb-2 font-medium">Active Dataset Filter:</div>
            <div id="active-filter-badge" class="text-xs font-semibold px-3 py-2 bg-slate-800 rounded text-sky-400 truncate">
                Global (All Datasets)
            </div>
            <button onclick="clearFilter()" class="mt-2 text-xs text-slate-400 hover:text-white underline w-full text-left">
                Clear Filter (Show All)
            </button>
        </div>
    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 p-6 overflow-y-auto">

        <!-- VIEW 1: HOME DASHBOARD -->
        <section id="view-home" class="space-y-6">
            <div class="flex flex-wrap justify-between items-center pb-4 border-b border-slate-800">
                <div>
                    <h2 class="text-2xl font-bold text-white">Interactive Project Overview & Executive Dashboard</h2>
                    <p class="text-xs text-slate-400">Real-Time Financial Risk, Profitability Tiers & Talent Performance</p>
                </div>
            </div>

            <!-- KPI Metric Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                <div class="glass-card p-4">
                    <div class="text-slate-400 text-xs font-semibold uppercase">Total Movies</div>
                    <div class="text-2xl font-extrabold text-white mt-1" id="kpi-movies">0</div>
                </div>
                <div class="glass-card p-4">
                    <div class="text-slate-400 text-xs font-semibold uppercase">Global Revenue</div>
                    <div class="text-2xl font-extrabold text-emerald-400 mt-1" id="kpi-revenue">$0</div>
                </div>
                <div class="glass-card p-4">
                    <div class="text-slate-400 text-xs font-semibold uppercase">Production Budget</div>
                    <div class="text-2xl font-extrabold text-slate-300 mt-1" id="kpi-budget">$0</div>
                </div>
                <div class="glass-card p-4">
                    <div class="text-slate-400 text-xs font-semibold uppercase">Net Profit</div>
                    <div class="text-2xl font-extrabold text-sky-400 mt-1" id="kpi-profit">$0</div>
                </div>
                <div class="glass-card p-4">
                    <div class="text-slate-400 text-xs font-semibold uppercase">Portfolio ROI %</div>
                    <div class="text-2xl font-extrabold text-indigo-400 mt-1" id="kpi-roi">0%</div>
                </div>
            </div>

            <!-- Charts Row 1 -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="glass-card p-5 lg:col-span-2">
                    <h3 class="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4">Yearly Budget vs. Revenue</h3>
                    <div class="h-64"><canvas id="chart-budget-revenue"></canvas></div>
                </div>
                <div class="glass-card p-5">
                    <h3 class="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4">Territory Revenue Split</h3>
                    <div class="h-64"><canvas id="chart-territory"></canvas></div>
                </div>
            </div>

            <!-- Charts Row 2 -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="glass-card p-5">
                    <h3 class="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4">Talent & Director Box Office Yield</h3>
                    <div class="h-64"><canvas id="chart-talent"></canvas></div>
                </div>
                <div class="glass-card p-5">
                    <h3 class="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4">Profitability Tier Distribution</h3>
                    <div class="h-64"><canvas id="chart-tiers"></canvas></div>
                </div>
            </div>

            <!-- Movie Financial Records Table with Filters & Pagination -->
            <div class="glass-card p-5 space-y-4">
                <div class="flex flex-wrap justify-between items-center gap-4">
                    <div>
                        <h3 class="text-sm font-bold text-slate-200 uppercase tracking-wider">Movie Financial Records</h3>
                        <p class="text-xs text-slate-400">Detailed profitability metrics, ROI %, and box-office tiers</p>
                    </div>
                    <div class="flex flex-wrap items-center gap-3">
                        <!-- Search Box -->
                        <div class="relative">
                            <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-500 text-xs"></i>
                            <input type="text" id="movie-search-input" oninput="filterMovieRecords()" placeholder="Search title or year..." class="bg-slate-800 text-white text-xs pl-8 pr-3 py-2 rounded-lg border border-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-400 w-44">
                        </div>

                        <!-- Tier Filter Dropdown -->
                        <select id="movie-tier-select" onchange="filterMovieRecords()" class="bg-slate-800 text-white text-xs p-2 rounded-lg border border-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-400">
                            <option value="ALL">All Profitability Tiers</option>
                            <option value="Blockbuster">Blockbuster (4x+)</option>
                            <option value="Profitable">Profitable (1x-4x)</option>
                            <option value="Broke Even">Broke Even (0x-1x)</option>
                            <option value="Flop">Flop (<0x)</option>
                        </select>

                        <!-- Page Size Selector Dropdown (Default: 10) -->
                        <div class="flex items-center space-x-2">
                            <label class="text-xs text-slate-400 font-medium">Show:</label>
                            <select id="movie-page-size" onchange="changeMoviePageSize()" class="bg-slate-800 text-white text-xs p-2 rounded-lg border border-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-400 font-bold text-sky-400">
                                <option value="5">5 per page</option>
                                <option value="10" selected>10 per page</option>
                                <option value="25">25 per page</option>
                                <option value="50">50 per page</option>
                                <option value="ALL">Show All</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="overflow-x-auto border border-slate-800 rounded-lg">
                    <table class="w-full text-left text-xs text-slate-300">
                        <thead class="bg-slate-800 text-slate-400 uppercase border-b border-slate-700">
                            <tr>
                                <th class="p-3">Title</th>
                                <th class="p-3">Year</th>
                                <th class="p-3">Budget</th>
                                <th class="p-3">Revenue</th>
                                <th class="p-3">Net Profit</th>
                                <th class="p-3">ROI %</th>
                                <th class="p-3">Tier</th>
                            </tr>
                        </thead>
                        <tbody id="table-movies-body" class="divide-y divide-slate-800"></tbody>
                    </table>
                </div>

                <!-- Pagination Footer -->
                <div class="flex flex-wrap justify-between items-center text-xs text-slate-400 pt-2">
                    <div id="movie-pagination-info">Showing 1 to 10 of 10 entries</div>
                    <div class="flex items-center space-x-2">
                        <button id="btn-movie-prev" onclick="prevMoviePage()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed font-semibold transition">
                            <i class="fa-solid fa-chevron-left mr-1"></i> Previous
                        </button>
                        <span id="movie-page-indicator" class="font-bold text-sky-400 px-2">Page 1 of 1</span>
                        <button id="btn-movie-next" onclick="nextMoviePage()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed font-semibold transition">
                            Next <i class="fa-solid fa-chevron-right ml-1"></i>
                        </button>
                    </div>
                </div>
            </div>
        </section>

        <!-- VIEW 2: UPLOAD NEW DATASET -->
        <section id="view-upload" class="space-y-6 hidden">
            <div class="flex justify-between items-center pb-4 border-b border-slate-800">
                <div>
                    <h2 class="text-2xl font-bold text-white">Upload New Movie Dataset</h2>
                    <p class="text-xs text-slate-400">Supports CSV, Excel (.xlsx / .xls), and JSON file formats</p>
                </div>
                <button onclick="navTo('nav-home')" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center space-x-2">
                    <i class="fa-solid fa-house"></i>
                    <span>Back to Home / Dashboard</span>
                </button>
            </div>

            <div class="glass-card p-8 max-w-2xl mx-auto text-center space-y-4">
                <div class="p-6 border-2 border-dashed border-slate-700 hover:border-sky-400 rounded-xl transition cursor-pointer" onclick="document.getElementById('file-input').click()">
                    <i class="fa-solid fa-cloud-arrow-up text-4xl text-sky-400 mb-3"></i>
                    <h3 class="text-base font-bold text-white">Click or Drag & Drop Movie Dataset File</h3>
                    <p class="text-xs text-slate-400 mt-1">Accepts CSV, Excel (.xlsx/.xls), or JSON</p>
                    <input type="file" id="file-input" class="hidden" accept=".csv, .xlsx, .xls, .json" onchange="handleFileSelected(event)">
                </div>

                <div id="upload-status" class="hidden text-sm p-4 rounded-lg"></div>

                <button id="btn-upload" onclick="uploadDataset()" class="hidden w-full py-3 bg-sky-400 hover:bg-sky-500 text-slate-950 font-bold rounded-lg transition">
                    <i class="fa-solid fa-database mr-2"></i> Process & Ingest Dataset into MySQL
                </button>
            </div>
        </section>

        <!-- VIEW 3: HISTORY & FILE MANAGEMENT HUB -->
        <section id="view-history" class="space-y-6 hidden">
            <div class="flex justify-between items-center pb-4 border-b border-slate-800">
                <div>
                    <h2 class="text-2xl font-bold text-white">Dataset Upload History & File Management Hub</h2>
                    <p class="text-xs text-slate-400">Select any uploaded file to re-run analytics or switch dataset focus</p>
                </div>
                <button onclick="navTo('nav-home')" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center space-x-2">
                    <i class="fa-solid fa-house"></i>
                    <span>Back to Home / Dashboard</span>
                </button>
            </div>

            <div class="glass-card p-5">
                <h3 class="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4">Uploaded Datasets Log</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-300">
                        <thead class="bg-slate-800 text-slate-400 uppercase border-b border-slate-700">
                            <tr>
                                <th class="p-3">Upload ID</th>
                                <th class="p-3">File Name</th>
                                <th class="p-3">Format</th>
                                <th class="p-3">Upload Date</th>
                                <th class="p-3">Total Movies</th>
                                <th class="p-3">Status</th>
                                <th class="p-3 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody id="table-history-body" class="divide-y divide-slate-800"></tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- VIEW 4: SQL EXPLORER -->
        <section id="view-sql" class="space-y-6 hidden">
            <div class="flex justify-between items-center pb-4 border-b border-slate-800">
                <div>
                    <h2 class="text-2xl font-bold text-white">Relational Table Explorer</h2>
                    <p class="text-xs text-slate-400">Directly inspect normalized database tables</p>
                </div>
                <button onclick="navTo('nav-home')" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center space-x-2">
                    <i class="fa-solid fa-house"></i>
                    <span>Back to Home / Dashboard</span>
                </button>
            </div>

            <div class="glass-card p-5 space-y-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <label class="text-xs text-slate-300 font-semibold uppercase">Select Relational Table:</label>
                        <select id="select-table" onchange="loadTableData()" class="bg-slate-800 text-white text-xs p-2.5 rounded-lg border border-slate-700 font-medium focus:ring-2 focus:ring-sky-400 outline-none">
                            <option value="dim_movies">dim_movies</option>
                            <option value="dim_talent">dim_talent</option>
                            <option value="bridge_movie_cast">bridge_movie_cast</option>
                            <option value="fact_movie_financials">fact_movie_financials</option>
                            <option value="fact_audience_ratings">fact_audience_ratings</option>
                            <option value="dataset_upload_history">dataset_upload_history</option>
                        </select>
                    </div>
                    <div id="table-sql-count" class="text-xs font-semibold px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-sky-400">
                        0 rows
                    </div>
                </div>

                <div class="overflow-x-auto border border-slate-800 rounded-lg">
                    <table class="w-full text-left text-xs text-slate-300">
                        <thead id="table-sql-head" class="bg-slate-800 text-slate-400 uppercase"></thead>
                        <tbody id="table-sql-body" class="divide-y divide-slate-800/40"></tbody>
                    </table>
                </div>
            </div>
        </section>

    </main>

    <script>
        let currentUploadFilter = null;
        let selectedFilePayload = null;
        let chartInstances = {};

        // Movie Table Pagination & Filtering State
        let allMoviesData = [];
        let filteredMoviesData = [];
        let movieCurrentPage = 1;
        let moviePageSize = 10;

        const fmtMoney = (v) => '$' + (v >= 1e9 ? (v/1e9).toFixed(2) + 'B' : v >= 1e6 ? (v/1e6).toFixed(1) + 'M' : Number(v).toLocaleString());

        function navTo(navId) {
            document.querySelectorAll('main > section').forEach(s => s.classList.add('hidden'));
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

            const viewMap = {
                'nav-home': 'view-home',
                'nav-upload': 'view-upload',
                'nav-history': 'view-history',
                'nav-sql': 'view-sql'
            };

            document.getElementById(viewMap[navId]).classList.remove('hidden');
            document.getElementById('btn-' + navId).classList.add('active');

            if (navId === 'nav-home') loadAnalytics();
            if (navId === 'nav-history') loadHistory();
            if (navId === 'nav-sql') loadTableData();
        }

        function setFilter(uploadId, filename) {
            currentUploadFilter = uploadId;
            document.getElementById('active-filter-badge').innerText = uploadId ? `Upload #${uploadId} - ${filename}` : 'Global (All Datasets)';
            navTo('nav-home');
        }

        function clearFilter() {
            currentUploadFilter = null;
            document.getElementById('active-filter-badge').innerText = 'Global (All Datasets)';
            loadAnalytics();
        }

        async function loadAnalytics() {
            const url = currentUploadFilter ? `/api/analytics?upload_id=${currentUploadFilter}` : '/api/analytics';
            const res = await fetch(url);
            const data = await res.json();
            const s = data.summary;

            document.getElementById('kpi-movies').innerText = s.total_movies;
            document.getElementById('kpi-revenue').innerText = fmtMoney(s.total_revenue);
            document.getElementById('kpi-budget').innerText = fmtMoney(s.total_budget);
            document.getElementById('kpi-profit').innerText = fmtMoney(s.total_net_profit);
            document.getElementById('kpi-roi').innerText = s.overall_roi_pct + '%';

            // Store raw movies data
            allMoviesData = data.movies || [];
            filterMovieRecords();

            // Yearly Chart
            if (chartInstances.budgetRev) chartInstances.budgetRev.destroy();
            chartInstances.budgetRev = new Chart(document.getElementById('chart-budget-revenue'), {
                type: 'bar',
                data: {
                    labels: data.time_series.map(t => t.release_year),
                    datasets: [
                        { label: 'Budget ($)', data: data.time_series.map(t => t.budget), backgroundColor: '#64748b' },
                        { label: 'Revenue ($)', data: data.time_series.map(t => t.revenue), backgroundColor: '#38bdf8' }
                    ]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { ticks: { color: '#94a3b8' } }, x: { ticks: { color: '#94a3b8' } } } }
            });

            // Donut Territory
            if (chartInstances.territory) chartInstances.territory.destroy();
            chartInstances.territory = new Chart(document.getElementById('chart-territory'), {
                type: 'doughnut',
                data: {
                    labels: ['Domestic', 'International'],
                    datasets: [{ data: [s.total_domestic, s.total_international], backgroundColor: ['#38bdf8', '#818cf8'] }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#cbd5e1' } } } }
            });

            // Talent Bar
            if (chartInstances.talent) chartInstances.talent.destroy();
            chartInstances.talent = new Chart(document.getElementById('chart-talent'), {
                type: 'bar',
                data: {
                    labels: data.talent.map(t => t.talent_name),
                    datasets: [{ label: 'Box Office Revenue ($)', data: data.talent.map(t => t.total_revenue), backgroundColor: '#c084fc' }]
                },
                options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, scales: { y: { ticks: { color: '#94a3b8' } }, x: { ticks: { color: '#94a3b8' } } } }
            });

            // Tier Pie
            const tierMap = {};
            data.movies.forEach(m => { tierMap[m.profitability_tier] = (tierMap[m.profitability_tier] || 0) + 1; });
            if (chartInstances.tiers) chartInstances.tiers.destroy();
            chartInstances.tiers = new Chart(document.getElementById('chart-tiers'), {
                type: 'pie',
                data: {
                    labels: Object.keys(tierMap),
                    datasets: [{ data: Object.values(tierMap), backgroundColor: ['#10b981', '#38bdf8', '#fbbf24', '#ef4444'] }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        // Movie Table Pagination & Filtering Logic
        function filterMovieRecords() {
            const searchEl = document.getElementById('movie-search-input');
            const search = searchEl ? searchEl.value.toLowerCase().trim() : '';
            const tierEl = document.getElementById('movie-tier-select');
            const tier = tierEl ? tierEl.value : 'ALL';
            
            filteredMoviesData = allMoviesData.filter(m => {
                const matchesSearch = !search || m.title.toLowerCase().includes(search) || String(m.release_year).includes(search);
                const matchesTier = (tier === 'ALL') || (m.profitability_tier && m.profitability_tier.includes(tier));
                return matchesSearch && matchesTier;
            });

            movieCurrentPage = 1;
            renderMovieTable();
        }

        function changeMoviePageSize() {
            const szEl = document.getElementById('movie-page-size');
            const sz = szEl ? szEl.value : '10';
            moviePageSize = (sz === 'ALL') ? filteredMoviesData.length : parseInt(sz);
            movieCurrentPage = 1;
            renderMovieTable();
        }

        function prevMoviePage() {
            if (movieCurrentPage > 1) {
                movieCurrentPage--;
                renderMovieTable();
            }
        }

        function nextMoviePage() {
            const total = filteredMoviesData.length;
            const sz = moviePageSize || 10;
            const totalPages = Math.ceil(total / sz) || 1;
            if (movieCurrentPage < totalPages) {
                movieCurrentPage++;
                renderMovieTable();
            }
        }

        function renderMovieTable() {
            const total = filteredMoviesData.length;
            const sz = moviePageSize || 10;
            const totalPages = Math.ceil(total / sz) || 1;

            if (movieCurrentPage > totalPages) movieCurrentPage = totalPages;
            if (movieCurrentPage < 1) movieCurrentPage = 1;

            const startIdx = (movieCurrentPage - 1) * sz;
            const endIdx = Math.min(startIdx + sz, total);
            const pageItems = filteredMoviesData.slice(startIdx, endIdx);

            const bodyEl = document.getElementById('table-movies-body');
            if (!pageItems.length) {
                bodyEl.innerHTML = '<tr><td colspan="7" class="p-4 text-center text-slate-500 font-medium">No matching movie financial records found.</td></tr>';
            } else {
                bodyEl.innerHTML = pageItems.map(m => `
                    <tr class="hover:bg-slate-800/50 transition border-b border-slate-800/40">
                        <td class="p-3 font-semibold text-white">${m.title}</td>
                        <td class="p-3 text-slate-400">${m.release_year}</td>
                        <td class="p-3">${fmtMoney(m.budget)}</td>
                        <td class="p-3 text-emerald-400 font-medium">${fmtMoney(m.revenue)}</td>
                        <td class="p-3 text-sky-400 font-medium">${fmtMoney(m.net_profit)}</td>
                        <td class="p-3 font-bold ${m.roi_percentage >= 400 ? 'text-emerald-400' : m.roi_percentage >= 100 ? 'text-sky-400' : 'text-amber-400'}">${m.roi_percentage}%</td>
                        <td class="p-3"><span class="px-2 py-1 rounded text-xs font-bold bg-slate-800 text-sky-400 border border-slate-700">${m.profitability_tier}</span></td>
                    </tr>
                `).join('');
            }

            // Info & Buttons
            const infoEl = document.getElementById('movie-pagination-info');
            if (infoEl) {
                infoEl.innerText = total > 0 
                    ? `Showing ${startIdx + 1} to ${endIdx} of ${total} entries`
                    : 'Showing 0 to 0 of 0 entries';
            }

            const pageIndEl = document.getElementById('movie-page-indicator');
            if (pageIndEl) pageIndEl.innerText = `Page ${movieCurrentPage} of ${totalPages}`;

            const prevBtn = document.getElementById('btn-movie-prev');
            if (prevBtn) prevBtn.disabled = (movieCurrentPage <= 1);

            const nextBtn = document.getElementById('btn-movie-next');
            if (nextBtn) nextBtn.disabled = (movieCurrentPage >= totalPages);
        }

        function handleFileSelected(evt) {
            const file = evt.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                const b64 = e.target.result.split(',')[1] || e.target.result;
                selectedFilePayload = {
                    filename: file.name,
                    file_type: file.name.split('.').pop(),
                    content_b64: b64
                };

                const statusBox = document.getElementById('upload-status');
                statusBox.className = 'text-sm p-4 rounded-lg bg-slate-800 text-sky-400 border border-slate-700';
                statusBox.innerHTML = `File Loaded: <strong>${file.name}</strong> (${(file.size/1024).toFixed(1)} KB)`;
                statusBox.classList.remove('hidden');

                document.getElementById('btn-upload').classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }

        async function uploadDataset() {
            if (!selectedFilePayload) return;
            const statusBox = document.getElementById('upload-status');
            statusBox.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Ingesting dataset into MySQL...';

            const res = await fetch('/api/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(selectedFilePayload)
            });

            const result = await res.json();
            if (result.success) {
                statusBox.className = 'text-sm p-4 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
                statusBox.innerHTML = `✅ ${result.message}`;
                setTimeout(() => setFilter(result.upload_id, result.filename), 1200);
            } else {
                statusBox.className = 'text-sm p-4 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30';
                statusBox.innerHTML = `❌ Error: ${result.error}`;
            }
        }

        async function loadHistory() {
            const res = await fetch('/api/history');
            const history = await res.json();
            document.getElementById('table-history-body').innerHTML = history.map(h => `
                <tr class="hover:bg-slate-800/50">
                    <td class="p-3 font-bold text-sky-400">#${h.upload_id}</td>
                    <td class="p-3 font-semibold text-white">${h.file_name}</td>
                    <td class="p-3"><span class="px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-slate-300">${h.file_type}</span></td>
                    <td class="p-3 text-slate-400">${h.uploaded_at || 'N/A'}</td>
                    <td class="p-3 font-medium">${h.total_movies}</td>
                    <td class="p-3"><span class="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded font-bold">${h.status}</span></td>
                    <td class="p-3 text-right">
                        <button onclick="setFilter(${h.upload_id}, '${h.file_name}')" class="px-3 py-1 bg-sky-500/20 hover:bg-sky-500/40 text-sky-300 rounded font-semibold text-xs border border-sky-500/30 transition">
                            Trigger Analytics
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        async function loadTableData() {
            const tableName = document.getElementById('select-table').value;
            const headEl = document.getElementById('table-sql-head');
            const bodyEl = document.getElementById('table-sql-body');
            const badgeEl = document.getElementById('table-sql-count');
            
            headEl.innerHTML = '';
            bodyEl.innerHTML = '<tr><td class="p-4 text-sky-400 font-semibold"><i class="fa-solid fa-spinner fa-spin mr-2"></i> Loading table data...</td></tr>';
            
            try {
                const res = await fetch(`/api/table?name=${tableName}`);
                const data = await res.json();

                if (!data || !data.length) {
                    headEl.innerHTML = '';
                    bodyEl.innerHTML = '<tr><td class="p-4 text-slate-500 font-medium">No records found in table `' + tableName + '`.</td></tr>';
                    if (badgeEl) badgeEl.innerText = '0 rows';
                    return;
                }

                if (badgeEl) badgeEl.innerText = `${data.length} rows loaded`;

                const cols = Object.keys(data[0]);
                headEl.innerHTML = `<tr>${cols.map(c => `<th class="p-3 font-semibold text-slate-300 border-b border-slate-700">${c}</th>`).join('')}</tr>`;
                bodyEl.innerHTML = data.map(r => `
                    <tr class="hover:bg-slate-800/60 transition border-b border-slate-800/40">
                        ${cols.map(c => {
                            let val = r[c];
                            if (val === null || val === undefined) val = '<span class="text-slate-600 italic">null</span>';
                            return `<td class="p-3 font-medium text-slate-200">${val}</td>`;
                        }).join('')}
                    </tr>
                `).join('');
            } catch (err) {
                headEl.innerHTML = '';
                bodyEl.innerHTML = `<tr><td class="p-4 text-red-400 font-medium">❌ Error loading table: ${err.message}</td></tr>`;
            }
        }

        window.onload = () => loadAnalytics();
    </script>
</body>
</html>
"""


def open_browser_async():
    time.sleep(1.2)
    url = f"http://localhost:{PORT}"
    print(f"\n[INFO] Opening CineScope Full-Stack Platform in browser: {url}\n")
    webbrowser.open(url)


def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, CineScopePlatformHandler)
    print("==================================================")
    print("  CineScope SQL Full-Stack Analytics Platform    ")
    print("==================================================")
    print(f"Platform running at: http://localhost:{PORT}")

    threading.Thread(target=open_browser_async, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down CineScope Platform Server.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
