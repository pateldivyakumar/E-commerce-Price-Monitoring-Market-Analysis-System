# 🏗️ Power BI Report Build Guide — Price Monitoring System
### From Zero to Enterprise Dashboard in Power BI Desktop

**Your Role**: You're building a 6-page, consulting-grade Power BI report that transforms your scraped e-commerce data into actionable competitive intelligence.

**What You Already Have**:
- ✅ PostgreSQL `price_monitor` database with star schema (`books_catalog` + `price_history`)
- ✅ CSV fallback data in `data/books.csv` and `data/history.csv`
- ✅ 1,000 products × 50 categories with price, rating, and stock data

---

## Phase 0: Prerequisites Checklist

Before opening Power BI, verify everything is ready:

| Requirement | How to Check | Status |
|---|---|---|
| Power BI Desktop installed | Open from Start Menu | ☐ |
| PostgreSQL running | Open pgAdmin or `psql -l` | ☐ |
| `price_monitor` database exists | `\l` in psql or check pgAdmin | ☐ |
| Tables populated | `SELECT COUNT(*) FROM books_catalog;` → should return 1000 | ☐ |
| `.env` has correct credentials | Check `DB_HOST`, `DB_USER`, `DB_PASSWORD` | ☐ |

> [!TIP]
> If PostgreSQL is not set up or you prefer a simpler start, you can connect Power BI directly to your **CSV files** instead. Instructions for both paths are provided below.

---

## Phase 1: Connect to Your Data

### Option A: Connect to PostgreSQL (Recommended)

1. Open **Power BI Desktop** → Click **Home** → **Get Data**
2. Search for **"PostgreSQL database"** → Select it → Click **Connect**

   > [!NOTE]
   > If you don't see PostgreSQL, you may need to install the **Npgsql** driver. Power BI will prompt you with a download link. Install it and restart Power BI.

3. Enter connection details:
   ```
   Server:    localhost
   Database:  price_monitor
   ```
4. Click **OK** → Select **Database** credentials tab
5. Enter:
   ```
   User name: postgres
   Password:  <your password from .env>
   ```
6. In the **Navigator** pane, check **both tables**:
   - ✅ `public.books_catalog`
   - ✅ `public.price_history`
7. Click **Transform Data** (NOT "Load" — we need to clean first)

### Option B: Connect to CSV Files (Fallback)

If PostgreSQL isn't available:

