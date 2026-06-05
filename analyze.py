# ============================================================
# analyze.py - Data Analysis Script
# Goal: Read the scraped data, generate useful statistics,
#       and save a summary report to the reports directory.
# ============================================================

# --- IMPORT ---
import pandas as pd
import os
import psycopg2
from dotenv import load_dotenv


# ============================================================
# STEP 1: Load the CSV file into a DataFrame
# ============================================================
# pd.read_csv() reads a CSV file and converts it into a DataFrame (table).
# It automatically detects:
#   - Column names from the first row (Title, Price, Rating, URL, Date_Collected)
#   - Data types for each column (strings, numbers, etc.)
#
# After this line, 'df' is a full table with 1000 rows and 5 columns.
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
        print(f"\n[WARNING] Could not query PostgreSQL database. Falling back to CSV.")
        print(f"Connection Detail: {e}\n")
        
        if os.path.exists("data/books.csv"):
            df = pd.read_csv("data/books.csv")
            # Parse rating
            rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
            if df["Rating"].dtype == object:
                df["Rating_Numeric"] = df["Rating"].map(rating_map).fillna(pd.to_numeric(df["Rating"], errors='coerce')).fillna(0).astype(int)
            else:
                df["Rating_Numeric"] = df["Rating"].fillna(0).astype(int)
            return df, "CSV Snapshot Backup (data/books.csv)"
        else:
            print("ERROR: No CSV backup snapshot found at data/books.csv!")
            exit()

df, data_source = load_data()

# We will collect all our analysis lines in a list so we can both
# print them to the terminal and save them as a text report.
report_lines = []


# ============================================================
# STEP 2: Total number of books
# ============================================================
# len() returns the number of items in any Python object.
# len(df) counts the number of ROWS in the DataFrame.
# Each row = one book, so len(df) = total number of books scraped.
total_books = len(df)

report_lines.append("=" * 50)
report_lines.append("       BOOKS.TOSCRAPE.COM - DATA ANALYSIS")
report_lines.append("=" * 50)
report_lines.append(f"Data Source : {data_source}")
report_lines.append(f"Total books in dataset: {total_books}")


# ============================================================
# STEP 3: Price Statistics
# ============================================================
# df["Price"] selects just the Price column from the DataFrame.
# It returns a 'Series' — which is like a single-column table.
#
# pandas Series have built-in math methods:
#   .mean()  → calculates the AVERAGE (sum of all / count)
#   .max()   → finds the LARGEST value
#   .min()   → finds the SMALLEST value
#
# round(value, 2) rounds a number to 2 decimal places.
#   round(35.635857, 2) → 35.64
#   This prevents messy output like 35.635857142857...

average_price = round(df["Price"].mean(), 2)
highest_price = df["Price"].max()
lowest_price = df["Price"].min()

report_lines.append("\n--- Price Statistics ---")
report_lines.append(f"Average price: {average_price}")
report_lines.append(f"Highest price: {highest_price}")
report_lines.append(f"Lowest price:  {lowest_price}")


# ============================================================
# STEP 4: Find WHICH books have the highest and lowest prices
# ============================================================
# Knowing the max/min price is useful, but knowing WHICH BOOK it is
# is even more useful. We use two techniques here:
#
# df["Price"].idxmax() → returns the ROW INDEX of the maximum value.
#   If the most expensive book is in row 52, idxmax() returns 52.
#
# df.loc[52] → retrieves the entire row at index 52.
#   This gives us all columns (Title, Price, Rating, etc.) for that book.
#
# df.loc[52, "Title"] → retrieves ONLY the Title from row 52.

most_expensive_index = df["Price"].idxmax()
most_expensive_title = df.loc[most_expensive_index, "Title"]

cheapest_index = df["Price"].idxmin()
cheapest_title = df.loc[cheapest_index, "Title"]

report_lines.append(f"\nMost expensive: {most_expensive_title} ({highest_price})")
report_lines.append(f"Cheapest:       {cheapest_title} ({lowest_price})")


# ============================================================
# STEP 5: Rating Distribution
# ============================================================
# "Rating distribution" means: how many books have each rating?
# For example: 200 books with 1 star, 180 with 2 stars, etc.
#
# df["Rating"].value_counts() does this automatically.
# It counts how many times each unique value appears in the column.
#
# .sort_index() sorts the result by the rating number (1, 2, 3, 4, 5)
# instead of by count. Without it, pandas sorts by most frequent first.

rating_counts = df["Rating_Numeric"].value_counts().sort_index()

report_lines.append("\n--- Rating Distribution ---")
report_lines.append("Stars | Count")
report_lines.append("-" * 20)

# .items() lets us loop through each rating and its count.
# It returns pairs like: (1, 336), (2, 222), (3, 185), etc.
for stars, count in rating_counts.items():
    # Create a simple visual bar using the * character.
    # "*" * 10 produces "**********" — 10 asterisks.
    # We divide count by 10 to keep the bar a reasonable length.
    # int() removes the decimal: int(33.6) → 33
    bar = "*" * int(count / 10)

    # Print each row: star rating, count, and visual bar
    report_lines.append(f"  {stars}   |  {count:>3}  {bar}")
    #                       ↑
    #                  {:>3} means: right-align the number in a space 3 characters wide
    #                  This lines up single and triple digit numbers:
    #                    "  5" vs "336" — both take 3 characters


# ============================================================
# STEP 6: Quick Summary Table using .describe()
# ============================================================
# df["Price"].describe() generates 8 statistics in one call:
#   count  → number of values (1000)
#   mean   → average
#   std    → standard deviation (how spread out the prices are)
#   min    → smallest value
#   25%    → 25th percentile (25% of books cost less than this)
#   50%    → median (middle value — half cost more, half cost less)
#   75%    → 75th percentile (75% of books cost less than this)
#   max    → largest value
#
# This is a very common pandas method used in data analysis.
# We convert the describe output to string so it can be added to the report.

report_lines.append("\n--- Full Price Summary (.describe()) ---")
report_lines.append(str(df["Price"].describe()))


# ============================================================
# DONE
# ============================================================
report_lines.append("\n" + "=" * 50)
report_lines.append("Analysis complete.")

# Join all lines with newlines to form the complete report text
report_text = "\n".join(report_lines)

# 1. Print the report to the console
print(report_text)

# 2. Save the report to a file in the reports/ folder
os.makedirs("reports", exist_ok=True)
report_file_name = "reports/analysis_report.txt"

# We open the file in write mode ("w") with utf-8 encoding to save correctly
with open(report_file_name, "w", encoding="utf-8") as f:
    f.write(report_text)

print(f"\n[SUCCESS] Report successfully saved to: {report_file_name}")
