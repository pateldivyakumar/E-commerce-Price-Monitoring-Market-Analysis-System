# ============================================================
# scraper.py - Advanced Concurrent Web Scraper
# Website: https://books.toscrape.com
# Goal: Scrape title, price, rating, and URL from ALL 50 pages
#       Optimized using ThreadPoolExecutor for high performance.
# ============================================================

import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import utils
from database import save_to_postgres

# Initialize structured logging
logger = utils.setup_logging()

class BookScraper:
    def __init__(self):
        self.base_url = "https://books.toscrape.com/"
        self.catalogue_url = "https://books.toscrape.com/catalogue/"
        self.session = requests.Session()
        self.all_books = []
        self.today = datetime.date.today().strftime("%Y-%m-%d")
        self.rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

    def fetch_page_books(self, url):
        """Fetches all books on a single index page and their relative URLs."""
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        books_on_page = soup.find_all("article", class_="product_pod")
        
        parsed_books = []
        for book in books_on_page:
            # Extract basic info
            h3_tag = book.find("h3")
            a_tag = h3_tag.find("a")
            title = a_tag["title"]
            
            price_tag = book.find("p", class_="price_color")
            price_raw = price_tag.text.strip()
            # Clean the price: keep only digits and the decimal point
            price = float("".join([c for c in price_raw if c.isdigit() or c == "."]))
            
            rating_tag = book.find("p", class_="star-rating")
            rating_word = rating_tag["class"][1]
            rating = self.rating_map.get(rating_word, 0)
            
            relative_url = a_tag["href"]
            if "catalogue/" in relative_url:
                product_url = self.base_url + relative_url
            else:
                product_url = self.catalogue_url + relative_url
                
            parsed_books.append({
                "Title": title,
                "Price": price,
                "Rating": rating,
                "URL": product_url
            })
            
        # Check pagination
        next_button = soup.find("li", class_="next")
        next_url = None
        if next_button:
            next_page_relative = next_button.find("a")["href"]
            if "catalogue" in next_page_relative:
                next_url = self.base_url + next_page_relative
            else:
                next_url = self.catalogue_url + next_page_relative
                
        return parsed_books, next_url

    def fetch_book_details(self, book):
        """Deep scrape a single book detail page concurrently."""
        detail_response = self.session.get(book["URL"])
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")
        
        category = "Unknown"
        breadcrumb = detail_soup.find("ul", class_="breadcrumb")
        if breadcrumb:
            items = breadcrumb.find_all("li")
            if len(items) > 2:
                category = items[2].text.strip()
                
        upc = "Unknown"
        stock_quantity = 0
        info_table = detail_soup.find("table", class_="table-striped")
        if info_table:
            rows = info_table.find_all("tr")
            for row in rows:
                header = row.find("th").text.strip()
                value = row.find("td").text.strip()
                
                if header == "UPC":
                    upc = value
                elif header == "Availability":
                    qty_chars = "".join([c for c in value if c.isdigit()])
                    if qty_chars:
                        stock_quantity = int(qty_chars)
                        
        book["Date_Collected"] = self.today
        book["UPC"] = upc
        book["Category"] = category
        book["Stock_Quantity"] = stock_quantity
        return book

    def run(self):
        """Main execution flow for the scraper."""
        logger.info(f"Starting scrape for date: {self.today}")
        current_url = self.base_url
        page_number = 1
        
        basic_books = []
        
        # Phase 1: Sequentially extract URLs from all 50 pagination index pages
        while current_url:
            logger.info(f"Scraping index page {page_number}...")
            books_on_page, next_url = self.fetch_page_books(current_url)
            basic_books.extend(books_on_page)
            current_url = next_url
            page_number += 1
            
        logger.info(f"Found {len(basic_books)} books. Fetching details concurrently...")
        
        # Phase 2: Concurrently fetch all 1000 detailed product pages
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_book = {executor.submit(self.fetch_book_details, book): book for book in basic_books}
            for i, future in enumerate(as_completed(future_to_book), 1):
                try:
                    completed_book = future.result()
                    self.all_books.append(completed_book)
                    if i % 100 == 0:
                        logger.info(f"Processed {i}/{len(basic_books)} details...")
                except Exception as e:
                    logger.error(f"Error fetching details: {e}")
                    
        self.save_results()

    def save_results(self):
        """Saves data to CSV and database."""
        logger.info(f"Saving {len(self.all_books)} records...")
        df = pd.DataFrame(self.all_books)
        
        os.makedirs("data", exist_ok=True)
        
        # Save snapshot
        df.to_csv("data/books.csv", index=False)
        logger.info("Saved snapshot to data/books.csv")
        
        # Save dated archive
        dated_file = f"data/books_{self.today}.csv"
        df.to_csv(dated_file, index=False)
        logger.info(f"Saved archive to {dated_file}")
        
        # Append to history
        history_file = "data/history.csv"
        if os.path.exists(history_file):
            df.to_csv(history_file, mode="a", header=False, index=False)
            logger.info(f"Appended to {history_file}")
        else:
            df.to_csv(history_file, mode="w", header=True, index=False)
            logger.info(f"Created {history_file}")
            
        # Save to PostgreSQL
        logger.info("Initiating database insertion...")
        save_to_postgres(df)
        logger.info("Scraping and database insertion complete!")

if __name__ == "__main__":
    scraper = BookScraper()
    scraper.run()