1. **Home** → **Get Data** → **Text/CSV**
2. Navigate to `d:\Divyakumar\Data Scraping project\Price Monitoring System\data\`
3. Load `books.csv` first → Click **Transform Data**
4. Repeat for `history.csv`

> [!IMPORTANT]
> With CSVs, you'll need to manually split the data into dimension + fact tables in Power Query (covered in Phase 2 below).

---

## Phase 2: Data Transformation in Power Query Editor

Power Query Editor is where you clean, type, and shape your data before it hits the data model.

### 2.1 — Verify Column Data Types

#### Table: `books_catalog` (Dimension)

| Column | Set Type To | How |
|---|---|---|
| `upc` | **Text** | Right-click column header → **Change Type** → **Text** |
| `title` | **Text** | Should auto-detect |
| `category` | **Text** | Should auto-detect |
| `product_url` | **Text** | Should auto-detect |

#### Table: `price_history` (Fact)

| Column | Set Type To | How |
|---|---|---|
| `id` | **Whole Number** | Auto-detected |
| `upc` | **Text** | Critical — must match `books_catalog[upc]` type |
| `price` | **Fixed Decimal Number** | Right-click → Change Type → Fixed Decimal |
| `rating` | **Whole Number** | ⚠️ See note below |
| `stock_quantity` | **Whole Number** | Should auto-detect |
| `date_collected` | **Date** | Right-click → Change Type → Date |

> [!WARNING]
> **Rating Column**: Your `rating` column stores values as text strings like `"Three"`, `"Five"`. If connecting from PostgreSQL with the star schema, ratings are already stored as text in `VARCHAR(20)`. You'll need to convert these to numbers.
> 
> In Power Query, go to **Add Column** → **Custom Column** and use this M formula:
> ```
> = if [rating] = "One" then 1 
>   else if [rating] = "Two" then 2 
>   else if [rating] = "Three" then 3 
>   else if [rating] = "Four" then 4 
>   else if [rating] = "Five" then 5 
>   else null
> ```
> Name it `Rating_Numeric`. Then delete the original `rating` column and rename `Rating_Numeric` to `rating`.
> 
> **However**, if your PostgreSQL schema already stores rating as a `SMALLINT` (from the optimized schema), this step is unnecessary — the values will already be 1–5 integers.

### 2.2 — Add Calculated Columns

These columns create the segmentation layers your report needs.

#### Column 1: `Price Band` (in `price_history`)

1. Select the `price_history` table in the left pane
2. Click **Add Column** → **Conditional Column**
3. Configure:

| Column Name | Operator | Value | Output |
|---|---|---|---|
| `price` | is less than | `20` | `Budget (< £20)` |
| `price` | is less than or equal to | `40` | `Mid-Range (£20–£40)` |
| Otherwise | | | `Premium (> £40)` |

4. Name: **`Price Band`**

#### Column 2: `Stock Alert` (in `price_history`)

1. **Add Column** → **Conditional Column**
2. Configure:

| Column Name | Operator | Value | Output |
|---|---|---|---|
| `stock_quantity` | equals | `0` | `🔴 Out of Stock` |
| `stock_quantity` | is less than or equal to | `2` | `🟡 Low Stock` |
| `stock_quantity` | is less than or equal to | `10` | `🟢 Normal` |
| Otherwise | | | `🔵 Overstocked` |

3. Name: **`Stock Alert`**

#### Column 3: `Rating Tier` (in `price_history`)

1. **Add Column** → **Conditional Column**
2. Configure:

| Column Name | Operator | Value | Output |
|---|---|---|---|
| `rating` | is greater than or equal to | `4` | `⭐ High (4-5)` |
| `rating` | equals | `3` | `⚡ Medium (3)` |
| Otherwise | | | `⚠️ Low (1-2)` |

3. Name: **`Rating Tier`**

### 2.3 — If Using CSVs: Create the Star Schema Manually

If you loaded from `books.csv` instead of PostgreSQL, you need to split it:

1. **Right-click** the `books` query → **Duplicate** → Rename to `books_catalog`
2. In `books_catalog`: Select only `UPC`, `Title`, `Category`, `URL` columns → Right-click → **Remove Other Columns**
3. **Home** → **Remove Rows** → **Remove Duplicates** (using `UPC`)
4. Rename `UPC` to `upc`, `Title` to `title`, etc. to match the schema

5. Go back to original `books` query → Rename to `price_history`
6. Keep columns: `UPC` (rename to `upc`), `Price` → `price`, `Rating` → `rating`, `Stock_Quantity` → `stock_quantity`, `Date_Collected` → `date_collected`
7. Remove `Title`, `Category`, `URL` (they live in the dimension table now)

### 2.4 — Click "Close & Apply"

Once all transformations are done, click **Home** → **Close & Apply** to load data into the model.

---

## Phase 3: Data Model Configuration

### 3.1 — Switch to Model View

Click the **Model View** icon (3rd icon in the left sidebar — looks like a diagram).

### 3.2 — Create the Star Schema Relationship

1. If not auto-detected, **drag** `books_catalog[upc]` onto `price_history[upc]`
2. A relationship line will appear
3. **Double-click** the line to edit:
   - **Cardinality**: `One to Many (1:*)`
   - **Cross filter direction**: `Single`
   - **Make this relationship active**: ✅ Yes
4. Click **OK**

Your model should look like:
```
┌──────────────────┐         ┌──────────────────┐
│  books_catalog   │  1 : *  │  price_history   │
│  (Dimension)     │────────▶│  (Fact)          │
│                  │   upc   │                  │
│  • upc (PK)     │         │  • id (PK)       │
│  • title         │         │  • upc (FK)      │
│  • category      │         │  • price         │
│  • product_url   │         │  • rating        │
│                  │         │  • stock_quantity │
│                  │         │  • date_collected │
│                  │         │  • Price Band     │
│                  │         │  • Stock Alert    │
│                  │         │  • Rating Tier    │
└──────────────────┘         └──────────────────┘
```

### 3.3 — Create the `_Measures` Table

This is a **critical best practice** — all DAX measures live in a dedicated table for clean organization.

1. **Home** → **Enter Data**
2. Leave the table completely empty (no rows, no columns needed beyond the default)
3. Click **Load**
4. In the **Data pane** (right sidebar), right-click the new table → **Rename** → `_Measures`

> [!TIP]
> The underscore prefix `_` forces this table to sort to the top of the table list, making it easy to find.

---

## Phase 4: DAX Measures (The Brain of Your Report)

Right-click `_Measures` → **New Measure** for each formula below. Copy-paste each one exactly.

### 4.1 — Core KPIs (M01–M06)

```dax
Total Books = DISTINCTCOUNT(books_catalog[upc])
```
*What it does*: Counts unique products in catalog (not duplicated across dates)

```dax
Avg Price = AVERAGE(price_history[price])
```
*What it does*: Mean price across all records

```dax
Total Units = SUM(price_history[stock_quantity])
```
*What it does*: Sum of all inventory units

```dax
Total Stock Value = 
    SUMX(price_history, price_history[price] * price_history[stock_quantity])
