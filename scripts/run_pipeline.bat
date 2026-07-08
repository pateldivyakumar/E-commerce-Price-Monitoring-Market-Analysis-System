@echo off
:: ============================================================
:: run_pipeline.bat - Windows Data Pipeline Orchestrator
:: Goal: Execute the full ETL pipeline (Scrape -> DB -> Analyze -> Compare)
::       and log the status of the run.
:: NOTE: Python scripts log directly to logs/pipeline.log via their
::       own logging module. This batch script logs its orchestration
::       status to logs/batch_run.log to avoid Windows file-lock conflicts.
:: ============================================================

title Price Monitoring ETL Pipeline

:: Ensure execution from project root
cd /d "%~dp0.."

:: Create logs directory if it doesn't exist
if not exist logs mkdir logs

echo ============================================================ >> logs\batch_run.log
echo Run Started: %date% %time% >> logs\batch_run.log
echo ============================================================ >> logs\batch_run.log

echo Starting E-Commerce Price Monitoring ETL Pipeline...
echo ------------------------------------------------------------

:: 1. Run the Scraper (Extracts data, saves CSVs, and updates PostgreSQL)
echo [1/3] Extracting and Loading data to CSV and PostgreSQL...
python src\scraper.py
if %errorlevel% neq 0 (
    echo [ERROR] Scraper failed. Check logs/pipeline.log for details.
    echo Status: FAILED (Scraper Error) >> logs\batch_run.log
    goto END
)
echo [SUCCESS] Scraper executed. Data saved to PostgreSQL and CSV backups.
echo [SUCCESS] Scraper completed >> logs\batch_run.log

:: 2. Run Data Analysis
echo [2/3] Generating catalog descriptive statistics...
python src\analyze.py
if %errorlevel% neq 0 (
    echo [ERROR] Analysis failed. Check logs/pipeline.log for details.
    echo Status: FAILED (Analysis Error) >> logs\batch_run.log
    goto END
)
echo [SUCCESS] Statistics generated. Report saved in reports/analysis_report.txt.
echo [SUCCESS] Analysis completed >> logs\batch_run.log

:: 3. Run Price Change Detection
echo [3/3] Scanning for price changes...
python src\compare.py
if %errorlevel% neq 0 (
    echo [ERROR] Price comparison failed. Check logs/pipeline.log for details.
    echo Status: FAILED (Comparison Error) >> logs\batch_run.log
    goto END
)
echo [SUCCESS] Price changes flagged. Report saved in reports/ folder.
echo [SUCCESS] Price comparison completed >> logs\batch_run.log

echo ------------------------------------------------------------
echo Status: SUCCESS >> logs\batch_run.log
echo ETL Pipeline Run Complete! All database and CSV data synced automatically.
echo ------------------------------------------------------------

:END
echo Run Finished: %date% %time% >> logs\batch_run.log
echo ============================================================ >> logs\batch_run.log
pause
