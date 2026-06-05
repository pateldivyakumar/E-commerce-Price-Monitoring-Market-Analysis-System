# ============================================================
# compare.py - Price Change Detector Script
# Goal: Compare book prices across different dates in history.csv
#       and flag any books whose prices changed.
# ============================================================

# --- IMPORTS ---
import sys
sys.stdout.reconfigure(encoding="utf-8")
import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# ============================================================
# DATA CONNECTION LAYER (DUAL-MODE)
# ============================================================
def load_data():
    load_dotenv()
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "price_monitor")
    
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        
        # 1. Fetch unique collection dates in database
        date_cursor = conn.cursor()
        date_cursor.execute("SELECT DISTINCT date_collected FROM price_history ORDER BY date_collected ASC;")
        unique_dates = [row[0].strftime('%Y-%m-%d') for row in date_cursor.fetchall()]
        date_cursor.close()
        
        df_prev = None
        df_latest = None
        data_source = "PostgreSQL Database"
        is_simulation = False
        
        if len(unique_dates) < 2:
            print("\n[INFO] Less than 2 collection dates found in the database.")
            print("Running in SIMULATION MODE to show how price changes are calculated.")
            is_simulation = True
            
            # Fetch whatever unique date we have
            if len(unique_dates) == 1:
                target_date = unique_dates[0]
            else:
                # No data in database! Trigger exception to fall back to CSV
                raise ValueError("No records found in price_history table.")
            
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
            WHERE h.date_collected = %s;
            """
            df_base = pd.read_sql(query, conn, params=(target_date,))
            conn.close()
            
            # Simulate prev and latest
            df_prev = df_base.copy()
            previous_date = target_date
            latest_date = "2026-06-06"
            
            df_latest = df_base.copy()
            df_latest["Date_Collected"] = latest_date
            df_latest["Price"] = df_latest["Price"].astype(float)
            df_prev["Price"] = df_prev["Price"].astype(float)
            
            # Make some price modifications
            df_latest.loc[0, "Price"] = round(df_latest.loc[0, "Price"] - 5.78, 2)
            df_latest.loc[1, "Price"] = round(df_latest.loc[1, "Price"] + 2.50, 2)
            df_latest.loc[10, "Price"] = round(df_latest.loc[10, "Price"] - 12.00, 2)
        else:
            # Real data mode
            previous_date = unique_dates[-2]
            latest_date = unique_dates[-1]
            
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
            WHERE h.date_collected = %s;
            """
            df_prev = pd.read_sql(query, conn, params=(previous_date,))
            df_latest = pd.read_sql(query, conn, params=(latest_date,))
            conn.close()
            
            df_prev["Price"] = df_prev["Price"].astype(float)
            df_latest["Price"] = df_latest["Price"].astype(float)
            
        print(f"[DATABASE] Loaded snapshots: {previous_date} -> {latest_date}")
        return df_prev, df_latest, previous_date, latest_date, unique_dates, is_simulation, data_source

    except Exception as e:
        print(f"\n[WARNING] Could not connect to PostgreSQL database. Falling back to CSV logs.")
        print(f"Connection Detail: {e}\n")
        
        # Fallback to CSV
        history_file = "data/history.csv"
        if not os.path.exists(history_file):
            print("ERROR: history.csv not found! Run the scraper first.")
            exit()
            
        df = pd.read_csv(history_file)
        df = df.drop_duplicates(subset=["Title", "URL", "Date_Collected"], keep="last").reset_index(drop=True)
        unique_dates = sorted(list(df["Date_Collected"].unique()))
        
        is_simulation = False
        data_source = "CSV Backup Log (Fallback)"
        
        if len(unique_dates) < 2:
            is_simulation = True
            previous_date = unique_dates[0]
            latest_date = "2026-06-06"
            
            df_prev = df.copy()
            df_latest = df.copy()
            df_latest["Date_Collected"] = latest_date
            
            df_latest["Price"] = df_latest["Price"].astype(float)
            df_prev["Price"] = df_prev["Price"].astype(float)
            
            df_latest.loc[0, "Price"] = round(df_latest.loc[0, "Price"] - 5.78, 2)
            df_latest.loc[1, "Price"] = round(df_latest.loc[1, "Price"] + 2.50, 2)
            df_latest.loc[10, "Price"] = round(df_latest.loc[10, "Price"] - 12.00, 2)
        else:
            latest_date = unique_dates[-1]
            previous_date = unique_dates[-2]
            
            df_prev = df[df["Date_Collected"] == previous_date]
            df_latest = df[df["Date_Collected"] == latest_date]
            df_prev["Price"] = df_prev["Price"].astype(float)
            df_latest["Price"] = df_latest["Price"].astype(float)
            
        print(f"[CSV FALLBACK] Loaded snapshots: {previous_date} -> {latest_date}")
        return df_prev, df_latest, previous_date, latest_date, unique_dates, is_simulation, data_source

# Load comparison datasets
df_prev, df_latest, previous_date, latest_date, unique_dates, is_simulation, data_source = load_data()

