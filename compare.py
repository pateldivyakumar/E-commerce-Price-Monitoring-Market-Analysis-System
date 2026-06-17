# ============================================================
# compare.py - Price Change Detector Script
# Goal: Compare book prices across different dates
#       and flag any books whose prices changed.
# ============================================================

import sys
sys.stdout.reconfigure(encoding="utf-8")
import os
import pandas as pd
import utils

logger = utils.setup_logging()

def load_data():
    try:
        conn = utils.get_db_connection()
        date_cursor = conn.cursor()
        date_cursor.execute("SELECT DISTINCT date_collected FROM price_history ORDER BY date_collected ASC;")
        unique_dates = [row[0].strftime('%Y-%m-%d') for row in date_cursor.fetchall()]
        date_cursor.close()
        
        df_prev, df_latest = None, None
        data_source = "PostgreSQL Database"
        is_simulation = False
        
        if len(unique_dates) < 2:
            logger.info("Less than 2 collection dates found in DB. Running SIMULATION MODE.")
            is_simulation = True
            
            if len(unique_dates) == 1:
                target_date = unique_dates[0]
            else:
                raise ValueError("No records found in price_history table.")
            
            query = """
            SELECT c.title AS "Title", h.price AS "Price", h.rating AS "Rating", 
                   c.product_url AS "URL", h.date_collected AS "Date_Collected", 
                   c.upc AS "UPC", c.category AS "Category", h.stock_quantity AS "Stock_Quantity"
            FROM books_catalog c
            JOIN price_history h ON c.upc = h.upc
            WHERE h.date_collected = %s;
            """
            df_base = pd.read_sql(query, conn, params=(target_date,))
            
            df_prev = df_base.copy()
            previous_date = target_date
            latest_date = "2026-06-06"
            
            df_latest = df_base.copy()
            df_latest["Date_Collected"] = latest_date
            df_latest["Price"] = df_latest["Price"].astype(float)
            df_prev["Price"] = df_prev["Price"].astype(float)
            
            if len(df_latest) > 10:
                df_latest.loc[0, "Price"] = round(df_latest.loc[0, "Price"] - 5.78, 2)
                df_latest.loc[1, "Price"] = round(df_latest.loc[1, "Price"] + 2.50, 2)
                df_latest.loc[10, "Price"] = round(df_latest.loc[10, "Price"] - 12.00, 2)
        else:
            previous_date = unique_dates[-2]
            latest_date = unique_dates[-1]
            
            query = """
            SELECT c.title AS "Title", h.price AS "Price", h.rating AS "Rating", 
                   c.product_url AS "URL", h.date_collected AS "Date_Collected", 
                   c.upc AS "UPC", c.category AS "Category", h.stock_quantity AS "Stock_Quantity"
            FROM books_catalog c
            JOIN price_history h ON c.upc = h.upc
            WHERE h.date_collected = %s;
            """
            df_prev = pd.read_sql(query, conn, params=(previous_date,))
            df_latest = pd.read_sql(query, conn, params=(latest_date,))
            
            df_prev["Price"] = df_prev["Price"].astype(float)
            df_latest["Price"] = df_latest["Price"].astype(float)
            
        conn.close()
        logger.info(f"[DATABASE] Loaded snapshots: {previous_date} -> {latest_date}")
        return df_prev, df_latest, previous_date, latest_date, unique_dates, is_simulation, data_source

    except Exception as e:
        logger.warning(f"Could not connect to DB. Falling back to CSV. Detail: {e}")
        history_file = "data/history.csv"
        if not os.path.exists(history_file):
            logger.error("history.csv not found! Run the scraper first.")
            exit(1)
            
        df = pd.read_csv(history_file)
        df = df.drop_duplicates(subset=["Title", "URL", "Date_Collected"], keep="last").reset_index(drop=True)
        unique_dates = sorted(list(df["Date_Collected"].unique()))
        
        is_simulation = False
        data_source = "CSV Backup Log (Fallback)"
        
        if len(unique_dates) < 2:
            is_simulation = True
            previous_date = unique_dates[0] if unique_dates else "2026-06-05"
            latest_date = "2026-06-06"
            
            df_prev = df.copy()
            df_latest = df.copy()
            df_latest["Date_Collected"] = latest_date
            df_latest["Price"] = df_latest["Price"].astype(float)
            df_prev["Price"] = df_prev["Price"].astype(float)
            
            if len(df_latest) > 10:
                df_latest.loc[0, "Price"] = round(df_latest.loc[0, "Price"] - 5.78, 2)
                df_latest.loc[1, "Price"] = round(df_latest.loc[1, "Price"] + 2.50, 2)
                df_latest.loc[10, "Price"] = round(df_latest.loc[10, "Price"] - 12.00, 2)
        else:
            latest_date = unique_dates[-1]
            previous_date = unique_dates[-2]
            
            df_prev = df[df["Date_Collected"] == previous_date].copy()
            df_latest = df[df["Date_Collected"] == latest_date].copy()
            df_prev["Price"] = df_prev["Price"].astype(float)
            df_latest["Price"] = df_latest["Price"].astype(float)
            
        logger.info(f"[CSV FALLBACK] Loaded snapshots: {previous_date} -> {latest_date}")
        return df_prev, df_latest, previous_date, latest_date, unique_dates, is_simulation, data_source

