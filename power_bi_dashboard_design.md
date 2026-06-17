# Power BI Dashboard Design: Price Monitoring & Competitive Intelligence

**Role**: Senior Business Intelligence Consultant & Power BI Solution Architect  
**Data Source**: PostgreSQL `price_monitor` database  
**Schema**: Star Schema — `books_catalog` (Dimension) + `price_history` (Fact)  
**Join Key**: `upc` (One-to-Many cardinality)  
**Design Standard**: KPMG / Deloitte / EY consulting-grade

---

## 🎨 Professional Design System

### Color Palette

| Token | Hex | Usage |
|---|---|---|
| Corporate Navy | `#0A192F` | Page background, header bars |
| Steel Slate | `#1E293B` | Card backgrounds, panel fills |
| Teal Accent | `#64FFDA` | Primary KPI values, highlights |
| Ice Blue | `#38BDF8` | Secondary charts, links |
| Warm Amber | `#F59E0B` | Warning indicators, alerts |
| Coral Red | `#EF4444` | Negative variance, stockouts |
| Lime Green | `#22C55E` | Positive variance, growth |
| Text Primary | `#F8FAFC` | White headings |
| Text Secondary | `#94A3B8` | Labels, axis text |

### Typography

- **Font**: Inter (Google Fonts) or Segoe UI (fallback)
- **KPI Values**: 28pt Bold
- **Card Titles**: 10pt Regular, UPPERCASE, `#94A3B8`
- **Axis Labels**: 9pt, `#94A3B8`
- **Page Titles**: 18pt Bold, `#F8FAFC`

### Layout Grid

- **Canvas**: 1280 × 720 px (16:9)
- **Top Navigation Bar**: 50px height
- **KPI Banner**: 100px height
- **Margins**: 16px between all visuals
- **Card Border-Radius**: 8px
- **Card Shadow**: Subtle drop shadow (2px offset, 8px blur)

---

## 🛠️ DAX Measures Library (32 Measures)

> **Best Practice**: Create a dedicated **`_Measures`** table (Enter Data → empty table → rename to `_Measures`). Store all measures here for clean model organization. This is a standard practice used by Big 4 consulting firms.

### Core KPIs

```dax
// M01 — Total unique products in catalog
Total Books = DISTINCTCOUNT(books_catalog[upc])

// M02 — Average selling price across all records
Avg Price = AVERAGE(price_history[price])

// M03 — Total inventory units
Total Units = SUM(price_history[stock_quantity])

// M04 — Total capital locked in inventory
Total Stock Value = 
    SUMX(price_history, price_history[price] * price_history[stock_quantity])

// M05 — Average customer quality score
Avg Rating = AVERAGE(price_history[rating])

// M06 — Total unique genres
Total Categories = DISTINCTCOUNT(books_catalog[category])
```

### Inventory Intelligence

```dax
// M07 — Books with zero stock
Out of Stock Count = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[stock_quantity] = 0
    )

// M08 — Books with critically low stock (1-2 units)
Low Stock Count = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[stock_quantity] > 0,
        price_history[stock_quantity] <= 2
    )

// M09 — Out of Stock percentage
Out of Stock % = 
    DIVIDE([Out of Stock Count], [Total Books], 0)

// M10 — Overstocked items (>15 units)
Overstocked Count = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[stock_quantity] > 15
    )

// M11 — Average stock per book
Avg Stock Per Book = DIVIDE([Total Units], [Total Books], 0)
```

### Pricing Intelligence

```dax
// M12 — Maximum price in catalog
Max Price = MAX(price_history[price])

// M13 — Minimum price in catalog
Min Price = MIN(price_history[price])

// M14 — Price range (spread)
Price Range = [Max Price] - [Min Price]

// M15 — Median price
Median Price = MEDIAN(price_history[price])

// M16 — Price standard deviation (volatility)
Price Std Dev = 
    STDEV.P(price_history[price])

// M17 — Coefficient of variation (pricing consistency)
Price CV = 
    DIVIDE([Price Std Dev], [Avg Price], 0)

// M18 — Budget segment share
Budget Share % = 
    DIVIDE(
        CALCULATE([Total Books], price_history[Price Band] = "Budget (< £20)"),
        [Total Books],
        0
    )

// M19 — Premium segment share
Premium Share % = 
    DIVIDE(
        CALCULATE([Total Books], price_history[Price Band] = "Premium (> £40)"),
        [Total Books],
        0
    )
```

