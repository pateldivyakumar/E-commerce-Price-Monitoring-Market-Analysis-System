-- ============================================================
-- SQL Analysis Queries - Price Monitoring System
-- Goal: Query the books database to gather market intelligence.
-- ============================================================

-- 1. Total Number of Book Scrapes Stored
-- Counts every row in the books table.
SELECT COUNT(*) AS total_scraped_records 
FROM books;


-- 2. Average Price of All Stored Books
-- Calculates the average price across all collected records.
SELECT ROUND(AVG(price), 2) AS average_price 
FROM books;


-- 3. Top 10 Most Expensive Books
-- Sorts all books from highest to lowest price and limits results to 10.
SELECT title, price, category, product_url
FROM books
ORDER BY price DESC
LIMIT 10;


-- 4. Count of Books in Each Category (Genre Distribution)
-- Groups the books by category, counts them, and sorts from most to least popular.
SELECT category, COUNT(*) AS book_count
FROM books
GROUP BY category
ORDER BY book_count DESC;


-- 5. Average Price by Category
-- Calculates the average book price for each category, helping identify premium genres.
SELECT category, ROUND(AVG(price), 2) AS average_price, COUNT(*) AS book_count
FROM books
GROUP BY category
ORDER BY average_price DESC;


-- 6. Total Inventory Stock Level by Category
-- Sums the stock_quantity for each category to find where inventory is concentrated.
SELECT category, SUM(stock_quantity) AS total_items_in_stock
FROM books
GROUP BY category
ORDER BY total_items_in_stock DESC;


-- 7. Scarce Inventory Alert (Books with lowest stock)
-- Finds the books with only 1 or 2 copies remaining in stock.
SELECT title, category, stock_quantity, product_url
FROM books
WHERE stock_quantity <= 2
ORDER BY stock_quantity ASC
LIMIT 15;


-- 8. Duplicate Scrapes Audit (Check how many times each book has been scraped)
-- Groups by title and UPC to find historical tracking counts.
SELECT title, upc, COUNT(*) AS scrape_runs_logged
FROM books
GROUP BY title, upc
ORDER BY scrape_runs_logged DESC
LIMIT 10;