def generate_comparison_report():
    df_prev, df_latest, previous_date, latest_date, unique_dates, is_simulation, data_source = load_data()

    df_compare = pd.merge(
        df_prev[["Title", "URL", "Price"]], 
        df_latest[["Title", "URL", "Price"]], 
        on=["Title", "URL"], 
        suffixes=("_old", "_new")
    )

    df_compare["Price_Change"] = round(df_compare["Price_new"] - df_compare["Price_old"], 2)
    df_compare["Percent_Change"] = round((df_compare["Price_Change"] / df_compare["Price_old"]) * 100, 2)

    df_changed = df_compare[df_compare["Price_Change"] != 0]
    df_drops = df_changed[df_changed["Price_Change"] < 0]
    df_hikes = df_changed[df_changed["Price_Change"] > 0]

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

    report_lines.append("\n[DECREASE] Price Drops (Good Deals):")
    report_lines.append("-" * 65)
    if df_drops.empty:
        report_lines.append("  No price drops found.")
    else:
        for _, row in df_drops.iterrows():
            report_lines.append(f"* {row['Title']}")
            report_lines.append(f"  Old Price: £{row['Price_old']:.2f}  |  New Price: £{row['Price_new']:.2f}  |  Change: £{row['Price_Change']:.2f} ({row['Percent_Change']}%)")
            report_lines.append(f"  Link: {row['URL']}\n")

    report_lines.append("[INCREASE] Price Hikes (More Expensive):")
    report_lines.append("-" * 65)
    if df_hikes.empty:
        report_lines.append("  No price increases found.")
    else:
        for _, row in df_hikes.iterrows():
            report_lines.append(f"* {row['Title']}")
            report_lines.append(f"  Old Price: £{row['Price_old']:.2f}  |  New Price: £{row['Price_new']:.2f}  |  Change: +£{row['Price_Change']:.2f} (+{row['Percent_Change']}%)")
            report_lines.append(f"  Link: {row['URL']}\n")

    report_lines.append("=" * 65)
    report_lines.append("                       SUMMARY")
    report_lines.append("=" * 65)
    report_lines.append(f"  Checked Books   : {len(df_compare)}")
    report_lines.append(f"  Price Drops     : {len(df_drops)}")
    report_lines.append(f"  Price Hikes     : {len(df_hikes)}")
    report_lines.append(f"  Total Changes   : {len(df_changed)}")
    report_lines.append("=" * 65)

    report_text = "\n".join(report_lines)

    for line in report_lines:
        if line.strip():
            logger.info(line)

    os.makedirs("reports", exist_ok=True)
    report_file_name = f"reports/price_report_{latest_date}.txt"
    with open(report_file_name, "w", encoding="utf-8") as f:
        f.write(report_text)

    logger.info(f"Report successfully saved to: {report_file_name}")

if __name__ == "__main__":
    generate_comparison_report()