### Rating & Quality Intelligence

```dax
// M20 — High-rated books count (4-5 stars)
High Rated Books = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[rating] >= 4
    )

// M21 — Low-rated books count (1-2 stars)
Low Rated Books = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[rating] <= 2
    )

// M22 — Catalog quality index (% of books rated 4+)
Catalog Quality Index = 
    DIVIDE([High Rated Books], [Total Books], 0)

// M23 — Quality-to-price ratio
Quality Price Ratio = 
    DIVIDE([Avg Rating], [Avg Price], 0)
```

### Competitive Intelligence Measures

```dax
// M24 — Pricing Power Index (how much above/below market average)
Pricing Power Index = 
    DIVIDE(
        AVERAGE(price_history[price]) - [Avg Price],
        [Avg Price],
        0
    )

// M25 — Category Avg Price (for benchmarking)
Category Avg Price = 
    CALCULATE(
        AVERAGE(price_history[price]),
        ALLEXCEPT(books_catalog, books_catalog[category])
    )

// M26 — Price vs Category Benchmark
Price vs Benchmark = 
    AVERAGE(price_history[price]) - [Category Avg Price]

// M27 — Stock Velocity Indicator
Stock Velocity = 
    DIVIDE(
        [Total Units],
        [Total Books],
        0
    )

// M28 — Revenue Potential (price × stock for all items)
Revenue Potential = 
    SUMX(
        price_history,
        price_history[price] * price_history[stock_quantity]
    )

// M29 — Market Concentration (Herfindahl Index by category)
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

// M30 — Category Dominance (top category's share)
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

// M31 — Opportunity Score (high rating + low stock = opportunity)
Opportunity Score = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[rating] >= 4,
        price_history[stock_quantity] <= 5
    )

// M32 — Dead Stock Score (low rating + high stock = risk)
Dead Stock Score = 
    CALCULATE(
        DISTINCTCOUNT(price_history[upc]),
        price_history[rating] <= 2,
        price_history[stock_quantity] > 10
    )
```

---

## 📄 Page 1: Executive Overview

**Business Objective**: Provide C-level stakeholders with an instant, glanceable health check of the entire product catalog — covering catalog depth, financial exposure, pricing trajectory, and quality distribution.

### Layout Blueprint

```
┌─────────────────────────────────────────────────────────┐
│  📊 EXECUTIVE OVERVIEW           [Category ▼] [Date ▼] │  ← Nav bar + Slicers
├────────┬────────┬────────┬────────┬─────────────────────┤
│  Total │  Avg   │  Total │  Avg   │                     │
│  Books │  Price │  Value │ Rating │                     │  ← KPI Banner
│  1000  │ £35.07 │ £198K  │  3.0⭐  │                     │
├────────┴────────┴────────┴────────┤─────────────────────┤
│                                    │                     │
│  Clustered Column Chart            │   Donut Chart       │
│  Top 10 Categories by Book Count   │   Rating            │
│                                    │   Distribution      │
│                                    │   (1-5 Stars)       │
├────────────────────────────────────┴─────────────────────┤
│                                                          │
│  Area Chart — Average Price Trend over Collection Dates  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Visual Specifications

| # | Visual Type | Field Mapping | Format |
|---|---|---|---|
| KPI 1 | Card | `[Total Books]` | Integer, Teal `#64FFDA` |
| KPI 2 | Card | `[Avg Price]` | Currency £, 2 decimals |
| KPI 3 | Card | `[Total Stock Value]` | Currency £, 0 decimals, thousands separator |
| KPI 4 | Card | `[Avg Rating]` | Decimal `0.0`, star icon conditional |
| A | Clustered Column | X: `books_catalog[category]`, Y: `[Total Books]` | Top N = 10, descending, data labels ON |
| B | Donut Chart | Legend: `price_history[rating]`, Values: `[Total Books]` | Show % of total, 5-color gradient (Red→Green) |
| C | Area Chart | X: `price_history[date_collected]`, Y: `[Avg Price]` | Smooth line, markers ON, gradient fill |

