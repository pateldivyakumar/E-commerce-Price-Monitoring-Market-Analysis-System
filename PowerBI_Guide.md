# Power BI Dashboard Implementation Guide

This guide details how to build a professional, executive-level **Price Monitoring & Competitive Intelligence Dashboard** in Power BI Desktop using the data collected by the scraper.

---

## 🎨 Dashboard Design Mockup
Below is the visual blueprint for your dashboard, showcasing the layout, KPI cards, category distribution, and average price trend analysis.

![Power BI Dashboard Mockup](file:///d:/Divyakumar/Data%20Scraping%20project/Price%20Monitoring%20System/screenshots/power_bi_dashboard_mockup.png)

---

## 🔌 Step 1: Connecting Power BI to the Data

You can load your scraped data into Power BI in two ways. Connecting to PostgreSQL is recommended for real-time dashboards, while connecting to CSV is simpler for static reporting.

### Option A: Connect to PostgreSQL (Recommended)
1. Open **Power BI Desktop**.
2. Click **Get Data** > **PostgreSQL database**.
3. Enter the server details (from your `.env` file):
   * **Server**: `localhost`
   * **Database**: `price_monitor`
4. Choose **Import** mode and click **OK**.
5. When prompted for credentials, select the **Database** tab:
   * **User name**: `postgres`
   * **Password**: *Your PostgreSQL Password*
6. Select the `books` table from the list and click **Transform Data** to open Power Query.

### Option B: Connect to CSV File
1. Click **Get Data** > **Text/CSV**.
2. Browse and select [history.csv](file:///d:/Divyakumar/Data%20Scraping%20project/Price%20Monitoring%20System/data/history.csv) from your `data/` folder.
3. Click **Transform Data**.

---

## 🧹 Step 2: Data Cleaning in Power Query
Once your table is loaded in the Power Query Editor, verify the data types:
1. **Title** & **URL** / **UPC** / **Category**: Set to **Text**.
2. **Price**: Set to **Fixed Decimal Number** (Currency).
3. **Rating** & **Stock_Quantity**: Set to **Whole Number**.
4. **Date_Collected**: Set to **Date**.

### Add a Calculated Column for Price Bands
To group books into budget, mid-range, and premium tiers:
1. Click **Add Column** > **Conditional Column**.
2. Name the column `Price Band`.
3. Set the rules:
   * *If* `Price` is less than `20` -> *Then* `"Budget"`
   * *If* `Price` is less than or equal to `40` -> *Then* `"Mid-Range"`
   * *Else* -> `"Premium"`
4. Click **Close & Apply** to load the data into the model.

---

## 📊 Step 3: DAX Measures (Business Calculations)
Create these measures to calculate key metrics for your visuals. Right-click the `books` table, select **New Measure**, and paste the DAX code:

### 1. Total Unique Products
Counts the total number of distinct book titles in the inventory.
```dax
Total Books = DISTINCTCOUNT(books[title])
```

### 2. Average Price
Calculates the average price across all products.
```dax
Average Price = AVERAGE(books[price])
```

### 3. Total Inventory Stock
Sums the total number of copies available in stock.
```dax
Total Items in Stock = SUM(books[stock_quantity])
```

### 4. Total Stock Value
Calculates the total value of all stock in the warehouse by multiplying each book's price by its remaining copies.
```dax
Total Stock Value = SUMX(books, books[price] * books[stock_quantity])
```

### 5. Average Star Rating
Calculates the average rating (1–5) of the catalog.
```dax
Average Rating = AVERAGE(books[rating])
```

---

## 🖼️ Step 4: Building the Visualizations

### 1. KPI Cards (Top Banner)
Create three **Card** visuals across the top of the canvas to show:
* **Card 1**: `Total Books`
* **Card 2**: `Average Price` (Format as Currency: `£`)
* **Card 3**: `Total Stock Value` (Format as Currency: `£`)

### 2. Genre Distribution (Left Column)
* **Visual Type**: **Clustered Bar Chart** (Horizontal).
* **Y-Axis**: `Category`
* **X-Axis**: `Total Books`
* *Insight*: Highlights which categories dominate the catalog (e.g., *Default*, *Nonfiction*).

### 3. Pricing Tier Breakdown (Right Column)
* **Visual Type**: **Donut Chart** or **Pie Chart**.
* **Legend**: `Price Band`
* **Values**: `Total Books`
* *Insight*: Displays market segmentation (Budget vs. Premium products).

### 4. Historical Price Trend (Bottom Section)
* **Visual Type**: **Line Chart**.
* **X-Axis**: `Date_Collected`
* **Y-Axis**: `Average Price`
* *Insight*: Tracks whether overall bookstore prices are inflating or deflating over time.

### 5. Slicers (User Interaction)
Add two **Slicers** at the top right of the dashboard:
* **Slicer 1**: `Category` (allows users to zoom into specific genres like *Travel* or *Mystery*).
* **Slicer 2**: `Rating` (helps analyze premium highly-rated vs low-rated products).

---

## 📈 Business Insights Enabled by This Dashboard
* **Inventory Value Optimization**: By viewing **Total Stock Value** alongside **Stock Quantity**, managers can quickly identify where working capital is locked up.
* **Pricing Elasticity**: Allows the company to spot price changes and track if competitor prices are dropping, helping to time promotions.
* **Stock Scarcity Warnings**: You can create a tabular view sorted by `Stock_Quantity` ascending to flag items about to go out of stock, triggering automated restocks.