```
*What it does*: Total capital locked in inventory (price × quantity for each row, then sum)

```dax
Avg Rating = AVERAGE(price_history[rating])
```
*What it does*: Average customer rating across catalog

```dax
Total Categories = DISTINCTCOUNT(books_catalog[category])
```
*What it does*: Count of unique genres/categories

---

### 4.2 — Inventory Intelligence (M07–M11)

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

---

### 4.3 — Pricing Intelligence (M12–M19)

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
*What it does*: Coefficient of Variation — measures pricing consistency. CV > 0.5 = highly inconsistent pricing

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

---

### 4.4 — Rating & Quality Intelligence (M20–M23)

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
*What it does*: % of catalog rated 4+ stars — your quality scorecard

```dax
Quality Price Ratio = DIVIDE([Avg Rating], [Avg Price], 0)
```

---

### 4.5 — Competitive Intelligence (M24–M32)

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
*What it does*: Herfindahl-Hirschman Index — measures market concentration. <0.01 = competitive, >0.25 = concentrated

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
*What it does*: High-quality + low-stock items = restocking opportunities

```dax
Dead Stock Score = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[rating] <= 2,
        price_history[stock_quantity] > 10
    )
```
*What it does*: Low-quality + high-stock items = clearance candidates

### 4.6 — Strategic Action Measure (Bonus)

```dax
Strategic Action = 
    SWITCH(
        TRUE(),
        [Avg Rating] >= 4 && [Avg Stock Per Book] <= 5, "🟢 RESTOCK — High demand, low supply",
        [Avg Rating] <= 2 && [Avg Stock Per Book] > 10, "🔴 CLEARANCE — Low quality, excess stock",
        [Avg Rating] >= 4 && [Avg Stock Per Book] > 10, "🔵 PROMOTE — Quality product, push marketing",
        [Avg Rating] <= 2 && [Avg Stock Per Book] <= 5, "⚫ DELIST — Low quality, not worth restocking",
        "⚪ MAINTAIN — Normal operations"
    )
