# PostgreSQL Schema Optimization Report: `books` Table
**Role**: PostgreSQL Database Architect  
**Project**: Price Monitoring & Competitive Intelligence System  
**Status**: Architecture Review & Optimization Complete

---

## 🔍 Schema Audit & Key Recommendations

The current table structure works for simple ingestion but has major performance and integrity issues under production loads. Below is the architectural review and the corresponding optimization strategies:

### 1. Data Type Normalization
* **The Rating Column**: Currently, `rating` is stored as a `VARCHAR(20)` containing strings like `'Three'`. 
  * *Architectural Issue*: Text takes up significantly more disk space (variable-length text storage overhead) and makes SQL mathematical aggregations (e.g., finding the average rating of a category) impossible without slow string-to-number mapping at runtime.
  * *Optimization*: Convert `rating` to a `SMALLINT` (2 bytes, range -32,768 to 32,767). Add a `CHECK` constraint to restrict values to a range of `1` to `5`.

### 2. Data Integrity & Constraints
* **Nullability**: In your current schema, columns like `title`, `price`, `product_url`, and `date_collected` are nullable.
  * *Architectural Issue*: A scraped record with a missing price or URL is corrupted data. Allowing null values breaks downstream reporting and Power BI calculations.
  * *Optimization*: Apply `NOT NULL` constraints to all critical fields (`title`, `price`, `product_url`, `date_collected`, `upc`).
* **Check Constraints**:
  * **Price Safety**: Add `CHECK (price >= 0)` to prevent negative pricing errors from scraping bugs.
  * **Stock Safety**: Add `CHECK (stock_quantity >= 0)` to prevent negative inventory counts.
* **Uniqueness (The Natural Key)**:
  * *Architectural Issue*: There is no constraint preventing the same book from being inserted multiple times on the same date.
  * *Optimization*: Add a composite `UNIQUE (upc, date_collected)` constraint. This serves two roles:
    1. Prevents duplicate scraping runs on the same calendar day.
    2. Enables the use of safe **SQL UPSERT** (`INSERT ... ON CONFLICT DO UPDATE`) commands.

### 3. Indexing Strategy for Performance
Without indexes, PostgreSQL must perform a sequential scan (scanning every row on disk) for every search, grouping, or comparison. As your database grows, queries will slow down.
* **Composite Index `(upc, date_collected)`**: Automatically created by the `UNIQUE` constraint. This speeds up historical price lookups for individual books.
* **Single Column Index on `category`**: Speed up queries that group and average pricing by genre (e.g., bar and pie charts in Power BI).
* **Single Column Index on `date_collected`**: Speed up time-series filters and date-range comparisons in your reporting dashboards.

---

## 🛠️ Optimized DDL SQL Script

Here is the production-ready SQL script to create the optimized table schema:

```sql
-- 1. Create the optimized books table
CREATE TABLE books (
    -- Primary Key: Auto-incrementing surrogate key
    id SERIAL PRIMARY KEY,
    
    -- Natural Key: Unique UPC code (cannot be null)
    upc VARCHAR(50) NOT NULL,
    
    -- Core Attributes
    title TEXT NOT NULL,
    category VARCHAR(100),
    product_url TEXT NOT NULL,
    
    -- Numerical Metrics (with safety constraints)
    price NUMERIC(10,2) NOT NULL CONSTRAINT chk_positive_price CHECK (price >= 0),
    stock_quantity INT DEFAULT 0 CONSTRAINT chk_positive_stock CHECK (stock_quantity >= 0),
    
    -- Normalized Rating (1 to 5)
    rating SMALLINT CONSTRAINT chk_rating_range CHECK (rating BETWEEN 1 AND 5),
    
    -- Meta Information
    date_collected DATE NOT NULL,
    
    -- Data Integrity: Prevent duplicate entries of the same book on the same day
    CONSTRAINT uq_book_daily_snapshot UNIQUE (upc, date_collected)
);

-- 2. Performance Indexes

-- Index on category: Accelerates GROUP BY queries for category analysis
CREATE INDEX idx_books_category ON books (category);

-- Index on date: Accelerates historical time-series ranges and line-chart queries
CREATE INDEX idx_books_date_collected ON books (date_collected);

-- 3. Verification Queries for Database Maintenance
-- Query to audit index usage and size
SELECT 
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    pg_size_pretty(pg_relation_size(relid)) AS table_size,
    pg_size_pretty(pg_indexes_size(relid)) AS index_size
FROM pg_stat_user_tables
WHERE relname = 'books';
```
