# ============================================================
# database.py - PostgreSQL Star Schema Database Manager
# Goal: Normalizes raw scraped data into a Star Schema:
#       - books_catalog (Dimension Table: Unique Book Metadata)
#       - price_history (Fact Table: Daily Price/Stock Logs)
# ============================================================

# --- IMPORTS ---
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# ============================================================
# FUNCTION: save_to_postgres
# ============================================================
def save_to_postgres(df):
    load_dotenv()

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "price_monitor")

    print("\n" + "=" * 50)
    print("      CONNECTING TO POSTGRESQL DATABASE")
    print("=" * 50)

    # 1. Verify/Create the 'price_monitor' database
    try:
        conn_default = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database="postgres"
        )
        conn_default.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor_default = conn_default.cursor()

        cursor_default.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (db_name,))
        db_exists = cursor_default.fetchone()

        if not db_exists:
            print(f"Database '{db_name}' not found. Creating database '{db_name}'...")
            cursor_default.execute(f"CREATE DATABASE {db_name};")
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' verified (already exists).")

        cursor_default.close()
        conn_default.close()

    except Exception as e:
        print(f"ERROR: Could not verify or create database: {e}")
        print("Please check that PostgreSQL is running and your credentials in .env are correct.")
        return

    # 2. Connect to 'price_monitor' database and verify the Star Schema tables
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
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
        print("Star Schema tables (books_catalog, price_history) verified/created.")

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

        print(f"Syncing unique book metadata into 'books_catalog'...")
        for index, row in df.iterrows():
            cursor.execute(
                upsert_catalog_query,
                (row["UPC"], row["Title"], row["Category"], row["URL"])
            )
        conn.commit()

        # 4. Clean existing same-day records in price_history
        today_date = df["Date_Collected"].iloc[0]
        print(f"Cleaning existing history records for date: {today_date}...")
        cursor.execute("DELETE FROM price_history WHERE date_collected = %s;", (today_date,))

        # 5. Insert fresh run into price_history
        insert_history_query = """
        INSERT INTO price_history (upc, price, rating, stock_quantity, date_collected)
        VALUES (%s, %s, %s, %s, %s);
        """

        print(f"Inserting pricing logs into 'price_history'...")
        for index, row in df.iterrows():
            cursor.execute(
                insert_history_query,
                (
                    row["UPC"],
                    row["Price"],
                    str(row["Rating"]),
                    int(row["Stock_Quantity"]),
                    row["Date_Collected"]
                )
            )

        conn.commit()
        print("Star Schema sync complete! All data saved successfully.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        print("Operations failed. The database transaction has been rolled back.")
