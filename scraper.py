# ============================================================
# scraper.py - Beginner Web Scraper (Upgraded: All Pages)
# Website: https://books.toscrape.com
# Goal: Scrape title, price, rating, and URL from ALL 50 pages
# ============================================================

# --- IMPORTS ---

# 'requests' lets Python visit a website and download its HTML.
import requests

# 'BeautifulSoup' lets us search through and read the downloaded HTML.
from bs4 import BeautifulSoup

# 'os' is used to create the output folder if it doesn't exist.
import os

# 'pandas' is used to build a data table (DataFrame) and save it as a CSV file.
import pandas as pd

# Import our custom database manager module (database.py)
# This allows us to call save_to_postgres(df) to save our scraped records.
from database import save_to_postgres

# ============================================================
# UNDERSTANDING datetime
# ============================================================
# 'datetime' is a built-in Python module for working with dates and times.
# It comes pre-installed with Python — no need to pip install anything.
#
# Key concepts:
#   datetime.date.today()   --> today's date as a date object (e.g., 2026-06-05)
#   datetime.datetime.now() --> current date AND time (e.g., 2026-06-05 14:18:09)
#
# We use .date.today() because for price monitoring we only need the DATE,
# not the exact second the scraper ran.
#
# .strftime() converts a date object into a formatted STRING:
#   today.strftime("%Y-%m-%d")
#     %Y = full year   (2026)
#     %m = month       (06)
#     %d = day         (05)
#     Result: "2026-06-05"
#
# This format (YYYY-MM-DD) is called ISO 8601 — it's the international
# standard. It sorts correctly as text AND is understood by Excel, pandas,
# databases, and every programming language.
# ============================================================
import datetime


# ============================================================
# UNDERSTANDING PAGINATION
# ============================================================
# Books.toscrape.com has 1000 books spread across 50 pages.
# Each page shows 20 books.
#
# The URL pattern looks like this:
#   Page 1: https://books.toscrape.com/                         (homepage)
#   Page 2: https://books.toscrape.com/catalogue/page-2.html
#   Page 3: https://books.toscrape.com/catalogue/page-3.html
#   ...
#   Page 50: https://books.toscrape.com/catalogue/page-50.html
#
# At the bottom of each page, there is a "next" button:
#   <li class="next">
#     <a href="catalogue/page-2.html">next</a>
#   </li>
#
# Our strategy:
#   1. Start at page 1
#   2. Scrape all 20 books on the current page
#   3. Look for the "next" button
#   4. If found → build the next page's URL and repeat from step 2
#   5. If NOT found → we're on the last page, stop the loop
# ============================================================


# ============================================================
# UNDERSTANDING HOW RATINGS ARE STORED IN HTML
# ============================================================
# Most websites display ratings as stars (visual). But in the HTML source,
# the rating is stored as a CSS CLASS NAME, not as visible text.
#
# Here is the actual HTML for a 3-star book:
#   <p class="star-rating Three">
#     <i class="icon-star"></i>
#     ...
#   </p>
#
# Notice:
#   - The <p> tag has TWO CSS classes: "star-rating" and "Three"
#   - "star-rating" is a shared class (every book has it)
#   - "Three" is the UNIQUE class that tells us the rating
#
# When BeautifulSoup reads these classes, it gives us a Python LIST:
#   rating_tag["class"]  -->  ["star-rating", "Three"]
#       Index 0 = "star-rating"  (always the same, not useful)
#       Index 1 = "Three"        (this is the rating!)
#
# The possible rating words are: One, Two, Three, Four, Five
#
# WHY do websites use class names for data?
#   - CSS classes control STYLING. Each rating word triggers different CSS rules.
#   - "Three" might show 3 filled stars + 2 empty stars via CSS.
#   - It's a common web design pattern: encode data as class names.
#   - As scrapers, we can read these class names to extract the data.
# ============================================================