### Slicers

- `books_catalog[category]` — Dropdown, multi-select
- `price_history[date_collected]` — Date range slider

### Drill-Through

- Click any category bar → drills to **Page 4: Category Analysis** (filtered to that category)

### 📊 Business Insights (Page 1)

1. **Catalog Scale Assessment**: Total Books KPI reveals the competitive breadth of the catalog — more titles = wider market coverage.
2. **Financial Exposure**: Total Stock Value shows capital at risk in unsold inventory.
3. **Pricing Stability**: Area chart trend line reveals if the marketplace is experiencing inflation, deflation, or stable pricing.
4. **Quality Distribution**: Donut chart instantly flags if the majority of books are low-rated (red dominant) — a brand reputation risk.

---

## 📄 Page 2: Pricing Analysis

**Business Objective**: Analyze pricing structure, identify capital concentration risks, and optimize the pricing strategy across market segments.

### Layout Blueprint

```
┌──────────────────────────────────────────────────────────┐
│  💰 PRICING ANALYSIS        [Price Band ▼] [Category ▼] │
├────────┬────────┬────────┬───────────┬───────────────────┤
│  Avg   │  Max   │  Min   │  Median   │  Price CV         │
│ £35.07 │ £59.99 │ £10.00 │  £32.50   │  0.42             │
├────────┴────────┴────────┴───────────┴───────────────────┤
│                           │                               │
│  Treemap                  │   Clustered Column Chart      │
│  Capital Concentration    │   Price Band Distribution     │
│  by Category              │   (Budget / Mid / Premium)    │
│  (Size = Stock Value)     │                               │
│                           │                               │
├───────────────────────────┴───────────────────────────────┤
│                                                           │
│  Matrix Visual — Detailed Pricing Ledger                  │
│  Rows: Category > Title                                   │
│  Values: Avg Price | Stock Qty | Stock Value               │
│  Conditional Format: Data bars on Stock Value             │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Visual Specifications

| # | Visual Type | Field Mapping | Format |
|---|---|---|---|
| KPI 1 | Card | `[Avg Price]` | Currency £ |
| KPI 2 | Card | `[Max Price]` | Currency £, Coral Red if > £50 |
| KPI 3 | Card | `[Min Price]` | Currency £, Lime Green |
| KPI 4 | Card | `[Median Price]` | Currency £ |
| KPI 5 | Card | `[Price CV]` | Decimal 0.00 — Amber if > 0.5 |
| A | Treemap | Group: `books_catalog[category]`, Values: `[Total Stock Value]` | Data labels with £ values |
| B | Clustered Column | X: `price_history[Price Band]`, Y: `[Total Books]` | Custom sort: Budget → Mid → Premium |
| C | Matrix | Rows: `category` > `title`, Values: `[Avg Price]`, `stock_quantity`, `[Total Stock Value]` | Data bars on Stock Value column |

### Slicers

- `price_history[Price Band]` — Horizontal tile buttons
- `books_catalog[category]` — Searchable dropdown

### Drill-Through

- Click any treemap tile → drills to product detail showing individual book prices

### 📊 Business Insights (Page 2)

5. **Capital Concentration Risk**: If one category dominates the treemap (>30% of total stock value), it signals concentrated financial risk.
6. **Pricing Skewness**: If Budget segment dominates (>60%), it's a high-volume, low-margin strategy. If Premium dominates, it's niche positioning.
7. **Price Volatility**: A Price CV > 0.5 indicates inconsistent pricing strategy — opportunity to standardize.
8. **Margin Optimization**: The matrix ledger identifies individual high-value items where small price adjustments yield outsized revenue impact.

---

## 📄 Page 3: Inventory Analysis

**Business Objective**: Operational intelligence for supply chain — identify stockout risks, dead stock liabilities, and generate procurement priority lists.

### Layout Blueprint

```
┌──────────────────────────────────────────────────────────┐
│  📦 INVENTORY ANALYSIS      [Stock Alert ▼] [Category ▼]│
├────────┬────────┬────────┬──────────────┬────────────────┤
│  Total │  Out   │  Low   │  Overstocked │ Avg Stock/Book │
│ Units  │  of    │  Stock │  Items       │                │
│ 16,542 │  12    │  28    │  45          │  16.5          │
│        │  🔴    │  🟡    │  🔵          │                │
├────────┴────────┴────────┴──────────────┴────────────────┤
│                              │                            │
│  Matrix — Procurement List   │  Scatter Plot              │
│  Filtered: Stock ≤ 2         │  X: Price                  │
│  Columns: Title, UPC,        │  Y: Stock Quantity          │
│  Category, Stock, Price      │  Color: Category            │
│  Conditional: Red/Yellow BG  │  Size: Revenue Potential    │
│                              │                            │
├──────────────────────────────┴────────────────────────────┤
│                                                           │
│  Clustered Bar Chart — Stock Distribution by Category     │
│  Y: Category  |  X: Total Units                           │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Visual Specifications

