# --- Import required libraries ---
import os                      # Handles file paths and directories
import pandas as pd            # For reading and modifying CSV files
import psycopg2                # PostgreSQL connector for Python
from glob import glob          # Allows pattern-based file search (e.g., *.csv)

# --- CONFIGURATION SECTION ---

# The folder where your CSV files are stored
# Make sure all your procurement CSVs are in this folder
data_folder = '/Users/aleenamilburn/Desktop/Procurement_Data'

# PostgreSQL connection settings — update 'your_password' to match your real password
db_config = {
    'dbname': 'ScrumRedemp',       # Your PostgreSQL database name
    'user': 'postgres',            # The username you're connecting with
    'password': 'ScrumShankRedemp!',   # <-- Change this to your actual password
    'host': 'localhost',           # Host (use 'localhost' if you're running PostgreSQL locally)
    'port': 5432                   # Default PostgreSQL port
}

# Name of the table you're inserting data into (must already exist in the database)
target_table = 'eva_procurement_data'

# --- STEP 1: FIND & PROCESS CSV FILES ---

# Find all files in your data folder that match the pattern
# This assumes your files are named like "eva_procurement_data_2019.csv"
csv_files = glob(os.path.join(data_folder, 'eva_procurement_data_*.csv'))

# Loop through each CSV file
for file_path in csv_files:
    # Get just the file name (e.g., "eva_procurement_data_2019.csv")
    file_name = os.path.basename(file_path)

    # Extract the last 4 digits from the file name to get the year (e.g., "2019")
    # Adjust this if your file naming pattern changes!
    year_str = file_name[-8:-4]

    print(f"Processing: {file_name} | Year: {year_str}")

    # Load the CSV into a pandas DataFrame
    df = pd.read_csv(file_path)

    # Add two new columns to each row
    df['import_year'] = int(year_str)      # Add a column to track which year this file represents
    df['source_file'] = file_name          # Add a column to track which file each row came from

    # Create a temporary file with the new columns added
    # You can delete this step if you don't want to save the modified files
    temp_path = os.path.join(data_folder, f"ImportYearSourceFile_{file_name}")
    df.to_csv(temp_path, index=False)

    # --- STEP 2: CONNECT TO POSTGRESQL AND LOAD DATA ---

    # Establish a connection to your PostgreSQL database using your credentials
    
    # creates a connection object that gives python access to the db
    conn = psycopg2.connect(**db_config) 
    # cursor object to execute sql commands thru the connection
    cur = conn.cursor()

    # Open the temporary file and skip the header (PostgreSQL COPY requires this)
    with open(temp_path, 'r') as f:
        next(f)  # Skip the first line (header row)
        
        # Load the CSV into the PostgreSQL table using COPY
        # Make sure the columns in the file match your table columns in order
        cur.copy_expert(f"COPY {target_table} FROM STDIN WITH CSV", f)

    # Commit the transaction to make changes permanent
    conn.commit()

    # Clean up: close the cursor and the connection
    cur.close()
    conn.close()

    print(f"Successfully loaded into {target_table}: {file_name}")

# Once all files have been processed, print a final message
print("All procurement files processed and imported into PostgreSQL! You are deserving of praise.")
