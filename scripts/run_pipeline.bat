@echo off
:: ============================================================
:: run_pipeline.bat - Windows Data Pipeline Orchestrator
:: Goal: Execute the full ETL pipeline (Scrape -> DB -> Analyze -> Compare)
::       and log the status of the run.
:: ============================================================

title Price Monitoring ETL Pipeline

:: Ensure execution from project root
cd %~dp0..

:: Create logs directory if it doesn't exist
if not exist logs mkdir logs

echo ============================================================ >> logs\pipeline.log
echo Run Started: %date% %time% >> logs\pipeline.log
echo ============================================================ >> logs\pipeline.log

echo Starting E-Commerce Price Monitoring ETL Pipeline...
echo ------------------------------------------------------------

:: 1. Run the Scraper (Extracts data, saves CSVs, and updates PostgreSQL)
echo [1/3] Extracting and Loading data to CSV and PostgreSQL...
python src\scraper.py >> logs\pipeline.log 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Scraper failed. Check logs/pipeline.log for details.
    echo Status: FAILED (Scraper Error) >> logs\pipeline.log
    goto END
)
echo [SUCCESS] Scraper executed. Data saved to PostgreSQL and CSV backups.

:: 2. Run Data Analysis
echo [2/3] Generating catalog descriptive statistics...
python src\analyze.py >> logs\pipeline.log 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Analysis failed. Check logs/pipeline.log for details.
    echo Status: FAILED (Analysis Error) >> logs\pipeline.log
    goto END
)
echo [SUCCESS] Statistics generated. Report saved in reports/analysis_report.txt.

:: 3. Run Price Change Detection
echo [3/3] Scanning for price changes...
python src\compare.py >> logs\pipeline.log 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Price comparison failed. Check logs/pipeline.log for details.
    echo Status: FAILED (Comparison Error) >> logs\pipeline.log
    goto END
)
echo [SUCCESS] Price changes flagged. Report saved in reports/ folder.

echo ------------------------------------------------------------
echo Status: SUCCESS >> logs\pipeline.log
echo ETL Pipeline Run Complete! All database and CSV data synced automatically.
echo ------------------------------------------------------------

:END
echo Run Finished: %date% %time% >> logs\pipeline.log
echo ============================================================ >> logs\pipeline.log
pause