# --- RATING WORD-TO-NUMBER MAPPING ---
# The HTML uses English words ("One", "Two", etc.) for ratings.
# But for our CSV file, we want numbers (1, 2, 3, 4, 5).
#
# A dictionary maps each word to its number.
# Usage: rating_map["Three"]  -->  3
rating_map = {
    "One":   1,
    "Two":   2,
    "Three": 3,
    "Four":  4,
    "Five":  5
}



# --- STEP 1: Define the base URLs ---
# The homepage (page 1) lives at the root address.
# All pages from page 2 onwards live under the /catalogue/ folder.
#
# We need two base URLs because the site uses different relative link formats:
#   - From page 1, the "next" href is: "catalogue/page-2.html"
#   - From page 2+, the "next" href is: "page-3.html" (no 'catalogue/' prefix)
#
# By storing the catalogue base separately, we can always build the correct URL.
base_url      = "https://books.toscrape.com/"             # Used only for page 1
catalogue_url = "https://books.toscrape.com/catalogue/"   # Used for pages 2+

# --- STEP 2: Set the starting URL ---
# We begin at the homepage (page 1).
current_url = base_url

# --- STEP 2b: Create a requests Session ---
# A Session object reuses the same TCP connection for multiple HTTP requests.
# Since we will make 1000 individual requests to get details for each book,
# using a Session speeds up the scraper by 2x to 3x!
session = requests.Session()

# --- STEP 3: Create an empty list to collect all book data ---
# Each book will be stored as a dictionary with: Title, Price, Rating, URL
# After all pages are scraped, this list will have 1000 entries.
all_books = []

# --- STEP 4: Track the page number for progress display ---
# This counter increments by 1 each time we move to a new page.
page_number = 1

# --- NEW: Capture today's date ONCE before the loop starts ---
# We call datetime.date.today() to get today's date as a date object.
# Then .strftime("%Y-%m-%d") converts it to a clean string: "2026-06-05"
#
# WHY capture it ONCE, outside the loop?
#   - All 1000 books from the same scrape run should share the SAME date.
#   - If we called today() inside the loop, and the scraper ran past midnight,
#     some books would get yesterday's date and others today's. That would be messy.
#   - Capturing it once guarantees consistency across the entire run.
today = datetime.date.today().strftime("%Y-%m-%d")
print(f"Scrape date: {today}")


