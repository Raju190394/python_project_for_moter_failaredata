# Industrial Reliability & Cost Analytics Dashboard

A premium, high-performance analytics platform designed for industrial equipment monitoring. This tool calculates critical reliability metrics (MTTF, MTTR, Failure Rates) and provides a comprehensive financial overview of repair costs across multiple data sources.

---

## 🚀 Key Features

- **Reliability Metrics:** Automated calculation of:
  - **MTTF (Mean Time To Failure):** Average time before equipment fails.
  - **MTTR (Mean Time To Repair):** Average time taken to fix a failure.
  - **Failure Rate (λ):** Frequency of failures over a period.
  - **Repair Rate (μ):** Rate at which repairs are completed.
- **Multi-Sheet Cost Analysis:** Scans all sheets in an Excel file to calculate:
  - Total Repair Costs per sheet.
  - Costs excluding "MAINTENANCE" department (Adjustable filtering).
  - Grand Totals across the entire workbook.
- **Dynamic Visualizations:** Interactive timeline charts and failure reason distributions using Plotly.
- **Flexible Configuration:** Toggle between Minutes and Hours for all calculations.
- **Automatic Data Cleaning:** Handles inconsistent column names and non-numeric data gracefully.

---

## 🛠️ Technology Stack

This project is built using modern Python-based data science and web technologies:

- **[Python 3.x](https://www.python.org/):** Core programming language.
- **[Streamlit](https://streamlit.io/):** The web framework for creating the interactive dashboard UI.
- **[Pandas](https://pandas.pydata.org/):** High-performance data manipulation and analysis.
- **[Plotly](https://plotly.com/):** Interactive graphing library for the charts and visualizations.
- **[Openpyxl](https://openpyxl.readthedocs.io/):** For engine-level reading of modern Excel (`.xlsx`) files.
- **[NumPy](https://numpy.org/):** For efficient numerical calculations and handling of missing data.

---

## ⚙️ Project Setup

### 1. One-Click Setup (Windows Only)
Simply double-click **`setup_and_run.bat`**. It will automatically install Python dependencies and launch the dashboard.

### 2. Manual Installation
If you prefer the command line:
```bash
# Install required libraries
pip install -r requirements.txt

# Run the application
python -m streamlit run app.py
```

---

## � File Structure
- `app.py`: The main Streamlit application logic and UI.
- `requirements.txt`: List of all Python packages required.
- `setup_and_run.bat`: Automated batch script for Windows users.
- `setup.sh`: Automated shell script for Linux/Mac users.
- `generate_test_data.py`: Utility script to create sample Excel data.

---

## 📊 Data Requirements
For best results, your Excel file should include:
- **Downtime Column:** Numeric values representing minutes of downtime.
- **Repairing Cost Column:** Financial data for repairs.
- **Department Column:** (Optional) Used to filter out maintenance or other specific costs.
- **Reason Column:** (Optional) To see the breakdown of failure causes.

---

## 🔧 Troubleshooting
- **Missing Data in Summary:** Ensure your cost column name includes the word "cost". The system uses fuzzy matching to find relevant columns.
- **Streamlit Command Not Found:** Use `python -m streamlit run app.py` to ensure the module is executed via your Python environment.
- **Zero Values:** Ensure your Excel data is numeric and not stored as "text" format.