# ============================================================
# STEP 5: Merge the two dates on Book Title and URL
# ============================================================
# To compare prices side-by-side, we merge the previous and latest DataFrames.
#
# pd.merge() combines two tables like a database JOIN.
#   - on=["Title", "URL"] matches books by both Title and URL.
#   - suffixes=("_old", "_new") adds suffix to column names that exist in both.
#     So "Price" becomes "Price_old" (previous date) and "Price_new" (latest date).
#
# By default, pd.merge performs an "inner" join, meaning only books that
# exist on both dates are compared. This is perfect for our detector.
df_compare = pd.merge(
    df_prev[["Title", "URL", "Price"]], 
    df_latest[["Title", "URL", "Price"]], 
    on=["Title", "URL"], 
    suffixes=("_old", "_new")
)

# ============================================================
# STEP 6: Calculate Price Difference and Percentage Change
# ============================================================
# Subtract previous price from latest price to get change amount.
#   Positive value = price increase
#   Negative value = price decrease (sale / price drop)
df_compare["Price_Change"] = df_compare["Price_new"] - df_compare["Price_old"]

# Round the change amount to 2 decimal places to avoid floating point inaccuracies.
df_compare["Price_Change"] = round(df_compare["Price_Change"], 2)

# Calculate percentage change: (change / old) * 100
# Example: ( -5.78 / 51.77 ) * 100 = -11.16%
# We round the result to 2 decimal places.
df_compare["Percent_Change"] = round((df_compare["Price_Change"] / df_compare["Price_old"]) * 100, 2)

# ============================================================
# STEP 7: Filter for books that changed price
# ============================================================
# Filter the merged table to keep only rows where Price_Change is not equal to 0.
df_changed = df_compare[df_compare["Price_Change"] != 0]

# Split changed books into price drops (negative change) and price hikes (positive change).
df_drops = df_changed[df_changed["Price_Change"] < 0]
df_hikes = df_changed[df_changed["Price_Change"] > 0]

# ============================================================
# STEP 8: Generate and Save the Report
# ============================================================
# We build the report content as a list of lines. This allows us to
# both print it to the terminal AND save it as a text file in reports/
report_lines = []

mode_label = " (Simulated)" if is_simulation else ""
report_lines.append("=" * 65)
report_lines.append(f"         PRICE CHANGE DETECTOR REPORT{mode_label}")
report_lines.append("=" * 65)
report_lines.append(f"Comparing date: {previous_date}  -->  {latest_date}")
report_lines.append(f"Data Source:    {data_source}")
report_lines.append(f"Total books checked: {len(df_compare)}")
report_lines.append(f"Total price changes found: {len(df_changed)}")
report_lines.append("=" * 65)

# --- SECTION A: Price Drops (Deals!) ---
report_lines.append("\n[DECREASE] Price Drops (Good Deals):")
report_lines.append("-" * 65)

if df_drops.empty:
    report_lines.append("  No price drops found.")
else:
    # Loop through each price drop and add details to report
    for index, row in df_drops.iterrows():
        title = row["Title"]
        old = row["Price_old"]
        new = row["Price_new"]
        change = row["Price_Change"]
        percent = row["Percent_Change"]
        url = row["URL"]
        
        report_lines.append(f"* {title}")
        report_lines.append(f"  Old Price: £{old:.2f}  |  New Price: £{new:.2f}  |  Change: £{change:.2f} ({percent}%)")
        report_lines.append(f"  Link: {url}")
        report_lines.append("")

# --- SECTION B: Price Hikes ---
report_lines.append("[INCREASE] Price Hikes (More Expensive):")
report_lines.append("-" * 65)

if df_hikes.empty:
    report_lines.append("  No price increases found.")
else:
    # Loop through each price hike and add details to report
    for index, row in df_hikes.iterrows():
        title = row["Title"]
        old = row["Price_old"]
        new = row["Price_new"]
        change = row["Price_Change"]
        percent = row["Percent_Change"]
        url = row["URL"]
        
        report_lines.append(f"* {title}")
        report_lines.append(f"  Old Price: £{old:.2f}  |  New Price: £{new:.2f}  |  Change: +£{change:.2f} (+{percent}%)")
        report_lines.append(f"  Link: {url}")
        report_lines.append("")

# --- SUMMARY BOX ---
report_lines.append("=" * 65)
report_lines.append("                       SUMMARY")
report_lines.append("=" * 65)
report_lines.append(f"  Checked Books   : {len(df_compare)}")
report_lines.append(f"  Price Drops     : {len(df_drops)}")
report_lines.append(f"  Price Hikes     : {len(df_hikes)}")
report_lines.append(f"  Total Changes   : {len(df_changed)}")
report_lines.append("=" * 65)

# Join the lines with newlines to form the complete report text
report_text = "\n".join(report_lines)

# 1. Print the report to the console
print(report_text)

# 2. Save the report to a file in the reports/ folder
os.makedirs("reports", exist_ok=True)
report_file_name = f"reports/price_report_{latest_date}.txt"

# We open the file in write mode ("w") with utf-8 encoding to save the £ symbol correctly
with open(report_file_name, "w", encoding="utf-8") as f:
    f.write(report_text)

print(f"\n[SUCCESS] Report successfully saved to: {report_file_name}")
