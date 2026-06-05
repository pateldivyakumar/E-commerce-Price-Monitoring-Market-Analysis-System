# Power BI Dashboard Design Document: Price & Competitive Intelligence
**Role**: Senior Business Intelligence Consultant  
**Data Source**: PostgreSQL `price_monitor` database (`books` table)  
**Layout Theme**: Modern Dark Mode (Navy `#0A192F`, Teal `#64FFDA`, Slate `#8892B0`, Accent Lime `#A2FF0A`)

---

## 🛠️ Global DAX Measures Table
Create these measures in your model first. They will be reused across multiple pages:

```dax
-- 1. Total Catalog Depth
Total Books = DISTINCTCOUNT(books[title])

-- 2. Average Price of Catalog
Average Price = AVERAGE(books[price])

-- 3. Total Inventory Units
Total Units in Stock = SUM(books[stock_quantity])

-- 4. Total Capital Locked in Inventory
Total Stock Value = SUMX(books, books[price] * books[stock_quantity])

-- 5. Average Quality Score (Rating)
Average Rating = AVERAGE(books[rating])

-- 6. Out of Stock Alert (Units = 0)
Out of Stock Count = CALCULATE(COUNT(books[title]), books[stock_quantity] = 0)

-- 7. Scarce Stock Alert (Units <= 2)
Low Stock Count = CALCULATE(COUNT(books[title]), books[stock_quantity] <= 2 && books[stock_quantity] > 0)
```

---

## 📄 Page 1: Executive Overview
**Objective**: Provide high-level stakeholders with an immediate snapshot of catalog depth, total inventory value, average pricing, and overall ratings.

### 1. KPI Cards (Banner)
* **Visual 1**: `Total Books` (Format: Integer)
* **Visual 2**: `Total Stock Value` (Format: Currency `£`, 0 decimal places)
* **Visual 3**: `Total Units in Stock` (Format: Integer with thousands separator)
* **Visual 4**: `Average Rating` (Format: Decimal, `0.0` stars)

### 2. Visualization Layout
* **Visual A: Clustered Column Chart (Top Genres)**
  * *X-Axis*: `Category`
  * *Y-Axis*: `Total Books`
  * *Sorting*: Descending by book count (Limit to Top 10)
  * *Formatting*: Data labels enabled.
* **Visual B: Donut Chart (Rating Distribution)**
  * *Legend*: `Rating` (1 to 5)
  * *Values*: `Total Books`
  * *Formatting*: Percent of total.
* **Visual C: Area Chart (Average Price Trend)**
  * *X-Axis*: `Date_Collected`
  * *Y-Axis*: `Average Price`
  * *Formatting*: Smooth line, markers enabled.

### 3. Slicers & Filters
* **Slicer**: `Date_Collected` (Date Range slider)
* **Slicer**: `Category` (Dropdown list)

### 📊 Business Insights
* Identifies which genres drive the most inventory volume.
* Tracks pricing stability and fluctuations across scrape dates (daily trends).
* Audits the overall quality profile of the bookstore (share of highly-rated vs. poorly-rated books).

---

## 📄 Page 2: Pricing Analysis
**Objective**: Analyze pricing tiers, capital concentration, and product price distribution to optimize margins.

### 1. KPI Cards (Banner)
* **Visual 1**: `Average Price` (Format: Currency `£`)
* **Visual 2**: Maximum Book Price (`MAX(books[price])`)
* **Visual 3**: Minimum Book Price (`MIN(books[price])`)

### 2. Visualization Layout
* **Visual A: Treemap (Capital Concentration by Genre)**
  * *Group*: `Category`
  * *Values*: `Total Stock Value`
  * *Formatting*: Data labels with currency value.
  * *Insight*: Highlights which genres hold the most financial value (locked-up capital).
* **Visual B: Column Chart (Pricing Buckets)**
  * *X-Axis*: `Price Band` (Calculated in Power Query: Budget <£20, Mid-Range £20-£40, Premium >£40)
  * *Y-Axis*: `Total Books`
  * *Formatting*: Sort by Price Band order.
* **Visual C: Matrix Visual (Detailed Product Pricing Ledger)**
  * *Rows*: `Category` > `Title`
  * *Values*: `Average Price`, `Stock_Quantity`, `Total Stock Value`
  * *Formatting*: Conditional formatting (data bars) applied to the `Total Stock Value` column.

### 3. Slicers & Filters
* **Slicer**: `Price Band` (Horizontal buttons/tiles)
* **Slicer**: `Category` (Searchable list)

### 📊 Business Insights
* Detects price skewness. For example, if 80% of books are in the premium tier, it highlights a low-volume, high-margin inventory strategy.
* Identifies categories where capital is heavily concentrated (e.g., a category with few books but high stock values, indicating high financial risk).

---

## 📄 Page 3: Inventory Analysis
**Objective**: Operational analytics focusing on warehouse stock counts, inventory turnover risks, and stockout prevention.