```

> [!IMPORTANT]
> After creating all measures, your `_Measures` table in the Data pane should show **33 measures**. If any are missing, right-click `_Measures` → **New Measure** and add them.

---

## Phase 5: Apply the Custom Theme

Before building pages, apply the dark corporate theme to avoid manual formatting on every visual.

### 5.1 — Create the Theme JSON

Save this file as `PriceMonitor_Theme.json` in your project folder:

```json
{
    "name": "PriceMonitor_Corporate",
    "dataColors": [
        "#64FFDA", "#38BDF8", "#F59E0B", "#EF4444", 
        "#22C55E", "#A78BFA", "#F97316", "#06B6D4",
        "#E879F9", "#84CC16"
    ],
    "background": "#0A192F",
    "foreground": "#F8FAFC",
    "tableAccent": "#64FFDA",
    "visualStyles": {
        "*": {
            "*": {
                "background": [{"color": {"solid": {"color": "#1E293B"}}}],
                "border": [{"color": {"solid": {"color": "#334155"}}, "radius": 8}],
                "title": [{
                    "fontColor": {"solid": {"color": "#94A3B8"}},
                    "fontSize": 10
                }]
            }
        }
    }
}
```

### 5.2 — Apply the Theme

1. In Power BI Desktop: **View** → **Themes** → **Browse for themes**
2. Select your `PriceMonitor_Theme.json`
3. Click **Open** → The entire report will adopt the dark corporate palette

---

## Phase 6: Build the 6 Report Pages

### Global Page Setup (Do This FIRST on Every Page)

For each new page:
1. Right-click the page tab → **Rename** to the page name
2. **Format pane** → **Page background** → Color: `#0A192F`, Transparency: 0%
3. **Format pane** → **Wallpaper** → Color: `#0A192F`
4. Insert a **Text Box** at the top (full width, 50px height):
   - Font: **Segoe UI Bold**, 18pt, Color: `#F8FAFC`
   - Background: `#1E293B` with 90% opacity

---

### 📄 PAGE 1: Executive Overview

**Rename tab**: `Executive Overview`

**Top title text**: `📊 EXECUTIVE OVERVIEW`

#### KPI Banner (Row 1 — Top Area, Below Title)

Add **4 Card visuals** side-by-side:

| Card | Measure | Format |
|---|---|---|
| Card 1 | `[Total Books]` | Title: "TOTAL BOOKS", Value: 28pt Bold Teal `#64FFDA` |
| Card 2 | `[Avg Price]` | Title: "AVG PRICE", Value: £ format, 2 decimals |
| Card 3 | `[Total Stock Value]` | Title: "TOTAL STOCK VALUE", Value: £ format, 0 decimals |
| Card 4 | `[Avg Rating]` | Title: "AVG RATING", Value: 1 decimal |

**Formatting each Card**:
- Click the card → **Format** pane → **Callout value** → Font size: 28, Color: `#64FFDA`
- **Category label** → Font size: 10, Color: `#94A3B8`, UPPERCASE
- **Card background** → Color: `#1E293B`, Rounded corners: 8px
- **Effects** → Shadow: ON

#### Visual A — Clustered Column Chart (Left, Below KPIs)

1. Insert → **Clustered Column Chart**
2. Drag: **X-axis**: `books_catalog[category]` | **Y-axis**: `[Total Books]`
3. **Format**:
   - Visual → **Filters on this visual** → Top N: `10`, By Value: `[Total Books]`, Sort: Descending
   - Data labels: ON, color `#F8FAFC`
   - X-axis labels: 9pt, color `#94A3B8`, angled 45°
   - Column color: `#64FFDA`
   - Title: "TOP 10 CATEGORIES BY BOOK COUNT"

#### Visual B — Donut Chart (Right of Column Chart)

1. Insert → **Donut Chart**
2. Drag: **Legend**: `price_history[rating]` | **Values**: `[Total Books]`
3. **Format**:
   - Show percentages in data labels
   - Colors: 1=`#EF4444`, 2=`#F97316`, 3=`#F59E0B`, 4=`#84CC16`, 5=`#22C55E`
   - Title: "RATING DISTRIBUTION"

