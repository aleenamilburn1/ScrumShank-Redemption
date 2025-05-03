import pandas as pd
from sqlalchemy import create_engine

# ------------------------
# 1. Connect to Postgres
# ------------------------
engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

# ------------------------
# 2. Load 'doc_data_enriched' into DataFrame
# ------------------------
query = """
SELECT 
    vendor_name, 
    order_number, 
    swam_minority, 
    swam_woman, 
    swam_small, 
    swam_micro_business 
FROM doc_data_enriched
"""
doc_data = pd.read_sql(query, engine)

# ------------------------
# 3. Compute Vendor SWAM Status
# ------------------------

# Create a SWAM indicator at the order level
doc_data['swam_flag'] = (
    doc_data[['swam_minority', 'swam_woman', 'swam_small', 'swam_micro_business']]
    .fillna(0)
    .sum(axis=1)
    .apply(lambda x: 1 if x > 0 else 0)
)

# Group by Vendor
vendor_swam = (
    doc_data.groupby('vendor_name')
    .agg(
        total_orders=('order_number', 'nunique'),
        swam_orders=('swam_flag', 'sum')
    )
    .reset_index()
)

# Calculate SWAM Ratio
vendor_swam['swam_order_ratio'] = vendor_swam['swam_orders'] / vendor_swam['total_orders']

# Create Binary SWAM Vendor Flag
vendor_swam['vendor_ISswam'] = vendor_swam['swam_order_ratio'].apply(lambda x: 1 if x >= 0.5 else 0)

# ------------------------
# 4. Select only necessary columns for vendor_view
# ------------------------

vendor_view = vendor_swam[['vendor_name', 'vendor_ISswam']]

# ------------------------
# 5. Save to Postgres
# ------------------------

vendor_view.to_sql(
    name="vendor_view",
    con=engine,
    if_exists="replace",  # Replace if it exists
    index=False
)

print("✅ vendor_view table created successfully in Postgres with 'vendor_ISswam' column!")