| # | Visual Type | Field Mapping | Format |
|---|---|---|---|
| KPI 1 | Card | `[Total Units]` | Integer, Teal |
| KPI 2 | Card | `[Out of Stock Count]` | Integer, Coral Red `#EF4444` |
| KPI 3 | Card | `[Low Stock Count]` | Integer, Amber `#F59E0B` |
| KPI 4 | Card | `[Overstocked Count]` | Integer, Ice Blue |
| KPI 5 | Card | `[Avg Stock Per Book]` | Decimal 0.0 |
| A | Matrix | Rows: `title`, Values: `upc`, `category`, `stock_quantity`, `price` | Filter: `stock_quantity ≤ 2`. Conditional BG: Red=0, Yellow=1-2 |
| B | Scatter | X: `price`, Y: `stock_quantity`, Legend: `category`, Size: `[Revenue Potential]` | Reference lines at price median & stock median |
| C | Clustered Bar | Y: `books_catalog[category]`, X: `[Total Units]` | Descending sort, data labels ON |

### Slicers

- `price_history[Stock Alert]` — Buttons (🔴 Out of Stock / 🟡 Low / 🟢 Normal / 🔵 Overstocked)
- `books_catalog[category]` — Multi-select checkbox

### 📊 Business Insights (Page 3)

9. **Stockout Prevention**: The procurement matrix is an instant, actionable reorder list — export directly to CSV for the supply chain team.
10. **Dead Stock Identification**: Scatter plot quadrant (top-left: expensive + high stock) reveals items consuming warehouse capital without movement.
11. **Category Imbalance**: Bar chart reveals if inventory is concentrated in few categories — a supply chain fragility risk.
12. **Restock Prioritization**: Cross-reference low stock with high rating — these are your highest-priority restock items (use `[Opportunity Score]`).

---

## 📄 Page 4: Category (Genre) Analysis

**Business Objective**: Strategic category management — compare genre performance, identify "Cash Cows" vs "Dogs" using BCG-style quadrant analysis, and guide purchasing budgets.

### Layout Blueprint

