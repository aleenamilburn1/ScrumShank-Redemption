import os
import csv
from glob import glob

# === CONFIGURATION ===
SOURCE_FOLDER = '/Users/aleenamilburn/Desktop/Procurement_Data'
DEST_FOLDER = '/Users/aleenamilburn/Desktop/Cleaned_Procurement_Data'
EXPECTED_COLUMNS = 44
FILE_PATTERN = 'eva_procurement_data_*.csv'

# === SETUP OUTPUT FOLDER ===
os.makedirs(DEST_FOLDER, exist_ok=True)

# === MAIN LOOP ===
csv_files = glob(os.path.join(SOURCE_FOLDER, FILE_PATTERN))
summary = []

for file_path in csv_files:
    filename = os.path.basename(file_path)
    print(f"\n📂 Processing: {filename}")
    print("-" * 60)

    output_path = os.path.join(DEST_FOLDER, filename)

    total_rows = 0
    valid_rows = 0

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile, \
         open(output_path, 'w', encoding='utf-8', newline='') as outfile:

        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        for i, row in enumerate(reader):
            total_rows += 1
            if i == 0:
                writer.writerow(row)  # Write header
                continue
            if len(row) == EXPECTED_COLUMNS:
                writer.writerow(row)
                valid_rows += 1

    dropped_rows = total_rows - 1 - valid_rows
    pct_dropped = (dropped_rows / (total_rows - 1)) * 100 if total_rows > 1 else 0

    if dropped_rows == 0:
        print("✅ No malformed rows found.")
    else:
        print(f"⚠️ Dropped {dropped_rows} rows ({pct_dropped:.4f}%)")

    summary.append((filename, dropped_rows, pct_dropped))

# === FINAL SUMMARY ===
print("\n" + "=" * 60)
print("🧾 FINAL CLEANING SUMMARY")
for fname, dropped, pct in summary:
    if dropped > 0:
        print(f"🚫 {fname} — Dropped {dropped} rows ({pct:.4f}%)")
    else:
        print(f"✅ {fname} — Clean")

print("\n✅ Done. All cleaned files saved to:")
print(DEST_FOLDER)
