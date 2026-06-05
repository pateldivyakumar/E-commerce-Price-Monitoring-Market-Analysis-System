# Power BI Dashboard Implementation Guide (PostgreSQL Star Schema)

This guide details how to build a professional, executive-level **Price Monitoring & Competitive Intelligence Dashboard** in Power BI Desktop using the normalized PostgreSQL Star Schema tables (`books_catalog` and `price_history`).

---

## 🎨 Dashboard Design Mockup
Below is the visual blueprint for your dashboard, showcasing the layout, KPI cards, category distribution, and average price trend analysis.

![Power BI Dashboard Mockup](/screenshots/power_bi_dashboard_mockup.png)

---

## 🔌 Step 1: Connecting Power BI to PostgreSQL

1. Open **Power BI Desktop**.
2. Click **Get Data** > **PostgreSQL database** (or click **Get Data** > **More...** > **Database** > **PostgreSQL database**).
3. Enter your connection details:
   * **Server**: `localhost`
   * **Database**: `price_monitor`
4. Choose **Import** mode and click **OK**.
5. Select the database credentials tab:
   * **User name**: `postgres`
   * **Password**: *Your PostgreSQL password* (the one in your `.env` file).
6. In the Navigator pane, check both tables:
   * **`books_catalog`** (Dimension table containing Title, Category, URL)
   * **`price_history`** (Fact table containing Price, Rating, Stock, Date)
7. Click **Transform Data** to open the **Power Query Editor**.

---

## 🧹 Step 2: Data Cleaning & Power Query Setup

In the Power Query Editor, we must verify the columns and data types for both tables to ensure calculations work properly.

### Table A: `books_catalog`
Verify/set the following column types:
* **`upc`**: Text (Primary Key)
* **`title`**: Text
* **`category`**: Text
* **`product_url`**: Text

### Table B: `price_history`
Verify/set the following column types:
* **`upc`**: Text (Foreign Key)
* **`price`**: **Fixed Decimal Number** (Currency)
* **`rating`**: **Whole Number** (Since the database stores ratings as string numbers e.g. `"3"`, changing this type to *Whole Number* will automatically parse them to numbers 1–5).
* **`stock_quantity`**: **Whole Number**
* **`date_collected`**: **Date**

### Add a Calculated Column for Price Bands (in `price_history`)
To segment books into budget, mid-range, and premium tiers:
1. Select the `price_history` query in the left pane.
2. Click **Add Column** > **Conditional Column** from the top ribbon.
3. Name the column **`Price Band`**.
4. Set the rules:
   * *If* `price` is less than `20` -> *Then* `"Budget"`
   * *If* `price` is less than or equal to `40` -> *Then* `"Mid-Range"`
   * *Else* -> `"Premium"`
5. Click **Close & Apply** to load both tables into Power BI.

---

## 🔗 Step 3: Configure Table Relationships (Model View)

Power BI usually detects relationships automatically. To verify or set it manually:
1. Click the **Model View** icon (the third icon on the far-left sidebar: three boxes linked together).
2. You should see two cards: `books_catalog` and `price_history`.
3. If they are not linked, drag the **`upc`** column from `books_catalog` and drop it onto the **`upc`** column in `price_history`.
4. Right-click the relationship line and select **Properties**:
   * **Cardinality**: `One to many (1:*)` (One book in catalog has many daily prices in history).
   * **Cross filter direction**: `Single` (`books_catalog` filters `price_history`).
   * Click **OK**.

---

## 📊 Step 4: DAX Measures (Business Calculations)

Select the **Report View** (first icon on the left sidebar). Right-click the **`price_history`** table in the right pane, select **New Measure**, and write these DAX formulas:

### 1. Total Unique Products
Counts the total number of unique books in our inventory catalog.
```dax
Total Books = DISTINCTCOUNT(books_catalog[upc])
```

### 2. Average Price
Calculates the average price across all scraped listings.
```dax
Average Price = AVERAGE(price_history[price])
```

### 3. Total Inventory Stock
Sums the total number of book copies available.
```dax
Total Items in Stock = SUM(price_history[stock_quantity])
```

### 4. Total Stock Value
Calculates the total monetary value of the current stock in the bookstore.
```dax
Total Stock Value = SUMX(price_history, price_history[price] * price_history[stock_quantity])
```

### 5. Average Star Rating
Calculates the average rating (1–5) of the inventory.
```dax
Average Rating = AVERAGE(price_history[rating])
```

---

## 🖼️ Step 5: Building the Dashboard Visuals

### 1. KPI Cards (Top Banner)
Add three **Card** visuals across the top of your canvas:
* **Card 1 (Total Books)**: Drag the `Total Books` measure here.
* **Card 2 (Average Price)**: Drag the `Average Price` measure. Format as Currency (£).
* **Card 3 (Total Stock Value)**: Drag the `Total Stock Value` measure. Format as Currency (£).

### 2. Genre Distribution (Left Column)
* **Visual Type**: **Clustered Bar Chart** (Horizontal).
* **Y-Axis**: `books_catalog[category]`
* **X-Axis**: `Total Books` (or `DISTINCTCOUNT(books_catalog[upc])`)
* *Description*: Shows which genres have the most titles.

### 3. Price Segment Breakdown (Right Column)
* **Visual Type**: **Donut Chart** or **Pie Chart**.
* **Legend**: `price_history[Price Band]`
* **Values**: `Total Books`
* *Description*: Displays market segmentation (Budget vs. Premium products).

### 4. Historical Price Trend (Bottom Section)
* **Visual Type**: **Line Chart**.
* **X-Axis**: `price_history[date_collected]`
* **Y-Axis**: `Average Price`
* *Description*: Tracks price inflation/deflation over time.

### 5. Slicers (Interactive Filters)
Add two **Slicers** at the top right of the dashboard:
* **Slicer 1**: `books_catalog[category]` (select specific genres to filter the page).
* **Slicer 2**: `price_history[rating]` (filter by star rating 1-5).
