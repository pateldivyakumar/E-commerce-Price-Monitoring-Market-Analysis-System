# ============================================================
# app.py - Price Monitoring System Interactive Dashboard
# Framework: Streamlit
# Visualization: Plotly
# Database: PostgreSQL (with automatic CSV fallback)
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import subprocess
import datetime
import utils

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Price & Inventory Monitor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN STYLING (CSS) ---
# Custom styling to make the app look premium, using Inter-like typography,
# rounded card containers, clean spacing, and modern metric cards.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Elegant Metric Container */
    .metric-card {
        background: linear-gradient(135deg, #fbfbfb 0%, #f5f6f8 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 10px;
    }
    
    .metric-title {
        font-size: 0.85rem;
        color: #718096;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 1.8rem;
        color: #1a202c;
        font-weight: 700;
        margin: 5px 0;
    }
    
    .metric-subtitle {
        font-size: 0.75rem;
        color: #48bb78;
        font-weight: 500;
    }
    
    /* Banner styles */
    .status-banner-db {
        background-color: #ebf8ff;
        border-left: 5px solid #3182ce;
        color: #2b6cb0;
        padding: 12px;
        border-radius: 4px;
        font-weight: 500;
        margin-bottom: 20px;
    }
    
    .status-banner-csv {
        background-color: #fffaf0;
        border-left: 5px solid #dd6b20;
        color: #dd6b20;
        padding: 12px;
        border-radius: 4px;
        font-weight: 500;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# DATA CONNECTION LAYER (DUAL-MODE)
# ============================================================

@st.cache_data(ttl=3600)  # Cache results for 1 hour to ensure snappy performance
def load_data():
    """
    Tries to query the database first. If database is unreachable or missing,
    automatically falls back to loading and cleaning local CSV files.
    """
    data_source = "PostgreSQL Database"
    df_snapshot = None
    df_history = None
    
    try:
        # Try database connection
        conn = utils.get_db_connection()
        
        # 1. Fetch Latest Snapshot (join tables, filtered by latest collected date)
        snapshot_query = """
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
        df_snapshot = pd.read_sql(snapshot_query, conn)
        
        # 2. Fetch Complete Historical Log
        history_query = """
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
        ORDER BY h.date_collected ASC;
        """
        df_history = pd.read_sql(history_query, conn)
        
        conn.close()
        
        # Convert types just in case
        df_snapshot["Price"] = df_snapshot["Price"].astype(float)
        df_snapshot["Stock_Quantity"] = df_snapshot["Stock_Quantity"].astype(int)
        df_history["Price"] = df_history["Price"].astype(float)
        df_history["Stock_Quantity"] = df_history["Stock_Quantity"].astype(int)
        df_history["Date_Collected"] = pd.to_datetime(df_history["Date_Collected"]).dt.strftime('%Y-%m-%d')
        df_snapshot["Date_Collected"] = pd.to_datetime(df_snapshot["Date_Collected"]).dt.strftime('%Y-%m-%d')
        
    except Exception as db_err:
        # DB Error -> Fallback to CSV files
        data_source = "CSV Backup Log (Fallback Mode)"
        
        # Load snapshot CSV
        if os.path.exists("data/books.csv"):
            df_snapshot = pd.read_csv("data/books.csv")
        
        # Load history CSV
        if os.path.exists("data/history.csv"):
            df_history = pd.read_csv("data/history.csv")
            # Clean duplicate dates just like compare.py
            df_history = df_history.drop_duplicates(
                subset=["Title", "URL", "Date_Collected"], 
                keep="last"
            ).reset_index(drop=True)
            df_history["Date_Collected"] = pd.to_datetime(df_history["Date_Collected"]).dt.strftime('%Y-%m-%d')
            
    # Convert rating values (words, string numbers, numeric numbers) to clean integers
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    
    for df_tmp in [df_snapshot, df_history]:
        if df_tmp is not None:
            # Map string words ('Three' -> 3). Non-matches yield NaN.
            mapped = df_tmp["Rating"].map(rating_map)
            # Map direct numeric objects or string digits ('3' -> 3.0). Non-matches yield NaN.
            numeric = pd.to_numeric(df_tmp["Rating"], errors='coerce')
            # Combine results, default missing to 0, and cast to standard integers
            df_tmp["Rating_Numeric"] = mapped.fillna(numeric).fillna(0).astype(int)
                
    return df_snapshot, df_history, data_source


# Load the data
df_snapshot, df_history, data_source = load_data()


# ============================================================
# APP LAYOUT & SIDEBAR
# ============================================================
st.sidebar.title("📚 Book Monitor")
st.sidebar.markdown("### Competitive Price & Inventory Analytics")

# Display connection status
if "PostgreSQL" in data_source:
    st.sidebar.markdown(f'<div class="status-banner-db">🟢 Connected: {data_source}</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown(f'<div class="status-banner-csv">⚠️ Fallback: {data_source}</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### About this project")
st.sidebar.markdown("""
This data pipeline scrapes and monitors prices across 1,000 products on [Books to Scrape](https://books.toscrape.com/).
It normalizes web page DOM fields, writes records into a PostgreSQL Star Schema, tracks history, and logs price alerts.
""")

if df_snapshot is None or df_history is None:
    st.error("No data found! Please run the pipeline script first to generate CSVs or insert database tables.")
    st.info("You can use the 'ETL Pipeline & Systems' tab to trigger a scrape if running locally.")
    
    # Simple fallback tab when there's no data
    tab_init = st.tabs(["⚙️ Run Pipeline Setup"])[0]
    with tab_init:
        st.markdown("### No Data Detected")
        st.markdown("To start, run Python in your project folder:")
        st.code("python src/scraper.py")
        if st.button("Attempt Scraper Run (Local Only)"):
            with st.spinner("Scraping books.toscrape.com (this takes a couple of minutes)..."):
                try:
                    result = subprocess.run(["python", "src/scraper.py"], capture_output=True, text=True)
                    st.text_area("Pipeline Log Output:", result.stdout, height=300)
                    st.success("Scraper executed successfully! Reloading...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to execute pipeline script: {e}")
    st.stop()


# Create Dashboard Tabs
tab_overview, tab_alerts, tab_catalog, tab_system = st.tabs([
    "📊 Executive Overview", 
    "📉 Price Drop Alerts", 
    "🔍 Product Catalog Search", 
    "⚙️ ETL Pipeline & Systems"
])


# ============================================================
# TAB 1: EXECUTIVE OVERVIEW
# ============================================================
with tab_overview:
    st.subheader("Key Performance Indicators (KPIs)")
    
    # Calculate metrics
    tot_books = len(df_snapshot)
    avg_price = df_snapshot["Price"].mean()
    tot_stock = df_snapshot["Stock_Quantity"].sum()
    unique_categories = df_snapshot["Category"].nunique()
    
    # Format and present metric cards using columns and custom CSS
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Catalog Size</div>
            <div class="metric-value">{tot_books:,}</div>
            <div class="metric-subtitle">Active Books Monitored</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Average Price</div>
            <div class="metric-value">£{avg_price:.2f}</div>
            <div class="metric-subtitle">Across Catalog</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Inventory</div>
            <div class="metric-value">{tot_stock:,}</div>
            <div class="metric-subtitle">Copies in Stock</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Categories</div>
            <div class="metric-value">{unique_categories}</div>
            <div class="metric-subtitle">Distinct Genres</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Charts Row 1: Category Distribution & Star Ratings
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        st.markdown("#### 📦 Book Counts by Category")
        cat_counts = df_snapshot["Category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        # Limit to top 15 for readability
        fig_cat = px.bar(
            cat_counts.head(15), 
            x="Count", 
            y="Category", 
            orientation="h",
            labels={"Category": "Genre", "Count": "Number of Books"},
            color="Count",
            color_continuous_scale="Blues",
            height=400
        )
        fig_cat.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_cat, use_container_width=True)
        
    with col_chart2:
        st.markdown("#### ⭐ Rating Distribution")
        rating_counts = df_snapshot["Rating_Numeric"].value_counts().reset_index()
        rating_counts.columns = ["Rating", "Count"]
        rating_counts = rating_counts.sort_values(by="Rating")
        
        # Donut Chart
        fig_rating = px.pie(
            rating_counts, 
            values="Count", 
            names="Rating",
            color_discrete_sequence=px.colors.sequential.Teal,
            hole=0.4,
            height=400
        )
        fig_rating.update_traces(textinfo="percent+label")
        fig_rating.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_rating, use_container_width=True)
        
    st.markdown("---")
    
    # Charts Row 2: Average Price by Category
    st.markdown("#### 💸 Average Price by Category (£)")
    avg_price_cat = df_snapshot.groupby("Category")["Price"].mean().reset_index()
    avg_price_cat = avg_price_cat.sort_values(by="Price", ascending=False)
    
    fig_price_cat = px.bar(
        avg_price_cat.head(25), 
        x="Category", 
        y="Price", 
        labels={"Category": "Genre", "Price": "Average Price (£)"},
        color="Price",
        color_continuous_scale="Purples",
        height=400
    )
    fig_price_cat.update_layout(xaxis_tickangle=-45, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_price_cat, use_container_width=True)


# ============================================================
# TAB 2: PRICE DROP ALERTS
# ============================================================
with tab_alerts:
    st.subheader("🚨 Real-Time Competitor Price Changes")
    st.markdown("Identifies price drops (good deals) and price hikes (inflation alerts) between the two latest collection dates.")
    
    # Identify unique collection dates
    unique_dates = sorted(df_history["Date_Collected"].unique())
    
    if len(unique_dates) < 2:
        st.warning("Only one historical date detected in the dataset. Price changes cannot be measured automatically.")
        st.info("Simulating price changes so you can see how this panel behaves.")
        
        # Simulation Logic identical to compare.py
        is_simulation = True
        prev_date = unique_dates[0]
        latest_date = "2026-06-06"  # Tomorrow simulation
        
        df_prev = df_history[df_history["Date_Collected"] == prev_date].copy()
        df_latest = df_history[df_history["Date_Collected"] == prev_date].copy()
        df_latest["Date_Collected"] = latest_date
        
        # Simulate drops
        df_latest.loc[0, "Price"] = round(df_latest.loc[0, "Price"] - 5.78, 2)
        df_latest.loc[10, "Price"] = round(df_latest.loc[10, "Price"] - 12.00, 2)
        df_latest.loc[25, "Price"] = round(df_latest.loc[25, "Price"] - 8.50, 2)
        
        # Simulate hikes
        df_latest.loc[1, "Price"] = round(df_latest.loc[1, "Price"] + 2.50, 2)
        df_latest.loc[50, "Price"] = round(df_latest.loc[50, "Price"] + 9.99, 2)
        
    else:
        is_simulation = False
        prev_date = unique_dates[-2]
        latest_date = unique_dates[-1]
        
        df_prev = df_history[df_history["Date_Collected"] == prev_date]
        df_latest = df_history[df_history["Date_Collected"] == latest_date]
        
    # Merge and calculate differences
    df_compare = pd.merge(
        df_prev[["Title", "UPC", "URL", "Category", "Price"]],
        df_latest[["Title", "UPC", "Price"]],
        on=["Title", "UPC"],
        suffixes=("_old", "_new")
    )
    
    df_compare["Change_Amt"] = round(df_compare["Price_new"] - df_compare["Price_old"], 2)
    df_compare["Change_Pct"] = round((df_compare["Change_Amt"] / df_compare["Price_old"]) * 100, 2)
    
    df_drops = df_compare[df_compare["Change_Amt"] < 0].sort_values(by="Change_Pct")
    df_hikes = df_compare[df_compare["Change_Amt"] > 0].sort_values(by="Change_Pct", ascending=False)
    
    # Metrics
    col_al1, col_al2, col_al3 = st.columns(3)
    with col_al1:
        st.metric("Previous Collection Date", prev_date)
    with col_al2:
        st.metric("Latest Collection Date", latest_date, delta="New Snapshot" if not is_simulation else "SIMULATED")
    with col_al3:
        st.metric("Total Items Compared", len(df_compare))
        
    st.markdown("---")
    
    # Showcase Drops & Hikes Side-by-Side
    col_dr, col_hk = st.columns(2)
    
    with col_dr:
        st.markdown(f"#### 📉 Price Drops (Deals Detected: {len(df_drops)})")
        if df_drops.empty:
            st.info("No price drops detected.")
        else:
            # Add filter for discount magnitude
            pct_filter = st.slider("Filter by minimum discount %", min_value=0, max_value=50, value=0, key="pct_drop_slider")
            df_drops_filtered = df_drops[abs(df_drops["Change_Pct"]) >= pct_filter]
            
            # Clean and format table
            df_drops_view = df_drops_filtered.copy()
            df_drops_view["Old Price"] = df_drops_view["Price_old"].apply(lambda x: f"£{x:.2f}")
            df_drops_view["New Price"] = df_drops_view["Price_new"].apply(lambda x: f"£{x:.2f}")
            df_drops_view["Discount"] = df_drops_view["Change_Amt"].apply(lambda x: f"-£{abs(x):.2f}")
            df_drops_view["Discount %"] = df_drops_view["Change_Pct"].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(
                df_drops_view[["Title", "Category", "Old Price", "New Price", "Discount", "Discount %", "URL"]],
                column_config={
                    "URL": st.column_config.LinkColumn("Product Link", display_text="Visit Site")
                },
                hide_index=True,
                use_container_width=True
            )
            
    with col_hk:
        st.markdown(f"#### 📈 Price Hikes (Inflation Detected: {len(df_hikes)})")
        if df_hikes.empty:
            st.info("No price hikes detected.")
        else:
            df_hikes_view = df_hikes.copy()
            df_hikes_view["Old Price"] = df_hikes_view["Price_old"].apply(lambda x: f"£{x:.2f}")
            df_hikes_view["New Price"] = df_hikes_view["Price_new"].apply(lambda x: f"£{x:.2f}")
            df_hikes_view["Increase"] = df_hikes_view["Change_Amt"].apply(lambda x: f"+£{x:.2f}")
            df_hikes_view["Increase %"] = df_hikes_view["Change_Pct"].apply(lambda x: f"+{x:.2f}%")
            
            st.dataframe(
                df_hikes_view[["Title", "Category", "Old Price", "New Price", "Increase", "Increase %", "URL"]],
                column_config={
                    "URL": st.column_config.LinkColumn("Product Link", display_text="Visit Site")
                },
                hide_index=True,
                use_container_width=True
            )


# ============================================================
# TAB 3: PRODUCT CATALOG SEARCH
# ============================================================
with tab_catalog:
    st.subheader("🔍 Search & Filter Product Inventory")
    st.markdown("Easily find and discover books using search keywords, autocomplete, or quick presets.")
    
    # Fetch lists for dropdowns
    all_cats = ["All"] + sorted(list(df_snapshot["Category"].unique()))
    all_titles = ["-- Optional: Autocomplete Search --"] + sorted(list(df_snapshot["Title"].unique()))
    
    min_p = float(df_snapshot["Price"].min())
    max_p = float(df_snapshot["Price"].max())
    
    # Initialize session state variables if not present
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    if "selected_title" not in st.session_state:
        st.session_state.selected_title = "-- Optional: Autocomplete Search --"
    if "selected_cat" not in st.session_state:
        st.session_state.selected_cat = "All"
    if "selected_ratings" not in st.session_state:
        st.session_state.selected_ratings = [1, 2, 3, 4, 5]
    if "selected_price" not in st.session_state:
        st.session_state.selected_price = (min_p, max_p)
    if "stock_only" not in st.session_state:
        st.session_state.stock_only = False
    if "preset_choice" not in st.session_state:
        st.session_state.preset_choice = "📚 All Books"
    if "last_preset" not in st.session_state:
        st.session_state.last_preset = "📚 All Books"

    # --- SECTION A: QUICK PRESET FILTERS ---
    st.markdown("##### 🚀 Quick Discovery Presets (One-click filters)")
    preset_col1, preset_col2 = st.columns([3, 1])
    
    with preset_col1:
        preset = st.radio(
            "Select a preset view to instantly explore subsets of data:",
            options=[
                "📚 All Books", 
                "⭐ 5-Star Masterpieces", 
                "💸 Bargain Books (< £20)", 
                "⚠️ Low Stock Alerts (1-3 left)",
                "💎 Premium Reads (£50+)"
            ],
            horizontal=True,
            key="preset_choice"
        )
    
    with preset_col2:
        clear_filters = st.button("🔄 Reset All Filters", use_container_width=True)
        if clear_filters:
            st.session_state.search_query = ""
            st.session_state.selected_title = "-- Optional: Autocomplete Search --"
            st.session_state.selected_cat = "All"
            st.session_state.selected_ratings = [1, 2, 3, 4, 5]
            st.session_state.selected_price = (min_p, max_p)
            st.session_state.stock_only = False
            st.session_state.preset_choice = "📚 All Books"
            st.session_state.last_preset = "📚 All Books"
            st.rerun()

    # Detect if preset changed, and dynamically update the corresponding widget states
    if preset != st.session_state.last_preset:
        st.session_state.last_preset = preset
        st.session_state.search_query = ""
        st.session_state.selected_title = "-- Optional: Autocomplete Search --"
        st.session_state.selected_cat = "All"
        
        if preset == "📚 All Books":
            st.session_state.selected_ratings = [1, 2, 3, 4, 5]
            st.session_state.selected_price = (min_p, max_p)
            st.session_state.stock_only = False
        elif preset == "⭐ 5-Star Masterpieces":
            st.session_state.selected_ratings = [5]
            st.session_state.selected_price = (min_p, max_p)
            st.session_state.stock_only = False
        elif preset == "💸 Bargain Books (< £20)":
            st.session_state.selected_ratings = [1, 2, 3, 4, 5]
            st.session_state.selected_price = (min_p, 20.0)
            st.session_state.stock_only = False
        elif preset == "⚠️ Low Stock Alerts (1-3 left)":
            st.session_state.selected_ratings = [1, 2, 3, 4, 5]
            st.session_state.selected_price = (min_p, max_p)
            st.session_state.stock_only = True
        elif preset == "💎 Premium Reads (£50+)":
            st.session_state.selected_ratings = [1, 2, 3, 4, 5]
            st.session_state.selected_price = (50.0, max_p)
            st.session_state.stock_only = False
        st.rerun()
        
    st.markdown("---")
    
    # --- SECTION B: ADVANCED SEARCH & FILTERS ---
    col_fil1, col_fil2, col_fil3, col_fil4 = st.columns([1.5, 1, 1, 1.5])
    
    with col_fil1:
        # Binding directly to session state keys
        search_query = st.text_input(
            "Keyword Search (Title or UPC)", 
            placeholder="Type a word (e.g. 'love', 'history', 'art')...",
            key="search_query"
        )
        
        selected_title = st.selectbox(
            "Autocomplete Title Search",
            all_titles,
            key="selected_title",
            help="Type to search and select a specific book from the catalog."
        )
        
    with col_fil2:
        selected_cat = st.selectbox(
            "Category / Genre", 
            all_cats,
            key="selected_cat"
        )
        
    with col_fil3:
        selected_ratings = st.multiselect(
            "Rating Stars", 
            [1, 2, 3, 4, 5], 
            key="selected_ratings"
        )
        
    with col_fil4:
        selected_price_range = st.slider(
            "Price Range (£)", 
            min_value=min_p, 
            max_value=max_p, 
            key="selected_price"
        )
        
        stock_only = st.checkbox(
            "Only show books currently in stock", 
            key="stock_only"
        )

    # Filter DataFrame
    df_filtered = df_snapshot.copy()
    
    # 1. Autocomplete Search Override
    # If the user selects a specific book from the autocomplete dropdown,
    # show exactly that book and bypass other filters to avoid conflicts.
    if selected_title != "-- Optional: Autocomplete Search --":
        df_filtered = df_filtered[df_filtered["Title"] == selected_title]
    else:
        # Otherwise, apply cumulative filters (AND relation)
        
        # A. Apply Preset specific overrides to the data
        if preset == "⚠️ Low Stock Alerts (1-3 left)":
            df_filtered = df_filtered[(df_filtered["Stock_Quantity"] >= 1) & (df_filtered["Stock_Quantity"] <= 3)]
            
        # B. Apply Keyword Search
        if search_query:
            df_filtered = df_filtered[
                df_filtered["Title"].str.contains(search_query, case=False, na=False) |
                df_filtered["UPC"].str.contains(search_query, case=False, na=False)
            ]
            
        # C. Apply Genre Filter
        if selected_cat != "All":
            df_filtered = df_filtered[df_filtered["Category"] == selected_cat]
            
        # D. Apply Ratings Filter
        if selected_ratings:
            df_filtered = df_filtered[df_filtered["Rating_Numeric"].isin(selected_ratings)]
        else:
            df_filtered = df_filtered[df_filtered["Rating_Numeric"].isin([])]
        
        # E. Apply Price Slider Filter
        df_filtered = df_filtered[
            (df_filtered["Price"] >= selected_price_range[0]) & 
            (df_filtered["Price"] <= selected_price_range[1])
        ]
        
        # F. Apply Stock Checkbox
        if stock_only:
            df_filtered = df_filtered[df_filtered["Stock_Quantity"] > 0]
        
    # Display Result Stats
    st.markdown(f"**Found {len(df_filtered)} matching products**")
    
    # Format and display DataFrame
    df_view = df_filtered.copy()
    df_view["Price"] = df_view["Price"].apply(lambda x: f"£{x:.2f}")
    
    # Column configuration
    st.dataframe(
        df_view[["UPC", "Title", "Category", "Price", "Rating_Numeric", "Stock_Quantity", "URL"]],
        column_config={
            "Rating_Numeric": st.column_config.NumberColumn("Rating (Stars)", format="%d ⭐"),
            "Stock_Quantity": st.column_config.NumberColumn("Stock Qty"),
            "URL": st.column_config.LinkColumn("Product Link", display_text="Open Link")
        },
        hide_index=True,
        use_container_width=True
    )


# ============================================================
# TAB 4: ETL PIPELINE & SYSTEMS
# ============================================================
with tab_system:
    st.subheader("⚙️ Pipeline Status & System Controls")
    
    col_sys1, col_sys2 = st.columns(2)
    
    with col_sys1:
        st.markdown("#### 📋 System Details")
        st.markdown(f"""
        * **Pipeline Database**: `price_monitor` (PostgreSQL)
        * **Fact Table**: `price_history` (pricing logs, stock history)
        * **Dimension Table**: `books_catalog` (unique metadata, UPC primary key)
        * **Archive Storage**: Partitioned local CSVs in `./data/`
        * **Collection Strategy**: Paginated Multi-Page Scrape + Individual Master-Detail requests
        """)
        
        # Log viewer
        st.markdown("#### 📄 Latest Scraper Logs (`logs/pipeline.log`)")
        
        # Check multiple possible log file locations
        log_candidates = ["logs/pipeline.log", "../logs/pipeline.log"]
        log_content = None
        for log_path in log_candidates:
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    logs = f.readlines()
                if logs:
                    log_content = "".join(logs[-25:])
                break
        
        if log_content:
            st.text_area("Pipeline Logs:", log_content, height=300)
        else:
            st.info("No log file found. Click **'Run Scraper Pipeline Now'** to execute the pipeline and generate logs.")
            
    with col_sys2:
        st.markdown("#### ⚡ ETL Pipeline Runner")
        st.markdown("""
        Clicking the button below executes the scraping pipeline (`python src/scraper.py`) locally.
        This will download the fresh HTML files, clean data types, update the Star Schema tables,
        and generate a new date-partitioned backup CSV.
        
        *Note: Scrapes run concurrently using ThreadPoolExecutor, completing much faster than before.*
        """)
        
        if st.button("Run Scraper Pipeline Now"):
            log_placeholder = st.empty()
            log_placeholder.info("Starting pipeline execution... This may take 1-2 minutes.")
            
            with st.spinner("Executing ETL Pipeline (Scraping books.toscrape.com & updating PostgreSQL)..."):
                try:
                    # Execute python src/scraper.py securely without shell=True
                    process = subprocess.run(
                        ["python", "src/scraper.py"], 
                        capture_output=True, 
                        text=True,
                        timeout=300  # 5 minute timeout
                    )
                    
                    # Show output regardless of success/failure
                    if process.stdout:
                        st.text_area("📋 Pipeline Console Output:", process.stdout, height=250)
                    if process.stderr:
                        st.text_area("⚠️ Pipeline Warnings/Errors:", process.stderr, height=150)
                    
                    if process.returncode == 0:
                        st.success("✅ Pipeline executed successfully! Click the button below to reload fresh data.")
                        if st.button("🔄 Reload Dashboard with New Data"):
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        st.error(f"Pipeline exited with error code: {process.returncode}. Check the output above for details.")
                        
                except subprocess.TimeoutExpired:
                    st.error("Pipeline timed out after 5 minutes. The target site may be slow or unreachable.")
                except Exception as e:
                    st.error(f"Failed to execute pipeline: {e}")
                    
        st.markdown("---")
        st.markdown("#### 💾 Download Datasets")
        st.markdown("Download raw datasets directly to analyze in Excel, R, or other tools.")
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv_snapshot = df_snapshot.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Latest Snapshot (CSV)",
                data=csv_snapshot,
                file_name="books_snapshot.csv",
                mime="text/csv"
            )
        with col_dl2:
            csv_history = df_history.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Historical Log (CSV)",
                data=csv_history,
                file_name="books_price_history.csv",
                mime="text/csv"
            )

# Footer Info
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #718096; font-size: 0.8rem;'>"
    "Data scraped for career demonstration purposes from books.toscrape.com. Designed as a data portfolio project."
    "</div>", 
    unsafe_allow_html=True
)
