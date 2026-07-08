# E-Commerce Price Monitoring & Competitive Intelligence System

🔗 **Live Dashboard**: [View on Streamlit Cloud](https://e-commerce-price-monitoring-market-analysis-system-jssfqmcurxr.streamlit.app)

An automated, enterprise-ready **ETL (Extract, Transform, Load) Data Pipeline** that tracks, normalizes, stores, and analyzes competitor product prices and stock levels in real-time. 

Built with **Python**, **pandas**, and **PostgreSQL**, this system persists scraped data to both local CSV logs and a relational Star Schema database, enabling historical trend analysis, price change detection, and interactive business intelligence reporting via **Streamlit** and **Power BI**.

---

## ⚙️ System Architecture & Data Flow

This data pipeline is designed with a modular architecture that separates concerns across extraction, database integration, statistical analysis, and alerting layers.

```mermaid
graph TD
    A["Target E-Commerce Site"] -->|"HTTP GET (Requests Session)"| B["src/scraper.py (ETL Engine)"]
    B -->|"HTML Parsing (BeautifulSoup4)"| C["Data Transformation (pandas)"]
    
    C -->|"1. Snapshot Backup"| D["data/books.csv"]
    C -->|"2. Append Log"| E["data/history.csv"]
    C -->|"3. Relational Load"| F["src/database.py (Database Connector)"]
    
    F -->|"psycopg2 Parametric SQL"| G[("PostgreSQL (Star Schema)")]
    
    D -->|"Descriptive Stats"| H["src/analyze.py (Analytics Engine)"]
    E -->|"Price Change Report"| I["src/compare.py (Change Detector)"]
    G -->|"SQL Aggregations"| J["SQL/analysis_queries.sql"]
    
    G -->|"Query DB (Local Mode)"| K["src/app.py (Streamlit Web Dashboard)"]
    D -.->|"Load Snapshot (Cloud Fallback)"| K
    E -.->|"Load History (Cloud Fallback)"| K
```

---

## 🚀 Key Features

* **Interactive Streamlit Web Dashboard**: A responsive web application featuring real-time KPI cards, interactive Plotly charts (genre distributions, ratings, average pricing spreads), price drop deal highlights, product catalog search, and an in-app ETL pipeline runner.
* **Dual-Mode Data Architecture**: Connects to the local PostgreSQL database when running locally, and gracefully falls back to local CSV files when deployed to the cloud (enabling free public hosting!).
* **Concurrent High-Performance Scraping**: Uses `ThreadPoolExecutor` with 20 parallel workers to fetch all 1,000 product detail pages concurrently, reducing scrape time from ~3 minutes to under 30 seconds.
* **Paginated Multi-Page Scraping**: Automatically traverses across all 50 listing pages (1,000 products) of the target site.
* **Deep Page Harvesting (Master-Detail)**: Extracts Category, unique UPC (Universal Product Code), and Stock Quantity by visiting each product's details page.
* **Star Schema Database Design**: Separates data into a `books_catalog` dimension table (unique metadata) and a `price_history` fact table (pricing logs), reducing redundancy and enabling efficient analytical queries.
* **Network Performance Connection Pooling**: Utilizes `requests.Session()` to reuse TCP connections, speeding up network requests by 2.5x.
* **Auto-Schema Database Migrations**: The database connector automatically detects table changes and runs `ALTER TABLE` queries on-the-fly to update your schema without data loss.
* **Security & Parameterization**: Implements safe database connections via `.env` file credentials and utilizes SQL parameterized queries in `psycopg2` to protect against **SQL Injection**.
* **Price Change Detection**: Compares runs in the historical log and flags price drops (deals) and hikes, outputting absolute and percentage differences.
* **Business Intelligence (BI) Analytics**: Saves clean, descriptive statistics reports and features a complete setup blueprint for an interactive Power BI dashboard.

---

## 🛠️ Technology Stack & Rationale

| Tool / Library | Role | Rationale |
| :--- | :--- | :--- |
| **Python** | Core Language | Standard for data engineering due to its clean syntax and extensive data library ecosystem. |
| **BeautifulSoup4** | HTML Parser | Efficient library for parsing nested HTML elements, extracting attributes, and handling malformed markup. |
| **Requests** | HTTP Client | Lightweight synchronous client optimized with TCP connection sessions for reliable network connections. |
| **pandas** | Data Wrangler | Provides high-performance DataFrame operations for cleaning, data type casting, and exporting datasets. |
| **PostgreSQL** | Relational Database | High-performance, relational database system used for permanent historical data storage. |
| **psycopg2-binary** | Postgres Driver | Thread-safe database adapter for Python supporting parameterized queries and database transactions. |
| **python-dotenv** | Security Manager | Conforms to 12-factor app guidelines by loading server credentials from a secure `.env` configuration file. |
| **Streamlit** | Web Framework | Python-native framework for building interactive data dashboards with minimal frontend code. |
| **Plotly** | Visualization | Interactive charting library that renders responsive, publication-quality charts in the browser. |

---

## 📁 Repository Structure

```
├── src/                          # Core application source code
│   ├── app.py                    # Streamlit web dashboard (KPIs, charts, search, pipeline runner)
│   ├── scraper.py                # Concurrent web scraper with ThreadPoolExecutor
│   ├── database.py               # PostgreSQL Star Schema connector & migration engine
│   ├── analyze.py                # Descriptive statistics & report generator
│   ├── compare.py                # Price change detector (drops & hikes)
│   └── utils.py                  # Shared utilities (logging, DB connections)
│
├── scripts/
│   └── run_pipeline.bat          # Windows batch orchestrator (Scrape → Analyze → Compare)
│
├── data/
│   ├── books.csv                 # Latest scraped snapshot (overwritten each run)
│   ├── history.csv               # Append-only historical price log
│   └── books_YYYY-MM-DD.csv      # Date-partitioned archive backups
│
├── SQL/
│   ├── create_tables.sql         # DDL script for base schema
│   └── analysis_queries.sql      # Advanced analytical queries
│
├── docs/
│   ├── PowerBI_Guide.md          # Power BI setup walkthrough
│   ├── EXECUTION_GUIDE.md        # Detailed execution instructions
│   ├── Project_Report.md         # Project summary report
│   ├── optimized_schema.md       # Star Schema design documentation
│   ├── power_bi_build_guide.md   # Step-by-step Power BI build guide
│   ├── power_bi_dashboard_design.md  # Dashboard design specifications
│   └── code_review_report.md     # Code quality review
│
├── config/
│   └── PriceMonitor_Theme.json   # Custom Power BI theme
│
├── reports/
│   ├── analysis_report.txt       # Output stats from analyze.py
│   └── price_report_YYYY-MM-DD.txt  # Price change reports
│
├── screenshots/                  # Visual assets for documentation
├── .streamlit/                   # Streamlit configuration
├── .devcontainer/                # VS Code Dev Container setup
├── requirements.txt              # Python dependencies
├── .env                          # Database credentials (git-ignored)
└── .gitignore                    # Git exclusion rules
```

---

## 📊 Database Schema (Star Schema)

The system uses a normalized **Star Schema** with separate dimension and fact tables in the PostgreSQL `price_monitor` database.

### Dimension Table: `books_catalog`

| Column Name | SQL Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `upc` | `VARCHAR(50)` | `PRIMARY KEY` | The unique Universal Product Code of the book. |
| `title` | `TEXT` | - | The full name of the book. |
| `product_url` | `TEXT` | - | Absolute web link to product details page. |
| `category` | `VARCHAR(100)` | - | The genre/category of the book. |

### Fact Table: `price_history`

| Column Name | SQL Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` | `PRIMARY KEY` | Auto-incrementing unique identifier for each row. |
| `upc` | `VARCHAR(50)` | `FOREIGN KEY` | References `books_catalog.upc`. |
| `price` | `NUMERIC(10,2)` | - | Numeric price with 2 decimal precision. |
| `rating` | `VARCHAR(20)` | - | Star rating stored as integer (1-5). |
| `stock_quantity` | `INT` | - | The number of copies currently in stock. |
| `date_collected` | `DATE` | - | The collection date in ISO 8601 format (`YYYY-MM-DD`). |

---

## 📈 Project Results & Analytics

Running the pipeline extracts **1,000 unique products** and yields these data metrics:
* **Catalog Size**: 1,000 books across 50 pages.
* **Pricing Range**: Average price of **£35.07**, ranging from **£10.00** (Cheapest: *An Abundance of Katherines*) to **£59.99** (Most Expensive: *The Perfect Play*).
* **Inventory Volume**: Real-time stock counts tracked per book, allowing businesses to audit stock concentrations.
* **Scrape Performance**: ~30 seconds for full 1,000-product extraction using concurrent workers (vs. ~3 minutes sequentially).

---

## 🖼️ Dashboard Preview (Power BI)

The data extracted can be imported into Power BI to construct an interactive Business Intelligence report. Follow the instructions in **[docs/PowerBI_Guide.md](docs/PowerBI_Guide.md)** to load the data, write calculations, and configure the UI.

![Power BI Dashboard ](screenshots/power_bi_dashboard_mockup.png)

---

## 🚀 Installation & Setup Guide

### Prerequisites
1. **Python 3.7+** installed.
2. **PostgreSQL** server running locally (optional — the app works without it using CSV fallback).

### Step 1: Clone the Repository
```bash
git clone https://github.com/pateldivyakumar/E-commerce-Price-Monitoring-Market-Analysis-System.git
cd E-commerce-Price-Monitoring-Market-Analysis-System
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Database Credentials
Create a `.env` file in the root directory and add your PostgreSQL credentials:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=price_monitor
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD
```

---

## 🏃 Execution Commands

### 1. Extract Data (Run the Scraper)
Scrapes all 50 pages of the website, saves the data to `data/books.csv` and `data/history.csv`, and automatically syncs it to your PostgreSQL database:
```bash
python src/scraper.py
```

### 2. View Statistics (Run the Analyzer)
Computes descriptive statistics, identifies cheapest and most expensive books, and draws a star-rating distribution chart directly in the console:
```bash
python src/analyze.py
```

### 3. Detect Price Changes (Run the Price Change Detector)
Compares prices between the latest two runs in `history.csv` and flags price drops and hikes:
```bash
python src/compare.py
```

### 4. Run the Full ETL Pipeline (Batch Script)
To run the entire pipeline sequentially (Scrape → Load to DB → Analyze → Compare) and log status details automatically:
```bash
scripts\run_pipeline.bat
```
*Note: Python scripts log directly to `logs/pipeline.log`. The batch orchestrator logs its own status to `logs/batch_run.log`.*

### 5. Launch the Web Dashboard (Streamlit)
Launches the interactive dashboard in your local browser:
```bash
python -m streamlit run src/app.py
```

---

## ☁️ Deploying to the Cloud (Free Recruiter Showcase)

You can host this interactive dashboard for free on **Streamlit Community Cloud** so recruiters can view your work instantly without downloading code or setting up PostgreSQL!

### How it works:
Streamlit Cloud links directly to your public GitHub repository. Since cloud servers cannot access your local PostgreSQL database, `src/app.py` uses a **Dual-Mode Data Loader**:
1. **Local Mode**: Queries the local PostgreSQL `price_monitor` database via the Star Schema.
2. **Cloud Mode**: If the database is unreachable, it automatically catches the connection error and loads data from the date-partitioned CSV files inside your repository.

### Setup Instructions:
1. Push this project folder to your public **GitHub** repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
3. Click **New app**, select your repository, set the branch to `main`, and type `src/app.py` as the main file path.
4. Click **Deploy!** 
Once deployed, copy the link and paste it at the top of your repository description or your resume!

---

## ⏰ Automated Scheduling (Windows Task Scheduler)

You can configure your computer to run the pipeline automatically (e.g., every day, week, or month) without manual execution:

1. Open the **Windows Start Menu**, search for **Task Scheduler**, and open it.
2. In the right panel, click **Create Basic Task...**
3. Configure the task settings:
   * **Name**: `Price Monitoring Pipeline`
   * **Trigger**: Choose how often to run (e.g., *Daily* or *Monthly*).
   * **Action**: Choose **Start a program**.
4. In the **Program/script** field, click **Browse** and select [scripts/run_pipeline.bat](scripts/run_pipeline.bat).
5. In the **Start in (optional)** field, enter the absolute path to your project folder:
   `C:\path\to\your\E-commerce-Price-Monitoring-Market-Analysis-System`
6. Click **Finish**. 

Now, Windows will automatically trigger the scraper, clean the database, insert the new records, and refresh the reporting datasets on your schedule!

---

## 🧠 Skills Demonstrated

* **Data Pipeline & ETL Engineering**: Extracting unstructured web data, transforming schemas, and loading into files and SQL warehouses.
* **SQL Database Management**: Star Schema design, schema configuration, writing complex aggregations, and automating database migrations.
* **Concurrent Programming**: Implementing `ThreadPoolExecutor` for parallel I/O-bound web requests to optimize throughput.
* **Network & I/O Optimization**: Utilizing session persistence and connection pooling to reduce network request overhead.
* **Tabular Data Wrangling**: Implementing type cleaning, formatting, and mathematical statistics using `pandas`.
* **Full-Stack Web Development**: Building interactive dashboards with Streamlit, Plotly, and real-time data connections.
* **Cloud Deployment**: Deploying data applications to Streamlit Community Cloud with dual-mode data architecture.
* **Security Compliance**: Safeguarding credentials using environment configurations and preventing injection attacks.
* **Business Intelligence (BI)**: Visual data storytelling, DAX modeling, and report design.

---

## 🔮 Future Improvements

1. **Async Scraping**: Migrate from `ThreadPoolExecutor` to `asyncio` + `aiohttp` for even faster non-blocking I/O.
2. **Slowly Changing Dimensions (SCD Type 2)**: Add historical tracking of dimension changes (e.g., category reclassifications) with effective date ranges.
3. **Automated Alerting**: Integrate `smtplib` to trigger instant email notifications to users when price drops cross a defined discount threshold.
4. **CI/CD Pipeline**: Add GitHub Actions to automatically run the scraper on a schedule and commit fresh data back to the repository.
