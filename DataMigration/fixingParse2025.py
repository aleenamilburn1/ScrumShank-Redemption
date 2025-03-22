import os

# === CONFIG ===
file_path = '/Users/aleenamilburn/Desktop/Procurement_Data/eva_procurement_data_2025.csv'  # Change this as needed
expected_column_count = 44  # Adjust if your schema changes

# === FUNCTION TO CHECK ROWS ===
def inspect_csv_structure(file_path, expected_columns):
    print(f"🔍 Inspecting file: {file_path}")
    malformed_lines = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_number, line in enumerate(f, start=1):
            # Split the line on commas — assumes no commas inside quoted strings
            fields = line.strip().split(',')
            if len(fields) != expected_columns:
                malformed_lines.append((line_number, len(fields), line.strip()))

    if malformed_lines:
        print(f"\n⚠️ Found {len(malformed_lines)} malformed line(s):\n")
        for lineno, field_count, content in malformed_lines:
            print(f"Line {lineno} | Fields: {field_count}")
            print(f"  ↪ {content[:250]}")  # Truncate for readability
            print("-" * 60)
    else:
        print("✅ No malformed lines found! 🎉")

# === RUN CHECK ===
inspect_csv_structure(file_path, expected_column_count)
