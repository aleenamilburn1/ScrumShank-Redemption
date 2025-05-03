import pandas as pd
from sqlalchemy import create_engine

# ------------------------
# 1. Connect to Postgres
# ------------------------
engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

# ------------------------
# 2. Load necessary fields from doc_data_enriched
# ------------------------
query = """
SELECT 
    vendor_name, 
    nigp_description, 
    line_total
FROM doc_data_enriched
"""
doc_data = pd.read_sql(query, engine)

# ------------------------
# 3. Clean the data: drop duplicates and invalid values
# ------------------------

# Only positive line totals
doc_data = doc_data[doc_data['line_total'] > 0]

# Drop duplicate vendor/NIGP/line_total rows
doc_data = doc_data.drop_duplicates(subset=['vendor_name', 'nigp_description', 'line_total'])

# ------------------------
# 4. Calculate Vendor Dependency on NIGP Codes
# ------------------------

# Total spend per NIGP Description
nigp_total_spend = (
    doc_data.groupby('nigp_description')['line_total']
    .sum()
    .reset_index()
    .rename(columns={'line_total': 'total_nigp_spend'})
)

# Vendor spend per NIGP Description
vendor_nigp_spend = (
    doc_data.groupby(['vendor_name', 'nigp_description'])['line_total']
    .sum()
    .reset_index()
    .rename(columns={'line_total': 'vendor_spend_in_nigp'})
)

# Merge total spend into vendor spend
vendor_nigp = pd.merge(
    vendor_nigp_spend,
    nigp_total_spend,
    on='nigp_description',
    how='left'
)

# Calculate vendor share %
vendor_nigp['vendor_nigp_share_pct'] = (
    vendor_nigp['vendor_spend_in_nigp'] / vendor_nigp['total_nigp_spend'] * 100
)

# ------------------------
# 5. Find each vendor's max NIGP dependency
# ------------------------

# For each vendor, find the row where they have the highest share
vendor_max_nigp = (
    vendor_nigp.sort_values(['vendor_name', 'vendor_nigp_share_pct'], ascending=[True, False])
    .drop_duplicates(subset=['vendor_name'])
    .rename(columns={
        'nigp_description': 'vendor_max_dependency_nigp',
        'vendor_nigp_share_pct': 'vendor_max_nigp_dependency_pct'
    })
    [['vendor_name', 'vendor_max_dependency_nigp', 'vendor_max_nigp_dependency_pct']]
)

# ------------------------
# 6. Load existing vendor_view
# ------------------------

vendor_view = pd.read_sql("SELECT * FROM vendor_view", engine)

# ------------------------
# 7. Merge NIGP dependency into vendor_view
# ------------------------

vendor_view_updated = pd.merge(
    vendor_view,
    vendor_max_nigp,
    how='left',
    on='vendor_name'
)

# ------------------------
# 8. Save updated vendor_view back to Postgres
# ------------------------

vendor_view_updated.to_sql(
    name="vendor_view",
    con=engine,
    if_exists="replace",  # Overwrite existing vendor_view
    index=False
)

print("✅ vendor_view successfully updated with NIGP dependency information!")