### 1. KPI Cards (Banner)
* **Visual 1**: `Total Units in Stock`
* **Visual 2**: `Out of Stock Count` (Format: Red callout value if > 0)
* **Visual 3**: `Low Stock Count` (Format: Yellow callout value if > 0)

### 2. Visualization Layout
* **Visual A: Matrix (Stock Alerts & Procurement List)**
  * *Rows*: `Title` (Filtered where `Stock_Quantity <= 2`)
  * *Columns/Values*: `UPC`, `Category`, `Stock_Quantity`, `Price`, `Product_URL` (formatted as clickable web URL)
  * *Formatting*: Apply conditional formatting background color to `Stock_Quantity` (Red for 0, Yellow for 1-2).
* **Visual B: Scatter Plot (Velocity vs Capital)**
  * *X-Axis*: `Price`
  * *Y-Axis*: `Stock_Quantity`
  * *Legend*: `Category`
  * *Insight*: Reveals if expensive books have low stock (safe) or if cheap books have low stock (restock priority).
* **Visual C: Bar Chart (Stock Volatility)**
  * *Y-Axis*: `Category`
  * *X-Axis*: `Total Units in Stock`

### 3. Slicers & Filters
* **Slicer**: Stock Alert Status (Calculated column: `IF(Stock <= 0, "Out of Stock", IF(Stock <= 2, "Low Stock", "In Stock"))`)
* **Filter**: Page-level filter excluding historical runs to only show *current day* stock.

### 📊 Business Insights
* Generates an instant, clickable restocking order list for the procurement team.
* Flags "dead stock" (books with high prices, low ratings, and high stock levels) that are consuming warehouse space without generating sales.

---

## 📄 Page 4: Category (Genre) Analysis
**Objective**: Compare category performance, profitability, and catalog depth to guide purchasing budgets.

### 1. KPI Cards (Banner)
* **Visual 1**: Total Categories (`DISTINCTCOUNT(books[category])`)
* **Visual 2**: Top Category by Stock Value
* **Visual 3**: Average Category Rating

### 2. Visualization Layout
* **Visual A: Funnel Chart (Category Share of Inventory Value)**
  * *Group*: `Category`
  * *Values*: `Total Stock Value`
  * *Formatting*: Show percentage of first and percentage of previous.
* **Visual B: Scatter Plot (Category Performance Quadrant)**
  * *X-Axis*: `Average Price`
  * *Y-Axis*: `Average Rating`
  * *Details*: `Category`
  * *Size*: `Total Units in Stock`
  * *Insight*: Divides categories into 4 quadrants: Premium/High-Quality, Budget/High-Quality, Premium/Low-Quality (Avoid), Budget/Low-Quality.
* **Visual C: Multi-row Card**
  * Displays the top 3 and bottom 3 categories sorted by average rating.

### 3. Slicers & Filters
* **Slicer**: `Category` (Multi-select checkbox list)
* **Slicer**: `Date_Collected`

### 📊 Business Insights
* Identifies which categories are "Cash Cows" (high stock value, high ratings) and which are "Dogs" (low stock, low ratings).
* Helps the category manager distribute purchasing budgets proportionally based on category demand and value share.

---

## 📄 Page 5: Rating & Catalog Quality Analysis
**Objective**: Audit the quality of the catalog to ensure customer satisfaction and brand alignment.

### 1. KPI Cards (Banner)
* **Visual 1**: `Average Rating` (Stars format)
* **Visual 2**: Highly Rated Books (`CALCULATE(COUNT(books[title]), books[rating] >= 4)`)
* **Visual 3**: Low Rated Books (`CALCULATE(COUNT(books[title]), books[rating] <= 2)`)

### 2. Visualization Layout
* **Visual A: 100% Stacked Bar Chart (Rating Composition)**
  * *Y-Axis*: `Category`
  * *X-Axis*: `Total Books`
  * *Legend*: `Rating` (1 to 5)
  * *Formatting*: Colors mapped from Red (1-star) to Green (5-star).
  * *Insight*: Instantly flags genres with low-quality books (heavy red bars).
* **Visual B: Scatter Chart (Rating vs. Price Correlation)**
  * *X-Axis*: `Price`
  * *Y-Axis*: `Average Rating`
  * *Details*: `Title`
  * *Insight*: Checks if customer satisfaction correlates with price.
* **Visual C: Table (Critical Review/Defect List)**
  * *Columns*: `Title`, `UPC`, `Category`, `Rating`, `Stock_Quantity`, `Price`
  * *Filter*: Filtered where `Rating = 1` or `Rating = 2` and sorted by `Stock_Quantity` descending.
  * *Insight*: Flags highly overstocked but poorly reviewed books.

### 3. Slicers & Filters
* **Slicer**: `Rating` (1 to 5 selection)
* **Slicer**: `Category`

### 📊 Business Insights
* Flags catalog items that represent quality control risks.
* Informs marketing teams which genres are safe to promote (high average ratings) and which are risky (low average ratings).
