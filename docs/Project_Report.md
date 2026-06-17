# Project Report: E-Commerce Price Monitoring & Competitive Intelligence System

## 1. Executive Summary
The **E-Commerce Price Monitoring System** is an automated Extract, Transform, Load (ETL) data pipeline designed to track, normalize, store, and analyze competitor product prices and stock levels in real-time. By leveraging Python, pandas, and PostgreSQL, the system effectively manages historical trend analysis and price change detection. It also enables robust business intelligence (BI) reporting via Power BI and Streamlit. This report documents the architecture, key features, technology stack, and implementation details of the project.

## 2. System Architecture & Data Flow
The system's modular architecture separates concerns into extraction, database integration, statistical analysis, and alerting layers:

1. **Extraction**: `scraper.py` navigates target e-commerce sites using HTTP requests (via `requests.Session()`) and parses HTML with BeautifulSoup4.
2. **Transformation**: Extracted data is transformed and normalized using pandas DataFrames.
3. **Loading**: 
   - **Local Logging**: Data is written to local CSV snapshots (`books.csv` and `history.csv`).
   - **Relational Storage**: The `database.py` module establishes a secure connection to a PostgreSQL database, handles auto-schema migrations, and uses parameterized SQL to insert data.
4. **Analysis & BI**: `analyze.py` and `compare.py` handle statistical analysis and price change detection. A Streamlit web application (`app.py`) provides an interactive frontend that queries the local database or falls back to CSV logs if deployed on the cloud.

## 3. Technology Stack & Rationale
| Tool / Library       | Role                    | Rationale |
|----------------------|-------------------------|-----------|
| **Python**           | Core Language           | Ideal for data engineering, offering clean syntax and extensive data libraries. |
| **BeautifulSoup4**   | HTML Parser             | Efficiently parses nested HTML and extracts essential attributes. |
| **Requests**         | HTTP Client             | Uses TCP connection sessions for reliable and faster network connections. |
| **pandas**           | Data Wrangler           | Provides high-performance operations for data cleaning and exporting. |
| **PostgreSQL**       | Relational Database     | A highly robust, relational DB system for permanent historical data storage. |
| **psycopg2-binary**  | Postgres Driver         | Thread-safe database adapter supporting parameterized queries against SQL Injection. |
| **python-dotenv**    | Security Manager        | Manages secure loading of environment variables and credentials from `.env` files. |
| **Streamlit**        | Web Dashboard Frontend  | Facilitates rapid development of interactive web applications for data visualization. |

## 4. Key Features & Implementations
- **Dual-Mode Data Architecture**: The system can seamlessly switch between querying a local PostgreSQL database and falling back to local CSVs for cloud deployments (e.g., Streamlit Community Cloud).
- **Paginated Multi-Page Scraping & Deep Harvesting**: Successfully traverses paginated listings (up to 1,000 products over 50 pages), extracting detailed attributes like UPC, category, and stock quantity from product detail pages.
- **Connection Pooling**: Utilizes `requests.Session()` to reuse TCP connections, increasing the speed of details page requests significantly.
- **Auto-Schema Database Migrations**: Automatically detects table schema changes and executes `ALTER TABLE` queries to update schemas without losing data.
- **Price Change Detection**: Compares consecutive pipeline runs in the historical log to detect price drops (deals) or hikes, outputting actionable reports.
- **Interactive BI Analytics**: An integrated Streamlit dashboard for real-time KPIs and Plotly charts, alongside a structured Power BI setup for deep enterprise BI insights.

## 5. Database Schema Description
The `books` table resides in the `price_monitor` PostgreSQL database using a Star Schema design:

| Column Name      | SQL Data Type    | Description |
|------------------|------------------|-------------|
| `id`             | `SERIAL`         | Primary Key. Auto-incrementing unique identifier. |
| `title`          | `TEXT`           | Full name of the book. |
| `price`          | `NUMERIC(10,2)`  | Numeric price excluding currency symbols. |
| `rating`         | `VARCHAR(20)`    | Rating stored as string (e.g., 'Three'). |
| `product_url`    | `TEXT`           | Absolute web link to product details page. |
| `date_collected` | `DATE`           | Collection date in ISO 8601 format (`YYYY-MM-DD`). |
| `upc`            | `VARCHAR(50)`    | Unique Universal Product Code. |
| `category`       | `VARCHAR(100)`   | Genre or category. |
| `stock_quantity` | `INT`            | Current stock volume. |

## 6. Skills & Competencies Demonstrated
- **Data Engineering**: Constructing complete ETL pipelines, unstructured data extraction, and schema transformations.
- **Database Management**: Complex SQL aggregations, schema configurations, and automated DB migrations.
- **Network Optimization**: Implementing I/O optimization strategies like session persistence.
- **Security Best Practices**: Protecting connections via environment configurations and parameterized SQL.
- **Business Intelligence**: Visual storytelling, BI tool integration, and statistical modeling.

## 7. Future Improvements
1. **Pipeline Concurrency**: Implementing `asyncio` or thread pools for parallel fetching to reduce extraction time dramatically.
2. **Slowly Changing Dimensions (SCD Type 2)**: Normalizing the DB schema into dimension/fact tables to reduce historical data redundancy.
3. **Automated Alerting**: Integrating `smtplib` or messaging APIs to trigger instant notifications when prices drop below defined thresholds.