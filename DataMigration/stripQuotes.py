input_path = '/Users/aleenamilburn/Desktop/Procurement_Data/eva_procurement_data_2025.csv'

# Read the entire file, fix only the header line
with open(input_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Strip quotes only from the header (first line)
header = lines[0].replace('"', '')

# Write back to the same file: cleaned header + untouched data
with open(input_path, 'w', encoding='utf-8') as f:
    f.write(header)
    f.writelines(lines[1:])

print("✅ Stripped quotes from header only and kept the rest of the file intact.")
