# ============================================================
# analyze.py - Data Analysis Script
# Goal: Read the scraped data, generate useful statistics,
#       and save a summary report to the reports directory.
# ============================================================

import pandas as pd
import os
import utils

logger = utils.setup_logging()

def load_data():
    try:
        conn = utils.get_db_connection()
        query = """
        SELECT c.title AS "Title", 
               h.price AS "Price", 
               h.rating AS "Rating", 
               c.product_url AS "URL", 
               h.date_collected AS "Date_Collected", 
               c.upc AS "UPC", 
               c.category AS "Category", 
               h.stock_quantity AS "Stock_Quantity"
        FROM books_catalog c
        JOIN price_history h ON c.upc = h.upc
        WHERE h.date_collected = (SELECT max(date_collected) FROM price_history);
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Clean data types
        df["Price"] = df["Price"].astype(float)
        df["Stock_Quantity"] = df["Stock_Quantity"].astype(int)
        
        # Parse rating
        rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
        if df["Rating"].dtype == object:
            df["Rating_Numeric"] = df["Rating"].map(rating_map).fillna(pd.to_numeric(df["Rating"], errors='coerce')).fillna(0).astype(int)
        else:
            df["Rating_Numeric"] = df["Rating"].fillna(0).astype(int)
            
        return df, "PostgreSQL Database"
        
    except Exception as e:
        logger.warning(f"Could not query PostgreSQL database. Falling back to CSV. Detail: {e}")
        
        if os.path.exists("data/books.csv"):
            df = pd.read_csv("data/books.csv")
            rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
            if df["Rating"].dtype == object:
                df["Rating_Numeric"] = df["Rating"].map(rating_map).fillna(pd.to_numeric(df["Rating"], errors='coerce')).fillna(0).astype(int)
            else:
                df["Rating_Numeric"] = df["Rating"].fillna(0).astype(int)
            return df, "CSV Snapshot Backup (data/books.csv)"
        else:
            logger.error("No CSV backup snapshot found at data/books.csv!")
            exit(1)

def generate_report():
    df, data_source = load_data()
    report_lines = []

    total_books = len(df)
    report_lines.append("=" * 50)
    report_lines.append("       BOOKS.TOSCRAPE.COM - DATA ANALYSIS")
    report_lines.append("=" * 50)
    report_lines.append(f"Data Source : {data_source}")
    report_lines.append(f"Total books in dataset: {total_books}")

    average_price = round(df["Price"].mean(), 2)
    highest_price = df["Price"].max()
    lowest_price = df["Price"].min()

    report_lines.append("\n--- Price Statistics ---")
    report_lines.append(f"Average price: {average_price}")
    report_lines.append(f"Highest price: {highest_price}")
    report_lines.append(f"Lowest price:  {lowest_price}")

    most_expensive_index = df["Price"].idxmax()
    most_expensive_title = df.loc[most_expensive_index, "Title"]

    cheapest_index = df["Price"].idxmin()
    cheapest_title = df.loc[cheapest_index, "Title"]

    report_lines.append(f"\nMost expensive: {most_expensive_title} ({highest_price})")
    report_lines.append(f"Cheapest:       {cheapest_title} ({lowest_price})")

    rating_counts = df["Rating_Numeric"].value_counts().sort_index()
    report_lines.append("\n--- Rating Distribution ---")
    report_lines.append("Stars | Count")
    report_lines.append("-" * 20)

    for stars, count in rating_counts.items():
        bar = "*" * int(count / 10)
        report_lines.append(f"  {stars}   |  {count:>3}  {bar}")

    report_lines.append("\n--- Full Price Summary (.describe()) ---")
    report_lines.append(str(df["Price"].describe()))

    report_lines.append("\n" + "=" * 50)
    report_lines.append("Analysis complete.")

    report_text = "\n".join(report_lines)

    # Print to console via logger
    for line in report_lines:
        logger.info(line)

    # Save report
    os.makedirs("reports", exist_ok=True)
    report_file_name = "reports/analysis_report.txt"
    with open(report_file_name, "w", encoding="utf-8") as f:
        f.write(report_text)

    logger.info(f"Report successfully saved to: {report_file_name}")

if __name__ == "__main__":
    generate_report()