#### Visual C — Area Chart (Full Width, Bottom)

1. Insert → **Area Chart**
2. Drag: **X-axis**: `price_history[date_collected]` | **Y-axis**: `[Avg Price]`
3. **Format**:
   - Line: smooth, color `#38BDF8`
   - Area fill: gradient from `#38BDF8` (20% opacity) to transparent
   - Markers: ON
   - Title: "AVERAGE PRICE TREND"

#### Slicers

1. Insert → **Slicer** → Drag `books_catalog[category]`
   - Style: Dropdown, Multi-select
   - Position: Top-right corner
2. Insert → **Slicer** → Drag `price_history[date_collected]`
   - Style: Between (date range slider)
   - Position: Next to category slicer

---

### 📄 PAGE 2: Pricing Analysis

**Rename tab**: `Pricing Analysis`

**Top title text**: `💰 PRICING ANALYSIS`

#### KPI Banner — 5 Cards

| Card | Measure | Notes |
|---|---|---|
| Avg Price | `[Avg Price]` | £ format |
| Max Price | `[Max Price]` | Coral Red `#EF4444` if > £50 (use conditional formatting) |
| Min Price | `[Min Price]` | Lime Green `#22C55E` |
| Median Price | `[Median Price]` | £ format |
| Price CV | `[Price CV]` | 2 decimal places, Amber `#F59E0B` if > 0.5 |

#### Visual A — Treemap (Left)

1. Insert → **Treemap**
2. **Group**: `books_catalog[category]` | **Values**: `[Total Stock Value]`
3. Data labels with £ values
4. Title: "CAPITAL CONCENTRATION BY CATEGORY"

#### Visual B — Clustered Column (Right)

1. Insert → **Clustered Column Chart**
2. **X-axis**: `price_history[Price Band]` | **Y-axis**: `[Total Books]`
3. Custom sort order: Budget → Mid-Range → Premium
4. Title: "PRICE BAND DISTRIBUTION"

#### Visual C — Matrix (Bottom, Full Width)

1. Insert → **Matrix**
2. **Rows**: `books_catalog[category]` (expand into `books_catalog[title]`)
3. **Values**: `[Avg Price]`, `stock_quantity`, `[Total Stock Value]`
4. **Conditional Formatting**: Right-click `Total Stock Value` → **Conditional formatting** → **Data bars** → Teal `#64FFDA`
5. Title: "DETAILED PRICING LEDGER"

#### Slicers

- `Price Band` → Tile/button style
- `category` → Searchable dropdown

---

### 📄 PAGE 3: Inventory Analysis

**Rename tab**: `Inventory Analysis`

**Top title text**: `📦 INVENTORY ANALYSIS`

#### KPI Banner — 5 Cards

| Card | Measure | Color |
|---|---|---|
| Total Units | `[Total Units]` | Teal `#64FFDA` |
| Out of Stock | `[Out of Stock Count]` | 🔴 Coral Red `#EF4444` |
| Low Stock | `[Low Stock Count]` | 🟡 Amber `#F59E0B` |
| Overstocked | `[Overstocked Count]` | 🔵 Ice Blue `#38BDF8` |
| Avg Stock/Book | `[Avg Stock Per Book]` | Default |

#### Visual A — Matrix / Procurement List (Left)

1. Insert → **Matrix**
2. **Rows**: `title` | **Values**: `upc`, `category`, `stock_quantity`, `price`
3. **Filter**: `stock_quantity` ≤ 2
4. **Conditional Formatting** on `stock_quantity`:
   - Background color: Rules-based
   - If value = 0 → Red `#EF4444`
   - If value ≤ 2 → Yellow `#F59E0B`
5. Title: "⚠️ PROCUREMENT PRIORITY LIST"

#### Visual B — Scatter Plot (Right)

