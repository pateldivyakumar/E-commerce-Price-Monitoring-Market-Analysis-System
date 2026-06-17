# ============================================================
# database.py - PostgreSQL Star Schema Database Manager
# Goal: Normalizes raw scraped data into a Star Schema:
#       - books_catalog (Dimension Table: Unique Book Metadata)
#       - price_history (Fact Table: Daily Price/Stock Logs)
# ============================================================

# --- IMPORTS ---
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import execute_batch
import utils

logger = utils.setup_logging()

# ============================================================
# FUNCTION: save_to_postgres
# ============================================================
def save_to_postgres(df):
    db_name = utils.get_db_config()

    logger.info("=" * 50)
    logger.info("      CONNECTING TO POSTGRESQL DATABASE")
    logger.info("=" * 50)

    # 1. Verify/Create the 'price_monitor' database
    try:
        conn_default = utils.get_db_connection(database="postgres")
        conn_default.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor_default = conn_default.cursor()

        cursor_default.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (db_name,))
        db_exists = cursor_default.fetchone()

        if not db_exists:
            logger.info(f"Database '{db_name}' not found. Creating database '{db_name}'...")
            # Use psycopg2.sql to safely construct identifier to prevent SQL injection
            create_db_query = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
            cursor_default.execute(create_db_query)
            logger.info(f"Database '{db_name}' created successfully.")
        else:
            logger.info(f"Database '{db_name}' verified (already exists).")

        cursor_default.close()
        conn_default.close()

    except Exception as e:
        logger.error(f"Could not verify or create database: {e}")
        logger.error("Please check that PostgreSQL is running and your credentials in .env are correct.")
        return

    # 2. Connect to 'price_monitor' database and verify the Star Schema tables
    try:
        conn = utils.get_db_connection()
        cursor = conn.cursor()

        # A. Dimension Table: books_catalog (Unique Book Metadata)
        # Primary Key is 'upc' — ensuring exactly one entry per book.
        create_catalog_table = """
        CREATE TABLE IF NOT EXISTS books_catalog (
            upc VARCHAR(50) PRIMARY KEY,
            title TEXT NOT NULL,
            category VARCHAR(100),
            product_url TEXT NOT NULL
        );
        """
        cursor.execute(create_catalog_table)

        # B. Fact Table: price_history (Daily Price/Stock Logs)
        # Reference upc from books_catalog. Implements CHECK and UNIQUE constraints.
        create_history_table = """
        CREATE TABLE IF NOT EXISTS price_history (
            id SERIAL PRIMARY KEY,
            upc VARCHAR(50) REFERENCES books_catalog(upc) ON DELETE CASCADE,
            price NUMERIC(10,2) NOT NULL CONSTRAINT chk_positive_price CHECK (price >= 0),
            rating VARCHAR(20),
            stock_quantity INT DEFAULT 0 CONSTRAINT chk_positive_stock CHECK (stock_quantity >= 0),
            date_collected DATE NOT NULL,
            
            -- Prevent same-day duplicates for the same book
            CONSTRAINT uq_book_daily_snapshot UNIQUE (upc, date_collected)
        );
        """
        cursor.execute(create_history_table)
        conn.commit()
        logger.info("Star Schema tables (books_catalog, price_history) verified/created.")

        # 3. UPSERT unique metadata into books_catalog
        # If the UPC already exists, we update the title, category, and URL.
        upsert_catalog_query = """
        INSERT INTO books_catalog (upc, title, category, product_url)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (upc) DO UPDATE 
        SET title = EXCLUDED.title, 
            category = EXCLUDED.category, 
            product_url = EXCLUDED.product_url;
        """

        logger.info("Syncing unique book metadata into 'books_catalog' (bulk insert)...")
        catalog_data = [(row["UPC"], row["Title"], row["Category"], row["URL"]) for _, row in df.iterrows()]
        execute_batch(cursor, upsert_catalog_query, catalog_data)
        conn.commit()

        # 4. Clean existing same-day records in price_history
        today_date = df["Date_Collected"].iloc[0]
        logger.info(f"Cleaning existing history records for date: {today_date}...")
        cursor.execute("DELETE FROM price_history WHERE date_collected = %s;", (today_date,))

        # 5. Insert fresh run into price_history
        insert_history_query = """
        INSERT INTO price_history (upc, price, rating, stock_quantity, date_collected)
        VALUES (%s, %s, %s, %s, %s);
        """

        logger.info("Inserting pricing logs into 'price_history' (bulk insert)...")
        history_data = [
            (
                row["UPC"],
                row["Price"],
                str(row["Rating"]),
                int(row["Stock_Quantity"]),
                row["Date_Collected"]
            )
            for _, row in df.iterrows()
        ]
        execute_batch(cursor, insert_history_query, history_data)

        conn.commit()
        logger.info("Star Schema sync complete! All data saved successfully.")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"DATABASE ERROR: {e}")
        logger.error("Operations failed. The database transaction has been rolled back.")

