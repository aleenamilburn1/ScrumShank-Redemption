import os
from glob import glob

# === CONFIG ===
data_folder = '/Users/aleenamilburn/Desktop/Procurement_Data'
csv_files = glob(os.path.join(data_folder, 'eva_procurement_data_*.csv'))

print(f"🔍 Found {len(csv_files)} files.\n")

# === Extract and print all headers ===
for file_path in sorted(csv_files):  # sort for year-order listing
    with open(file_path, 'r', encoding='utf-8') as f:
        header_line = f.readline().strip()
        file_name = os.path.basename(file_path)
        columns = header_line.split(',')

        print(f"📄 {file_name}")
        print(f"   → Column Count: {len(columns)}")
        print("   → Columns:")
        for i, col in enumerate(columns, start=1):
            print(f"     {i:02d}. {col}")
        print("—" * 60)