```
┌──────────────────────────────────────────────────────────┐
│  📚 CATEGORY ANALYSIS       [Category ▼] [Date Range ▼] │
├────────┬────────┬────────┬──────────────┬────────────────┤
│  Total │  Top   │  Avg   │  Market HHI  │ Top Cat Share  │
│  Cats  │  Cat   │  Cat   │  (Concent.)  │                │
│  50    │ Romance│  3.2⭐  │  0.038       │  8.2%          │
├────────┴────────┴────────┴──────────────┴────────────────┤
│                              │                            │
│  Scatter Plot — BCG Matrix   │  Funnel Chart              │
│  X: Avg Price                │  Category by Stock Value   │
│  Y: Avg Rating               │  (Top 15 categories)       │
│  Size: Total Units           │                            │
│  Label: Category Name        │                            │
│                              │                            │
├──────────────────────────────┴────────────────────────────┤
│                                                           │
│  Grouped Bar — Category Comparison                        │
│  Y: Category  |  X: [Total Books] + [Total Stock Value]  │
│  (Side-by-side bars for Volume vs Value comparison)       │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Visual Specifications

| # | Visual Type | Field Mapping | Format |
|---|---|---|---|
| KPI 1 | Card | `[Total Categories]` | Integer |
| KPI 2 | Card | Top category by `[Total Stock Value]` | Text, use TOPN |
| KPI 3 | Card | `[Avg Rating]` overall | Decimal with star emoji |
| KPI 4 | Card | `[Market HHI]` | Decimal 0.000 |
| KPI 5 | Card | `[Top Category Share]` | Percentage |
| A | Scatter | X: `[Avg Price]`, Y: `[Avg Rating]`, Details: `category`, Size: `[Total Units]` | Reference lines at median price & median rating (creates 4 quadrants) |
| B | Funnel | Group: `category`, Values: `[Total Stock Value]` | Top N = 15, show % of total |
| C | Grouped Bar | Y: `category`, X1: `[Total Books]`, X2: `[Total Stock Value]` | Side-by-side comparison |

### Slicers

- `books_catalog[category]` — Multi-select checkbox
- `price_history[date_collected]` — Date range

### 📊 Business Insights (Page 4)

13. **BCG Quadrant Interpretation**:
    - **Top-Right** (High Price + High Rating) = **Stars** — Premium quality, invest more
    - **Top-Left** (Low Price + High Rating) = **Cash Cows** — High value, maintain supply
    - **Bottom-Right** (High Price + Low Rating) = **Question Marks** — Overpriced, needs review
    - **Bottom-Left** (Low Price + Low Rating) = **Dogs** — Consider delisting
14. **Market Concentration**: HHI < 0.01 = Perfectly competitive catalog. HHI > 0.25 = Highly concentrated (over-reliance on few genres).
15. **Budget Allocation**: Funnel chart shows which categories deserve larger purchasing budgets based on revenue potential share.
16. **Volume vs Value Gap**: Grouped bar reveals categories that have many books but low total value (cheap products) vs few books but high value (premium niche).

---

## 📄 Page 5: Rating & Catalog Quality Analysis

**Business Objective**: Audit the quality profile of the catalog to ensure customer satisfaction, identify quality control risks, and guide marketing promotion decisions.

### Layout Blueprint

```
┌──────────────────────────────────────────────────────────┐
│  ⭐ RATING & QUALITY ANALYSIS    [Rating ▼] [Category ▼]│
├────────┬────────┬────────┬─────────────┬─────────────────┤
│  Avg   │  High  │  Low   │  Quality    │ Quality-Price   │
│ Rating │  Rated │  Rated │  Index      │ Ratio           │
│  3.0   │  412   │  198   │  41.2%      │  0.086          │
├────────┴────────┴────────┴─────────────┴─────────────────┤
│                              │                            │
│  100% Stacked Bar Chart      │  Scatter Chart             │
│  Y: Category                 │  X: Price                  │
│  X: Book Count               │  Y: Rating                 │
│  Legend: Rating (1-5)        │  Details: Title             │
│  Colors: Red→Yellow→Green    │  Trend line: Linear         │
│                              │                            │
├──────────────────────────────┴────────────────────────────┤
│                                                           │
│  Table — Quality Defect List                              │
│  Columns: Title, Category, Rating, Stock, Price           │
│  Filter: Rating ≤ 2  |  Sorted by Stock DESC             │
│  Highlight: Items with Rating ≤ 2 AND Stock > 10         │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Visual Specifications

| # | Visual Type | Field Mapping | Format |
|---|---|---|---|
| KPI 1 | Card | `[Avg Rating]` | Decimal 0.0, star icon |
| KPI 2 | Card | `[High Rated Books]` | Integer, Lime Green `#22C55E` |
| KPI 3 | Card | `[Low Rated Books]` | Integer, Coral Red `#EF4444` |
| KPI 4 | Card | `[Catalog Quality Index]` | Percentage, Teal if > 50% |
| KPI 5 | Card | `[Quality Price Ratio]` | Decimal 0.000 |
| A | 100% Stacked Bar | Y: `category`, X: `[Total Books]`, Legend: `rating` | 5-color scale: 1=`#EF4444`, 2=`#F97316`, 3=`#F59E0B`, 4=`#84CC16`, 5=`#22C55E` |
| B | Scatter | X: `price`, Y: `rating`, Details: `title` | Linear trend line enabled |
| C | Table | Columns: `title`, `category`, `rating`, `stock_quantity`, `price` | Visual filter: `rating ≤ 2`, Sort: `stock_quantity` DESC |