# ============================================================
# STEP 5: The Pagination Loop
# ============================================================
# 'while True' creates a loop that runs forever — until WE break out of it.
# We break out when there is no "next" button (we've reached the last page).
#
# This pattern is called "loop until a condition is met":
#   - We don't know in advance how many pages there are
#   - We let the site tell us when to stop (absence of "next" button)
# ============================================================
while True:

    # ---- SHOW PROGRESS ----
    # Print the current page number so we can see the scraper is working.
    print(f"Scraping page {page_number}...")

    # ---- FETCH THE CURRENT PAGE ----
    # Visit the current URL and download its HTML using the Session.
    response = session.get(current_url)

    # ---- PARSE THE HTML ----
    # Convert the raw HTML string into a BeautifulSoup object we can search.
    soup = BeautifulSoup(response.text, "html.parser")

    # ---- FIND ALL BOOK CARDS ON THIS PAGE ----
    # Each book is wrapped in <article class="product_pod">
    # This returns a list of 20 book blocks (one per book on the page).
    books_on_page = soup.find_all("article", class_="product_pod")

    # ---- EXTRACT TITLE, PRICE, RATING, AND URL FROM EACH BOOK ----
    for book in books_on_page:

        # --- TITLE ---
        # Navigate: <article> → <h3> → <a title="Full Title">
        # The 'title' attribute holds the full, untruncated book name.
        h3_tag = book.find("h3")
        a_tag = h3_tag.find("a")
        title = a_tag["title"]

        # --- PRICE ---
        # Navigate: <article> → <p class="price_color">£51.77</p>
        price_tag = book.find("p", class_="price_color")
        price_raw = price_tag.text.strip()

        # Clean the price: keep only digits and the decimal point.
        # This removes the £ symbol regardless of encoding issues on Windows.
        # Example: "£51.77" → picks '5','1','.','7','7' → joins to "51.77"
        price_no_symbol = "".join([char for char in price_raw if char.isdigit() or char == "."])

        # Convert the cleaned string "51.77" to a float number 51.77
        price = float(price_no_symbol)

        # --- RATING ---
        # Navigate: <article> --> <p class="star-rating Three">
        #
        # The rating is NOT stored as text between the tags.
        # Instead, it's hidden in the CSS CLASS NAME of the <p> tag.
        #
        # book.find("p", class_="star-rating") finds the <p> tag that has
        # "star-rating" as one of its classes.
        rating_tag = book.find("p", class_="star-rating")

        # rating_tag["class"] returns a LIST of all CSS classes on this tag.
        # Example: ["star-rating", "Three"]
        #
        # The rating word is always at index [1] (the second item in the list).
        # Index [0] is always "star-rating" (not useful to us).
        rating_classes = rating_tag["class"]
        rating_word = rating_classes[1]
        # rating_word is now a string like "Three"

        # Convert the English word to a number using our dictionary.
        # rating_map["Three"]  -->  3
        rating = rating_map[rating_word]

        # --- PRODUCT URL ---
        # ============================================================
        # RELATIVE vs ABSOLUTE URLs
        # ============================================================
        # An ABSOLUTE URL is a complete web address you can paste into a browser:
        #   https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
        #
        # A RELATIVE URL is a shortcut that only works relative to the current page:
        #   catalogue/a-light-in-the-attic_1000/index.html   (from page 1)
        #   a-light-in-the-attic_1000/index.html             (from page 2+)
        #
        # Websites use relative URLs in their HTML because they're shorter.
        # But for our CSV data, we want ABSOLUTE URLs — complete links that
        # work from anywhere (email, spreadsheet, another script).
        #
        # The <a> tag inside <h3> has the product link in its 'href' attribute.
        # We already found a_tag above for the title, so we reuse it here.
        # ============================================================
        relative_url = a_tag["href"]

        # The site has the same two-format pattern we saw with pagination:
        #   From page 1: href = "catalogue/a-light-in-the-attic_1000/index.html"
        #                       ↑ includes 'catalogue/' prefix
        #   From page 2+: href = "a-light-in-the-attic_1000/index.html"
        #                        ↑ no 'catalogue/' prefix
        #
        # We detect which format it is and build the correct absolute URL.
        if "catalogue/" in relative_url:
            # Page 1 format: href already has 'catalogue/', add to base_url
            #   "https://books.toscrape.com/" + "catalogue/..." = full URL
            product_url = base_url + relative_url
        else:
            # Page 2+ format: href has no 'catalogue/', add to catalogue_url
            #   "https://books.toscrape.com/catalogue/" + "..." = full URL
            product_url = catalogue_url + relative_url

        # ---- DEEP SCRAPING: Fetch individual product page for extra details ----
        # To get the Category, UPC, and Stock Quantity, we must visit the book's individual page.
        # We reuse our session object to keep the requests fast.
        detail_response = session.get(product_url)
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")

        # 1. Extract Category from breadcrumbs
        # breadcrumb structure: <li>Home</li> <li>Books</li> <li>CategoryName</li>
        # The category is always the 3rd list item (index 2).
        category = "Unknown"
        breadcrumb = detail_soup.find("ul", class_="breadcrumb")
        if breadcrumb:
            items = breadcrumb.find_all("li")
            if len(items) > 2:
                category = items[2].text.strip()

        # 2. Extract UPC and Stock Quantity from the product details table
        upc = "Unknown"
        stock_quantity = 0
        info_table = detail_soup.find("table", class_="table-striped")
        if info_table:
            rows = info_table.find_all("tr")
            for row in rows:
                header = row.find("th").text.strip()
                value = row.find("td").text.strip()
                
                # Check for the UPC row
                if header == "UPC":
                    upc = value
                # Check for the Availability row (contains count)
                elif header == "Availability":
                    # Value is like: "In stock (22 available)"
                    # We extract only the digits to get the raw number
                    qty_chars = "".join([c for c in value if c.isdigit()])
                    if qty_chars:
                        stock_quantity = int(qty_chars)

        # --- STORE THIS BOOK ---
        # Create a dictionary for this book and append it to our master list.
        # Now includes Title, Price, Rating, URL, Date_Collected, UPC, Category, and Stock_Quantity.
        book_data = {
            "Title": title,
            "Price": price,
            "Rating": rating,
            "URL": product_url,
            "Date_Collected": today,
            "UPC": upc,
            "Category": category,
            "Stock_Quantity": stock_quantity
        }

        all_books.append(book_data)

    # ================================================================
    # STEP 6: Check for the "Next" Button (Pagination Logic)
    # ================================================================
    # After scraping all books on the current page, look for a "next" link.
    #
    # The "next" button HTML looks like this:
    #   <li class="next">
    #     <a href="catalogue/page-2.html">next</a>
    #   </li>
    #
    # soup.find("li", class_="next") returns:
    #   - The <li> tag  → if the "next" button exists (more pages left)
    #   - None          → if the button is missing (we're on the last page)
    # ================================================================
    next_button = soup.find("li", class_="next")

    # ---- CHECK: Is there a next page? ----
    if next_button is None:
        # No "next" button found — we are on the LAST page.
        # Print a message and break out of the while loop.
        print(f"Reached the last page ({page_number}). Done!")
        break  # 'break' immediately exits the while loop

    # ---- BUILD THE NEXT PAGE URL ----
    # If we're here, a "next" button exists. We need its URL.
    #
    # The <a> tag inside the <li class="next"> holds the relative link.
    # The href value changes depending on which page we're on:
    #
    #   From page 1 (homepage): href = "catalogue/page-2.html"
    #       → Full URL: base_url + "catalogue/page-2.html"
    #       → "https://books.toscrape.com/catalogue/page-2.html"  ✅
    #
    #   From page 2+ (catalogue pages): href = "page-3.html"
    #       → Full URL: catalogue_url + "page-3.html"
    #       → "https://books.toscrape.com/catalogue/page-3.html"  ✅
    #
    # We detect which case we're in by checking if 'catalogue' is already
    # in the href. If yes, it's from page 1. If no, it's from page 2+.
    next_page_relative = next_button.find("a")["href"]

    if "catalogue" in next_page_relative:
        # We're on page 1 — the href already includes 'catalogue/'
        # Just add it to the root base_url
        current_url = base_url + next_page_relative
    else:
        # We're on page 2 or beyond — href is just 'page-N.html'
        # Add it to the catalogue_url so the path is correct
        current_url = catalogue_url + next_page_relative

    # Increment the page counter so the progress message updates correctly
    page_number = page_number + 1

    # The while loop now repeats from the top with the new current_url


