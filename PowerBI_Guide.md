# Power BI Dashboard — Step-by-Step Implementation Guide

> **Companion Document**: This guide walks you through building the dashboard described in [power_bi_dashboard_design.md](power_bi_dashboard_design.md). Follow these steps in Power BI Desktop.

---

## 🔌 Step 1: Connect Power BI to PostgreSQL

1. Open **Power BI Desktop**.
2. Click **Get Data** → **PostgreSQL database** (or **Get Data** → **More...** → **Database** → **PostgreSQL database**).
3. Enter your connection details:
   - **Server**: `localhost`
   - **Database**: `price_monitor`
4. Choose **Import** mode and click **OK**.
5. Enter credentials:
   - **User name**: `postgres`
   - **Password**: *(Your PostgreSQL password from `.env`)*
6. In the **Navigator** pane, check both tables:
   - ✅ **`books_catalog`** — Dimension table (Title, Category, URL)
   - ✅ **`price_history`** — Fact table (Price, Rating, Stock, Date)
7. Click **Transform Data** to open **Power Query Editor**.

---

## 🧹 Step 2: Data Cleaning in Power Query

### Table A: `books_catalog`

Verify/set column types:

| Column | Data Type | Role |
|---|---|---|
| `upc` | Text | Primary Key |
| `title` | Text | Book name |
| `category` | Text | Genre |
| `product_url` | Text | Source URL |

### Table B: `price_history`

Verify/set column types:

| Column | Data Type | Notes |
|---|---|---|
| `upc` | Text | Foreign Key → `books_catalog[upc]` |
| `price` | Fixed Decimal Number | Currency (£) |
| `rating` | Whole Number | 1–5 scale (auto-parsed from text) |
| `stock_quantity` | Whole Number | Units available |
| `date_collected` | Date | Scrape timestamp |

### Add Calculated Columns (in `price_history`)

#### Column 1: Price Band

1. Select `price_history` in the left pane.
2. Click **Add Column** → **Conditional Column**.
3. Name: **`Price Band`**
4. Rules:
   - If `price` < `20` → `"Budget (< £20)"`
   - Else If `price` ≤ `40` → `"Mid-Range (£20–£40)"`
   - Else → `"Premium (> £40)"`

#### Column 2: Stock Alert

1. **Add Column** → **Conditional Column**.
2. Name: **`Stock Alert`**
3. Rules:
   - If `stock_quantity` = `0` → `"🔴 Out of Stock"`
   - Else If `stock_quantity` ≤ `2` → `"🟡 Low Stock"`
   - Else If `stock_quantity` ≤ `10` → `"🟢 Normal"`
   - Else → `"🔵 Overstocked"`

#### Column 3: Rating Tier

1. **Add Column** → **Conditional Column**.
2. Name: **`Rating Tier`**
3. Rules:
   - If `rating` ≥ `4` → `"⭐ High (4-5)"`
   - Else If `rating` = `3` → `"⚡ Medium (3)"`
   - Else → `"⚠️ Low (1-2)"`

4. Click **Close & Apply** to load both tables into Power BI.

---

## 🔗 Step 3: Configure Relationships (Model View)

1. Click the **Model View** icon (third icon on the left sidebar).
2. If not auto-detected, drag `books_catalog[upc]` → `price_history[upc]`.
3. Right-click the relationship line → **Properties**:
   - **Cardinality**: `One to many (1:*)`
   - **Cross filter direction**: `Single` (Dimension → Fact)
4. Click **OK**.

---

## 📐 Step 4: Create the `_Measures` Table

1. Click **Home** → **Enter Data**.
2. Leave the table empty. Click **Load**.
3. Rename the table to **`_Measures`** in the right pane.
4. Right-click `_Measures` → **New Measure** for each DAX formula below.

> **Tip**: Keeping all 32 measures in a single `_Measures` table is a consulting best practice for clean model organization.

---

## 📊 Step 5: Add All DAX Measures

### Core KPIs (M01–M06)

```dax
Total Books = DISTINCTCOUNT(books_catalog[upc])
```

```dax
Avg Price = AVERAGE(price_history[price])
```

```dax
Total Units = SUM(price_history[stock_quantity])
```

```dax
Total Stock Value = 
    SUMX(price_history, price_history[price] * price_history[stock_quantity])
```

```dax
Avg Rating = AVERAGE(price_history[rating])
```

```dax
Total Categories = DISTINCTCOUNT(books_catalog[category])
```

### Inventory Intelligence (M07–M11)

```dax
Out of Stock Count = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[stock_quantity] = 0
    )
```

```dax
Low Stock Count = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[stock_quantity] > 0,
        price_history[stock_quantity] <= 2
    )
```

```dax
Out of Stock % = DIVIDE([Out of Stock Count], [Total Books], 0)
```

```dax
Overstocked Count = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[stock_quantity] > 15
    )
```

```dax
Avg Stock Per Book = DIVIDE([Total Units], [Total Books], 0)
```

### Pricing Intelligence (M12–M19)

```dax
Max Price = MAX(price_history[price])
```

