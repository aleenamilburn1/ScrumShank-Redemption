import os
import pandas as pd
import csv
from glob import glob

# === CONFIGURATION ===
DATA_FOLDER = 'DataMigration/Cleaned_Procurement_Data'
EXPECTED_COLUMNS = 44
FILE_PATTERN = 'eva_procurement_data_*.csv'

# === RESULTS TRACKER ===
files_with_issues = []

# === MAIN PROCESSING ===
csv_files = glob(os.path.join(DATA_FOLDER, FILE_PATTERN))

if not csv_files:
    print("⚠️ No matching CSV files found.")
else:
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        print(f"\n📂 Processing: {filename}")
        print("-" * 60)

        issue_found = False

        # === COUNT LINES ===
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                total_lines = sum(1 for line in f) - 1
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            files_with_issues.append(filename)
            continue

        # === READ WITH PANDAS ===
        try:
            df_clean = pd.read_csv(file_path, on_bad_lines='skip')
            clean_rows = len(df_clean)
            dropped_rows = total_lines - clean_rows
            if dropped_rows > 0:
                print(f"⚠️ Dropped {dropped_rows} rows ({(dropped_rows / total_lines) * 100:.2f}%)")
                issue_found = True
        except Exception as e:
            print(f"❌ Error loading with pandas: {e}")
            files_with_issues.append(filename)
            continue

        # === COLUMN COUNT CHECK ===
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) != EXPECTED_COLUMNS:
                        print("🚨 At least one row has incorrect column count.")
                        issue_found = True
                        break
        except Exception as e:
            print(f"❌ Error checking structure: {e}")
            files_with_issues.append(filename)
            continue

        if not issue_found:
            print("✅ All rows imported correctly and match expected structure.")
        else:
            files_with_issues.append(filename)

    # === FINAL SUMMARY ===
    print("\n" + "=" * 60)
    print("🧾 SUMMARY")
    if files_with_issues:
        print("🚫 Files with structural issues:")
        for file in files_with_issues:
            print(f" - {file}")
    else:
        print("🎉 All files are clean and ready for migration!")