### Slicers

- `price_history[rating]` — Horizontal number buttons (1, 2, 3, 4, 5)
- `books_catalog[category]` — Multi-select

### Drill-Through

- Click any book in the defect table → drills to product detail page

### 📊 Business Insights (Page 5)

17. **Quality Control Alert**: Categories with dominant red bars (1-2 stars) need immediate quality review — these damage brand reputation.
18. **Price-Quality Correlation**: If the trend line is flat, price does NOT predict quality — this means budget books can be just as good as premium ones (marketing opportunity).
19. **Dead Stock Risk**: The defect table with `Stock > 10 AND Rating ≤ 2` identifies items consuming warehouse space that won't sell — candidates for clearance sales.
20. **Promotion Safety**: Categories with >70% green (4-5 star) bars are safe for marketing promotions. Categories with >30% red are risky to promote.

---

## 📄 Page 6: Competitive Intelligence Insights

**Business Objective**: Strategic market positioning analysis — benchmark against category averages, identify pricing power, and discover untapped market opportunities.

### Layout Blueprint

```
┌──────────────────────────────────────────────────────────┐
│  🎯 COMPETITIVE INTELLIGENCE    [Category ▼] [Band ▼]   │
├────────┬────────┬────────┬──────────────┬────────────────┤
│ Pricing│ Opport.│  Dead  │  Revenue     │  Avg Stock     │
│ Power  │ Score  │  Stock │  Potential   │  Velocity      │
│ +2.3%  │  67    │  12    │  £198,450    │  16.5          │
├────────┴────────┴────────┴──────────────┴────────────────┤
│                              │                            │
│  Waterfall Chart             │  Bubble Chart              │
│  Price vs Category Benchmark │  Opportunity Matrix        │
│  (Over/Under pricing by     │  X: Stock Quantity          │
│   category)                  │  Y: Rating                 │
│                              │  Size: Price               │
│                              │  Color: Category           │
├──────────────────────────────┴────────────────────────────┤
│                                                           │
│  Matrix — Strategic Action Items                          │
│  Rows: Category                                           │
│  Values: Avg Price | Benchmark | Variance | Rating |     │
│          Stock | Action Recommended                       │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Visual Specifications

| # | Visual Type | Field Mapping | Format |
|---|---|---|---|
| KPI 1 | Card | `[Pricing Power Index]` | Percentage, Green if +, Red if − |
| KPI 2 | Card | `[Opportunity Score]` | Integer, Teal |
| KPI 3 | Card | `[Dead Stock Score]` | Integer, Coral Red |
| KPI 4 | Card | `[Revenue Potential]` | Currency £ |
| KPI 5 | Card | `[Stock Velocity]` | Decimal |
| A | Waterfall | Category: `category`, Y: `[Price vs Benchmark]` | Green = overpriced, Red = underpriced |
| B | Scatter/Bubble | X: `stock_quantity`, Y: `rating`, Size: `price`, Color: `category` | Reference lines at rating=3 and stock=10 |
| C | Matrix | Rows: `category`, Values: `[Avg Price]`, `[Category Avg Price]`, `[Price vs Benchmark]`, `[Avg Rating]`, `[Total Units]` | Conditional: Red BG for negative variance, Green for positive |

### Strategic Action Column (DAX Calculated Measure)

```dax
// Strategic Action — creates executive-ready recommendations
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

### Slicers

- `books_catalog[category]` — Multi-select
- `price_history[Price Band]` — Tile buttons

### 📊 Business Insights (Page 6)

21. **Pricing Power Assessment**: A positive Pricing Power Index means pricing above market average — sustainable only if quality (rating) supports it.
22. **Opportunity Discovery**: The Opportunity Matrix bubble chart (Top-Left quadrant: High Rating + Low Stock) reveals high-demand items needing immediate restocking.
23. **Dead Stock Liquidation**: Bottom-Right quadrant (Low Rating + High Stock) items should be flagged for clearance sales, bundle deals, or delisting.
24. **Category Benchmarking**: The waterfall chart shows which categories are over/underpriced relative to the portfolio average — informs dynamic pricing strategy.
25. **Strategic Action Matrix**: The action column translates raw data into executive-ready recommendations (Restock, Clearance, Promote, Delist, Maintain).