```dax
Min Price = MIN(price_history[price])
```

```dax
Price Range = [Max Price] - [Min Price]
```

```dax
Median Price = MEDIAN(price_history[price])
```

```dax
Price Std Dev = STDEV.P(price_history[price])
```

```dax
Price CV = DIVIDE([Price Std Dev], [Avg Price], 0)
```

```dax
Budget Share % = 
    DIVIDE(
        CALCULATE([Total Books], price_history[Price Band] = "Budget (< £20)"),
        [Total Books],
        0
    )
```

```dax
Premium Share % = 
    DIVIDE(
        CALCULATE([Total Books], price_history[Price Band] = "Premium (> £40)"),
        [Total Books],
        0
    )
```

### Rating & Quality Intelligence (M20–M23)

```dax
High Rated Books = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[rating] >= 4
    )
```

```dax
Low Rated Books = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[rating] <= 2
    )
```

```dax
Catalog Quality Index = DIVIDE([High Rated Books], [Total Books], 0)
```

```dax
Quality Price Ratio = DIVIDE([Avg Rating], [Avg Price], 0)
```

### Competitive Intelligence (M24–M32)

```dax
Pricing Power Index = 
    DIVIDE(
        AVERAGE(price_history[price]) - [Avg Price],
        [Avg Price],
        0
    )
```

```dax
Category Avg Price = 
    CALCULATE(
        AVERAGE(price_history[price]),
        ALLEXCEPT(books_catalog, books_catalog[category])
    )
```

```dax
Price vs Benchmark = 
    AVERAGE(price_history[price]) - [Category Avg Price]
```

```dax
Stock Velocity = DIVIDE([Total Units], [Total Books], 0)
```

```dax
Revenue Potential = 
    SUMX(price_history, price_history[price] * price_history[stock_quantity])
```

```dax
Market HHI = 
    SUMX(
        SUMMARIZE(
            books_catalog,
            books_catalog[category],
            "CatShare", DIVIDE(
                CALCULATE([Total Books]),
                CALCULATE([Total Books], ALL(books_catalog[category])),
                0
            )
        ),
        [CatShare] ^ 2
    )
```

```dax
Top Category Share = 
    MAXX(
        SUMMARIZE(
            books_catalog,
            books_catalog[category],
            "Share", DIVIDE(
                CALCULATE([Total Books]),
                CALCULATE([Total Books], ALL(books_catalog[category])),
                0
            )
        ),
        [Share]
    )
```

```dax
Opportunity Score = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[rating] >= 4,
        price_history[stock_quantity] <= 5
    )
```

```dax
Dead Stock Score = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[rating] <= 2,
        price_history[stock_quantity] > 10
    )
```

---

## 🖼️ Step 6: Build the 6 Report Pages

> **Refer to** [power_bi_dashboard_design.md](power_bi_dashboard_design.md) for the detailed layout blueprints, visual specifications, and field mappings for each page.

### Page Setup (Apply to ALL pages)

1. **Format** → **Page background** → Color: `#0A192F` (Corporate Navy)
2. **Format** → **Wallpaper** → Color: `#0A192F`
3. Add a **Text Box** at the top for the page title (18pt Bold, `#F8FAFC`)

### Page 1: Executive Overview

1. Add 4 **Card** visuals → drag measures: `[Total Books]`, `[Avg Price]`, `[Total Stock Value]`, `[Avg Rating]`
2. Format KPI values: 28pt Bold, Teal `#64FFDA`
3. Add **Clustered Column Chart** → X: `books_catalog[category]`, Y: `[Total Books]`
   - Apply Top N filter = 10, sort descending
4. Add **Donut Chart** → Legend: `price_history[rating]`, Values: `[Total Books]`
5. Add **Area Chart** → X: `price_history[date_collected]`, Y: `[Avg Price]`
6. Add 2 **Slicers**: `books_catalog[category]` (dropdown), `price_history[date_collected]` (range)

### Page 2: Pricing Analysis

1. Add 5 **Cards**: `[Avg Price]`, `[Max Price]`, `[Min Price]`, `[Median Price]`, `[Price CV]`
2. Add **Treemap** → Group: `books_catalog[category]`, Values: `[Total Stock Value]`
3. Add **Clustered Column** → X: `price_history[Price Band]`, Y: `[Total Books]`
4. Add **Matrix** → Rows: `category` > `title`, Values: `[Avg Price]`, `stock_quantity`, `[Total Stock Value]`
   - Apply data bars conditional formatting on Stock Value
5. Add **Slicers**: `Price Band` (tile buttons), `category` (searchable dropdown)

### Page 3: Inventory Analysis

1. Add 5 **Cards**: `[Total Units]`, `[Out of Stock Count]`, `[Low Stock Count]`, `[Overstocked Count]`, `[Avg Stock Per Book]`
   - Color `Out of Stock Count` card: Coral Red `#EF4444`
   - Color `Low Stock Count` card: Amber `#F59E0B`
2. Add **Matrix** → filter `stock_quantity ≤ 2`
   - Apply conditional BG formatting: Red for 0, Yellow for 1-2