# ============================================================
# STEP 7: Convert collected data into a pandas DataFrame
# ============================================================
# pd.DataFrame(all_books) converts our list of 1000 dictionaries
# into a structured table with two columns: "Title" and "Price"
print(f"\nTotal books collected: {len(all_books)}")

df = pd.DataFrame(all_books)

# Show the first 5 rows as a preview (instead of all 1000)
# df.head() returns the first 5 rows by default.
print("\nPreview (first 5 rows):")
print(df.head())

# Show data types of each column — useful to confirm Price is float, not string
print("\nColumn data types:")
print(df.dtypes)


# ============================================================
# STEP 8: Save the DataFrame to CSV files
# ============================================================
# Create the output folder "data/" if it doesn't already exist.
os.makedirs("data", exist_ok=True)

# ---- FILE 1: books.csv (current snapshot — always overwritten) ----
# This file always contains ONLY the latest scrape.
# Every run replaces it completely. Useful for quick analysis of current data.
df.to_csv("data/books.csv", index=False)
print("\nData saved to: data/books.csv (current snapshot)")

# ---- FILE 1b: Dated backup file (e.g., books_2026-06-05.csv — never overwritten) ----
# This creates a separate file for each scraping run based on today's date.
# Excellent for long-term data warehousing partitioning and scheduling.
dated_file = f"data/books_{today}.csv"
df.to_csv(dated_file, index=False)
print(f"Dated archive saved to: {dated_file}")