---

## 🧭 Navigation & UX Features

### Page Navigation Tabs

Create a consistent top navigation bar using **Buttons** with **Page Navigation** actions:

| Button | Target Page | Style |
|---|---|---|
| Executive Overview | Page 1 | Active = Teal underline |
| Pricing | Page 2 | Inactive = Slate text |
| Inventory | Page 3 | Inactive = Slate text |
| Categories | Page 4 | Inactive = Slate text |
| Ratings | Page 5 | Inactive = Slate text |
| Intelligence | Page 6 | Inactive = Slate text |

### Bookmarks

Create bookmarks for common executive views:

- **"Critical Alerts"** — Pre-filters to show only Out of Stock and Low Stock items
- **"Premium Products"** — Filters to Premium price band + Rating ≥ 4
- **"At Risk Items"** — Filters to Rating ≤ 2 AND Stock > 10

### Report-Level Filters

- All pages inherit the `Date_Collected` and `Category` slicers
- Sync slicers across pages for consistent cross-page filtering

---

## 📋 Complete Business Insights Summary (25 Insights)

| # | Insight | Page | Category |
|---|---|---|---|
| 1 | Catalog Scale Assessment | Executive Overview | Strategic |
| 2 | Financial Exposure in Inventory | Executive Overview | Financial |
| 3 | Pricing Stability Trend | Executive Overview | Market |
| 4 | Quality Distribution Risk | Executive Overview | Quality |
| 5 | Capital Concentration Risk | Pricing Analysis | Financial |
| 6 | Pricing Skewness (Volume vs Margin) | Pricing Analysis | Strategy |
| 7 | Price Volatility (CV Analysis) | Pricing Analysis | Market |
| 8 | Margin Optimization via Ledger | Pricing Analysis | Financial |
| 9 | Stockout Prevention List | Inventory Analysis | Operations |
| 10 | Dead Stock Identification | Inventory Analysis | Operations |
| 11 | Category Imbalance Risk | Inventory Analysis | Supply Chain |
| 12 | Restock Prioritization | Inventory Analysis | Operations |
| 13 | BCG Quadrant Classification | Category Analysis | Strategy |
| 14 | Market Concentration (HHI) | Category Analysis | Competitive |
| 15 | Budget Allocation Guidance | Category Analysis | Strategy |
| 16 | Volume vs Value Gap | Category Analysis | Financial |
| 17 | Quality Control Alert | Rating Analysis | Quality |
| 18 | Price-Quality Correlation | Rating Analysis | Analytics |
| 19 | Dead Stock Clearance Candidates | Rating Analysis | Operations |
| 20 | Promotion Safety Assessment | Rating Analysis | Marketing |
| 21 | Pricing Power Assessment | Competitive Intel. | Competitive |
| 22 | Opportunity Discovery | Competitive Intel. | Strategy |
| 23 | Dead Stock Liquidation | Competitive Intel. | Operations |
| 24 | Category Benchmarking | Competitive Intel. | Competitive |
| 25 | Strategic Action Recommendations | Competitive Intel. | Executive |

---

## ✅ Design Verification Checklist

- [ ] All pages use Corporate Navy background (`#0A192F`)
- [ ] KPI values use Teal accent (`#64FFDA`)
- [ ] Navigation bar appears on all 6 pages
- [ ] All cards have consistent 8px border-radius and shadows
- [ ] Font: Inter or Segoe UI throughout
- [ ] No default Power BI theme colors — all custom palette
- [ ] All DAX measures stored in `_Measures` table
- [ ] Model View shows `books_catalog[upc] → price_history[upc]` (1:*)
- [ ] Slicers synced across all pages
- [ ] Drill-through configured on Pages 1, 2, and 5
- [ ] Bookmarks created for Critical Alerts, Premium Products, At Risk Items
- [ ] Report exported as PDF renders cleanly at 1280×720
