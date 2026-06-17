# 🚀 Price Monitoring System - Execution Guide

This guide provides detailed, step-by-step instructions on how to set up, execute, and monitor the Price Monitoring ETL Pipeline and Streamlit Dashboard.

---

## 1️⃣ Environment Setup

Before running anything, ensure your environment is prepared.

1. **Install PostgreSQL**: Ensure PostgreSQL is installed and running on your machine.
2. **Environment Variables**: Make sure your `.env` file in the root directory contains the correct database credentials:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_NAME=price_monitor
   ```
3. **Install Dependencies**: Ensure you have all the required Python libraries installed:
   ```bash
   pip install -r requirements.txt
   ```

---

## 2️⃣ Running the ETL Pipeline (Data Collection)

The pipeline extracts data from the website, saves it to CSV backups, and loads it into the PostgreSQL Star Schema. You have three ways to run it:

### Option A: Using the Streamlit UI (Recommended for Users)
1. Start the dashboard (see Step 3 below).
2. Navigate to the **"⚙️ ETL Pipeline & Systems"** tab.
3. Click the **"Run Scraper Pipeline Now"** button.
4. Wait for the success message. The logs and data will automatically refresh.

### Option B: Using the Windows Batch Script (Recommended for Automation)
If you want to run the full pipeline (Scraper ➔ Analysis ➔ Comparison) automatically in one click:
1. Open your terminal or command prompt in the **project root directory**.
2. Run the batch script:
   ```cmd
   .\scripts\run_pipeline.bat
   ```
3. This will create a `logs/` folder and output everything to `logs/pipeline.log`.

### Option C: Running the Python Scripts Manually (For Developers)
Always run these scripts from the **project root directory**.

1. **Run the Scraper** (Fetches data & updates DB):
   ```bash
   python src/scraper.py
   ```
2. **Run the Data Analysis** (Generates statistical reports):
   ```bash
   python src/analyze.py
   ```
3. **Run the Price Comparison** (Detects price drops/hikes):
   ```bash
   python src/compare.py
   ```

---

## 3️⃣ Starting the Streamlit Dashboard

The interactive dashboard allows you to visualize the data, track inventory, and spot price drops.

1. Open your terminal in the **project root directory**.
2. Run the Streamlit server:
   ```bash
   streamlit run src/app.py
   ```
3. Your browser should automatically open to `http://localhost:8501`. If it doesn't, manually click the link in your terminal.

---

## 4️⃣ Connecting Power BI

If you want to view the advanced executive dashboard in Power BI:
1. Open Power BI Desktop.
2. Connect to the PostgreSQL database using the credentials from your `.env` file.
3. Import the `books_catalog` and `price_history` tables.
4. Apply the custom theme file located at `config/PriceMonitor_Theme.json`.
> *For detailed Power BI instructions, refer to `docs/PowerBI_Guide.md`.*

---

## 🛑 Troubleshooting

- **"ModuleNotFoundError: No module named 'src'"**: You are running the scripts from inside the `src/` folder. You MUST run all commands from the **root** folder of the project (`Price Monitoring System/`).
- **"psycopg2.OperationalError: Connection refused"**: PostgreSQL is not running, or your password in the `.env` file is incorrect.
- **"No log file found" in Streamlit**: This just means you haven't run the scraper yet. Go to the "ETL Pipeline & Systems" tab and click the run button to generate the first log file.