1. Insert → **Scatter Chart**
2. **X-axis**: `price_history[price]` | **Y-axis**: `price_history[stock_quantity]`
3. **Legend**: `books_catalog[category]` | **Size**: `[Revenue Potential]`
4. Add **Reference Lines**:
   - X-axis: Constant line at median price (~£35)
   - Y-axis: Constant line at median stock (~15)
5. Title: "PRICE vs STOCK QUADRANT"

#### Visual C — Clustered Bar (Bottom)

1. Insert → **Clustered Bar Chart**
2. **Y-axis**: `books_catalog[category]` | **X-axis**: `[Total Units]`
3. Sort descending, data labels ON
4. Title: "STOCK DISTRIBUTION BY CATEGORY"

#### Slicers

- `Stock Alert` → Button style (🔴 🟡 🟢 🔵)
- `category` → Multi-select checkbox

---

### 📄 PAGE 4: Category Analysis

**Rename tab**: `Category Analysis`

**Top title text**: `📚 CATEGORY ANALYSIS`

#### KPI Banner — 5 Cards

| Card | Measure |
|---|---|
| Total Categories | `[Total Categories]` |
| Top Category | Use a card with TOPN logic or manually note "Sequential Art" |
| Avg Rating | `[Avg Rating]` |
| Market HHI | `[Market HHI]` — 3 decimal places |
| Top Cat Share | `[Top Category Share]` — % format |

#### Visual A — BCG Scatter Plot (Left)

1. Insert → **Scatter Chart**
2. **X-axis**: `[Avg Price]` | **Y-axis**: `[Avg Rating]`
3. **Details**: `books_catalog[category]` | **Size**: `[Total Units]`
4. Add **Reference Lines**:
   - X-axis: Median of `[Avg Price]`
   - Y-axis: Median of `[Avg Rating]`
5. These lines create 4 quadrants (BCG Matrix):
   - **Top-Right** = Stars (High Price + High Rating)
   - **Top-Left** = Cash Cows (Low Price + High Rating)
   - **Bottom-Right** = Question Marks
   - **Bottom-Left** = Dogs
6. Title: "BCG QUADRANT — CATEGORY STRATEGY"

#### Visual B — Funnel Chart (Right)

1. Insert → **Funnel Chart**
2. **Group**: `books_catalog[category]` | **Values**: `[Total Stock Value]`
3. Top N filter = 15
4. Title: "TOP 15 CATEGORIES BY STOCK VALUE"

#### Visual C — Grouped Bar (Bottom)

1. Insert → **Clustered Bar Chart** (grouped mode)
2. **Y-axis**: `books_catalog[category]`
3. **X-axis**: `[Total Books]` and `[Total Stock Value]` (side-by-side)
4. Title: "VOLUME vs VALUE COMPARISON"

---

### 📄 PAGE 5: Rating & Quality Analysis

**Rename tab**: `Rating & Quality`

**Top title text**: `⭐ RATING & QUALITY ANALYSIS`

#### KPI Banner — 5 Cards

| Card | Measure | Color |
|---|---|---|
| Avg Rating | `[Avg Rating]` | Default |
| High Rated | `[High Rated Books]` | Lime Green `#22C55E` |
| Low Rated | `[Low Rated Books]` | Coral Red `#EF4444` |
| Quality Index | `[Catalog Quality Index]` | % format, Teal if > 50% |
| Q/P Ratio | `[Quality Price Ratio]` | 3 decimal places |

#### Visual A — 100% Stacked Bar (Left)

1. Insert → **100% Stacked Bar Chart**
2. **Y-axis**: `books_catalog[category]` | **X-axis**: `[Total Books]` | **Legend**: `price_history[rating]`
3. **Color mapping**:
   - 1 star = `#EF4444` (Red)
   - 2 stars = `#F97316` (Orange)
   - 3 stars = `#F59E0B` (Amber)
   - 4 stars = `#84CC16` (Light Green)
   - 5 stars = `#22C55E` (Green)
4. Title: "RATING COMPOSITION BY CATEGORY"