# ============================================================
# STEP 9: Append to history.csv (never overwrite!)
# ============================================================
# history.csv is the HEART of our price monitoring system.
# It keeps ALL scrape runs — today's, yesterday's, last week's.
# Every time the scraper runs, new rows are ADDED to the bottom.
# Old rows are NEVER deleted or overwritten.
#
# This lets us track price changes over time:
#   Title,                     Price, Date_Collected
#   A Light in the Attic,      51.77, 2026-06-05
#   A Light in the Attic,      49.99, 2026-06-06   ← price dropped!
#   A Light in the Attic,      49.99, 2026-06-07
#
# ============================================================
# UNDERSTANDING os.path.exists()
# ============================================================
# os.path.exists() checks if a file or folder exists on your computer.
# It returns a boolean:
#   True  → the file is already there
#   False → the file does not exist yet
#
# Example:
#   os.path.exists("data/history.csv")
#     → True   (file was created by a previous run)
#     → False  (this is the very first time we're running the scraper)
#
# WHY do we need this check?
#
# A CSV file has a HEADER ROW at the top:
#   Title,Price,Rating,URL,Date_Collected     ← header (column names)
#   A Light in the Attic,51.77,3,...          ← data row
#   Tipping the Velvet,53.74,1,...            ← data row
#
# When the file does NOT exist (first run):
#   → We need to CREATE it WITH the header row
#   → df.to_csv("file.csv", header=True)  ← writes header + data
#
# When the file ALREADY exists (second run, third run, etc.):
#   → The header is already there from the first run
#   → We just need to ADD new data rows below the existing ones
#   → If we wrote the header again, we'd get duplicate headers:
#       Title,Price,Rating,...        ← original header
#       ...data from run 1...
#       Title,Price,Rating,...        ← DUPLICATE header (bad!)
#       ...data from run 2...
#
# So we use mode="a" (append) with header=False to avoid duplicates.
# ============================================================

# Define the path to our history file
history_file = "data/history.csv"

# Check if history.csv already exists
file_exists = os.path.exists(history_file)

if file_exists:
    # ---- FILE EXISTS: Append new data WITHOUT writing the header again ----
    #
    # mode="a" means "append" — add to the END of the file.
    #   Compare with mode="w" (write) which REPLACES the entire file.
    #   "a" is like adding pages to the back of a notebook.
    #   "w" is like ripping out all pages and starting fresh.
    #
    # header=False means: do NOT write the column names again.
    #   The header row (Title,Price,Rating,...) already exists from the first run.
    #
    # index=False means: do NOT write row numbers.
    df.to_csv(history_file, mode="a", header=False, index=False)
    print(f"Data appended to: {history_file} (added {len(df)} new records)")

else:
    # ---- FILE DOES NOT EXIST: Create it WITH the header ----
    #
    # This is the very first run. We use the default mode="w" (write)
    # and header=True (which is the default, but we write it explicitly
    # for clarity).
    df.to_csv(history_file, mode="w", header=True, index=False)
    print(f"Created new file: {history_file} (with {len(df)} records)")


# ============================================================
# ============================================================
# STEP 10: PostgreSQL Database Integration
# ============================================================
# We call save_to_postgres(df) which is imported from database.py.
# This connects to our PostgreSQL database, verifies that the database
# and books table exist (creating them if not), and saves the records.
# ============================================================
save_to_postgres(df)


# ============================================================
# DONE
# ============================================================
print("-" * 40)
print(f"Total pages scraped : {page_number}")
print(f"Total books scraped : {len(all_books)}")
print("Scraping and database insertion complete!")
