import csv

input_path = '/Users/aleenamilburn/Desktop/Procurement_Data/eva_procurement_data_2025.csv'
output_path = '/Users/aleenamilburn/Desktop/Procurement_Data/eva_procurement_data_2025_cleaned.csv'

bad_line_number = 1005897  # line number from inspection (starts at 1)

with open(input_path, 'r', newline='', encoding='utf-8') as infile, \
     open(output_path, 'w', newline='', encoding='utf-8') as outfile:

    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    for line_num, row in enumerate(reader, start=1):
        if line_num == bad_line_number:
            # Fix the unescaped quote in Item Description (index 4)
            if len(row) == 45 and '"' in row[4]:
                row[4] = row[4].replace('"', 'in')  # Replace inch symbol
                print(f"✅ Fixed line {line_num}")
        writer.writerow(row)

print(f"\n✅ Cleaned file written to:\n{output_path}")