#### Visual B — Scatter with Trend (Right)

1. Insert → **Scatter Chart**
2. **X-axis**: `price_history[price]` | **Y-axis**: `price_history[rating]`
3. **Details**: `books_catalog[title]`
4. **Analytics pane** → **Trend line** → ON (Linear)
5. Title: "PRICE vs QUALITY CORRELATION"

#### Visual C — Table (Bottom)

1. Insert → **Table**
2. **Columns**: `title`, `category`, `rating`, `stock_quantity`, `price`
3. **Filter**: `rating` ≤ 2
4. **Sort**: `stock_quantity` descending
5. **Conditional Formatting**: Highlight rows where `stock_quantity > 10` with red background
6. Title: "⚠️ QUALITY DEFECT LIST — LOW RATED HIGH STOCK"

---

### 📄 PAGE 6: Competitive Intelligence

**Rename tab**: `Intelligence`

**Top title text**: `🎯 COMPETITIVE INTELLIGENCE`

#### KPI Banner — 5 Cards

| Card | Measure | Color Logic |
|---|---|---|
| Pricing Power | `[Pricing Power Index]` | Green if positive, Red if negative |
| Opportunity Score | `[Opportunity Score]` | Teal |
| Dead Stock | `[Dead Stock Score]` | Coral Red |
| Revenue Potential | `[Revenue Potential]` | £ format |
| Stock Velocity | `[Stock Velocity]` | Decimal |

#### Visual A — Waterfall Chart (Left)

1. Insert → **Waterfall Chart**
2. **Category**: `books_catalog[category]` | **Y-axis**: `[Price vs Benchmark]`
3. Colors: Green = above benchmark, Red = below benchmark
4. Title: "PRICE vs CATEGORY BENCHMARK"

#### Visual B — Bubble Chart (Right)

1. Insert → **Scatter Chart** (bubble mode)
2. **X-axis**: `price_history[stock_quantity]` | **Y-axis**: `price_history[rating]`
3. **Size**: `price_history[price]` | **Color**: `books_catalog[category]`
4. **Reference Lines**: rating=3 (horizontal), stock=10 (vertical)
5. Title: "OPPORTUNITY MATRIX"

#### Visual C — Strategic Matrix (Bottom)

1. Insert → **Matrix**
2. **Rows**: `books_catalog[category]`
3. **Values**: `[Avg Price]`, `[Category Avg Price]`, `[Price vs Benchmark]`, `[Avg Rating]`, `[Total Units]`
4. **Conditional Formatting** on `Price vs Benchmark`:
   - Rules: Negative → Red background, Positive → Green background
5. Title: "STRATEGIC ACTION DASHBOARD"

---

## Phase 7: Navigation & UX Polish

### 7.1 — Page Navigation Bar

On **every page**, add a navigation bar:

1. **Insert** → **Buttons** → **Blank**
2. Create 6 buttons, one for each page:

| Button Text | Action Type | Destination |
|---|---|---|
| Executive Overview | Page Navigation | Page 1 |
| Pricing | Page Navigation | Page 2 |
| Inventory | Page Navigation | Page 3 |
| Categories | Page Navigation | Page 4 |
| Ratings | Page Navigation | Page 5 |
| Intelligence | Page Navigation | Page 6 |

3. **Format each button**:
   - Fill: Transparent
   - Text: `Segoe UI`, 10pt
   - Active page: Text color `#64FFDA`, underline
   - Inactive pages: Text color `#94A3B8`
4. Arrange horizontally in the title bar area
5. **Copy-paste** the button group to all pages (update active state per page)

### 7.2 — Create Bookmarks

1. **View** → **Bookmarks** pane
2. Click **Add** for each:
   - **"Critical Alerts"**: Filter to `Stock Alert` = 🔴 or 🟡
   - **"Premium Products"**: Filter `Price Band` = Premium AND `rating` ≥ 4
   - **"At Risk Items"**: Filter `rating` ≤ 2 AND `stock_quantity` > 10