3. Add **Scatter Plot** → X: `price`, Y: `stock_quantity`, Legend: `category`, Size: `[Revenue Potential]`
4. Add **Clustered Bar** → Y: `category`, X: `[Total Units]`
5. Add **Slicers**: `Stock Alert` (buttons), `category` (checkboxes)

### Page 4: Category Analysis

1. Add 5 **Cards**: `[Total Categories]`, Top category name, `[Avg Rating]`, `[Market HHI]`, `[Top Category Share]`
2. Add **Scatter Plot** (BCG Quadrant) → X: `[Avg Price]`, Y: `[Avg Rating]`, Details: `category`, Size: `[Total Units]`
   - Add constant reference lines at median price and median rating
3. Add **Funnel** → Group: `category`, Values: `[Total Stock Value]`
4. Add **Grouped Bar** → Y: `category`, Values: `[Total Books]` + `[Total Stock Value]`
5. Add **Slicers**: `category` (checkboxes), `date_collected` (range)

### Page 5: Rating & Quality Analysis

1. Add 5 **Cards**: `[Avg Rating]`, `[High Rated Books]`, `[Low Rated Books]`, `[Catalog Quality Index]`, `[Quality Price Ratio]`
2. Add **100% Stacked Bar** → Y: `category`, X: `[Total Books]`, Legend: `rating`
   - Color mapping: 1=`#EF4444`, 2=`#F97316`, 3=`#F59E0B`, 4=`#84CC16`, 5=`#22C55E`
3. Add **Scatter** → X: `price`, Y: `rating`, Details: `title`
   - Enable linear trend line
4. Add **Table** → Columns: `title`, `category`, `rating`, `stock_quantity`, `price`
   - Filter: `rating ≤ 2`, Sort: `stock_quantity` DESC
5. Add **Slicers**: `rating` (horizontal buttons), `category` (multi-select)

### Page 6: Competitive Intelligence

1. Add 5 **Cards**: `[Pricing Power Index]`, `[Opportunity Score]`, `[Dead Stock Score]`, `[Revenue Potential]`, `[Stock Velocity]`
2. Add **Waterfall** → Category: `category`, Y: `[Price vs Benchmark]`
3. Add **Bubble Chart** → X: `stock_quantity`, Y: `rating`, Size: `price`, Color: `category`
   - Add reference lines at rating=3 and stock=10
4. Add **Matrix** → Rows: `category`, Values: `[Avg Price]`, `[Category Avg Price]`, `[Price vs Benchmark]`, `[Avg Rating]`, `[Total Units]`
   - Apply conditional formatting (Red/Green) on `Price vs Benchmark`
5. Add **Slicers**: `category` (multi-select), `Price Band` (tiles)

---

## 🧭 Step 7: Navigation & UX Polish

### Add Page Navigation Bar

On each page:
1. Insert → **Button** → **Blank** for each page tab
2. Configure **Action** → Type: **Page Navigation** → Destination: target page
3. Style:
   - Active tab: Teal underline `#64FFDA`
   - Inactive tabs: Slate text `#94A3B8`
   - Background: transparent

### Create Bookmarks

1. **View** → **Bookmarks** pane → **Add**
2. Create these bookmarks:
   - **"Critical Alerts"** — Filter to Out of Stock + Low Stock only
   - **"Premium Products"** — Filter to Premium band + Rating ≥ 4
   - **"At Risk Items"** — Filter to Rating ≤ 2 AND Stock > 10

### Sync Slicers

1. **View** → **Sync slicers**
2. Sync `category` and `date_collected` slicers across all 6 pages

---

## ✅ Step 8: Verification Checklist

### Data Accuracy

Cross-check Power BI KPIs against direct PostgreSQL queries:

```sql
-- Verify Total Books
SELECT COUNT(DISTINCT upc) FROM books_catalog;

-- Verify Avg Price, Max, Min
SELECT AVG(price), MAX(price), MIN(price) FROM price_history;

-- Verify Total Stock
SELECT SUM(stock_quantity) FROM price_history;

-- Verify Out of Stock
SELECT COUNT(DISTINCT upc) FROM price_history WHERE stock_quantity = 0;
```

### Visual Verification

- [ ] All 6 pages use Corporate Navy background (`#0A192F`)
- [ ] KPI values display in Teal (`#64FFDA`) at 28pt Bold
- [ ] Navigation bar appears and works on all pages
- [ ] All cards have consistent border-radius and shadows
- [ ] Font is Inter or Segoe UI (no defaults)
- [ ] Slicers filter all visuals correctly
- [ ] Drill-through works from Pages 1, 2, and 5
- [ ] Bookmarks toggle filters correctly
- [ ] Export to PDF renders all 6 pages cleanly at 1280×720

### Model Verification

- [ ] Model View shows `books_catalog[upc] → price_history[upc]` (1:*)
- [ ] All 32 measures are in the `_Measures` table
- [ ] No circular dependency warnings
- [ ] All calculated columns exist in `price_history` (Price Band, Stock Alert, Rating Tier)
