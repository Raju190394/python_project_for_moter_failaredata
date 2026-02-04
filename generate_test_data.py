import pandas as pd

# Creating a sample failure data file as per user requirements
data = {
    "Date": pd.date_range(start="2024-01-01", periods=10, freq="D"),
    "Downtime_Minutes": [45, 0, 120, 0, 30, 0, 0, 60, 15, 0],
    "Repair_Time_Minutes": [45, 0, 120, 0, 30, 0, 0, 60, 15, 0],
    "Comments": ["Motor issue", "OK", "Belt break", "OK", "Sensor clean", "OK", "OK", "Oil leak", "Loose screw", "OK"]
}

df = pd.DataFrame(data)

# Save to Excel
file_path = "failure_data_new.xlsx"
df.to_excel(file_path, index=False)
print(f"Sample file generated: {file_path}")