3. Add bookmark buttons to relevant pages

### 7.3 — Sync Slicers

1. Click on a slicer → **View** → **Sync slicers**
2. Sync `category` slicer across all 6 pages
3. Sync `date_collected` slicer across all 6 pages

### 7.4 — Configure Drill-Through

1. On **Page 4** (Category Analysis): Right-click the page → **Drill-through**
2. Add `books_catalog[category]` as the drill-through field
3. Now from **Page 1**, right-clicking a category bar → **Drill through** → Category Analysis

---

## Phase 8: Validation & Quality Assurance

### 8.1 — Cross-Check KPIs Against SQL

Run these queries in pgAdmin/psql and compare against your Power BI cards:

```sql
-- Should match [Total Books] card
SELECT COUNT(DISTINCT upc) FROM books_catalog;

-- Should match [Avg Price], [Max Price], [Min Price]
SELECT 
    ROUND(AVG(price), 2) AS avg_price,
    MAX(price) AS max_price,
    MIN(price) AS min_price
FROM price_history;

-- Should match [Total Units]
SELECT SUM(stock_quantity) FROM price_history;

-- Should match [Out of Stock Count]
SELECT COUNT(DISTINCT upc) 
FROM price_history 
WHERE stock_quantity = 0;

-- Should match [Total Categories]
SELECT COUNT(DISTINCT category) FROM books_catalog;
```

### 8.2 — Visual Checklist

- [ ] All 6 pages use Corporate Navy background (`#0A192F`)
- [ ] KPI values display in Teal (`#64FFDA`) at 28pt Bold
- [ ] Navigation bar appears and works on all 6 pages
- [ ] All card visuals have 8px rounded corners and subtle shadows
- [ ] Font is Segoe UI throughout (or Inter if installed)
- [ ] No default Power BI colors remain — all custom palette
- [ ] Slicers filter all visuals correctly on each page
- [ ] Drill-through works from Page 1 to Page 4
- [ ] Bookmarks toggle filters correctly
- [ ] All 33 measures are in the `_Measures` table

### 8.3 — Performance Check

1. **View** → **Performance analyzer** → **Start recording**
2. Navigate through all pages
3. Check that no visual takes > 3 seconds to render
4. If slow: Reduce scatter plot data points or add visual-level filters

---

## Phase 9: Publish & Share

### Option A: Save as .pbix
- **File** → **Save As** → `PriceMonitor_Dashboard.pbix`
- Share the `.pbix` file directly

### Option B: Publish to Power BI Service (if you have a license)
1. **Home** → **Publish**
2. Select your workspace
3. After publishing, configure **scheduled refresh** to auto-pull from PostgreSQL

### Option C: Export to PDF
1. **File** → **Export to PDF**
2. All 6 pages render at 1280×720
3. Great for emailing to stakeholders or including in your portfolio

---

## 📋 Summary of What You'll Build

| Page | Purpose | Key Visuals |
|---|---|---|
| 1. Executive Overview | C-level health check | 4 KPIs, Column chart, Donut, Area |
| 2. Pricing Analysis | Pricing structure deep-dive | Treemap, Price bands, Matrix ledger |
| 3. Inventory Analysis | Supply chain intelligence | Procurement list, Scatter quadrant |
| 4. Category Analysis | Strategic genre comparison | BCG scatter, Funnel, Grouped bar |
| 5. Rating & Quality | Catalog quality audit | 100% stacked, Trend line, Defect table |
| 6. Competitive Intelligence | Market positioning | Waterfall, Opportunity matrix, Actions |

**Total**: 6 pages × 5 KPIs each = **30 KPI cards** + **18 analytical visuals** + **33 DAX measures**

> [!IMPORTANT]
> **Estimated Build Time**: 3–5 hours for a first-time Power BI user following this guide step-by-step. If you get stuck on any specific step, let me know and I can provide more detailed instructions or troubleshoot.
