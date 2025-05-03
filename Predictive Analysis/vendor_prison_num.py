import pandas as pd
from sqlalchemy import create_engine

# ------------------------
# 1. Connect to Postgres
# ------------------------
engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

# ------------------------
# 2. Load existing vendor_view
# ------------------------
vendor_view = pd.read_sql("SELECT * FROM vendor_view", engine)


# ------------------------
# Load doc_data_enriched
# ------------------------
query = """
SELECT vendor_name, prison_id
FROM doc_data_enriched
"""
doc_data = pd.read_sql(query, engine)

# ------------------------
# Calculate unique prison_ids per vendor
# ------------------------
vendor_prison_reach = (
    doc_data.groupby('vendor_name')['prison_id']
    .nunique()
    .reset_index()
    .rename(columns={'prison_id': 'vendor_prison_count'})
)

# ------------------------
# Load vendor_view
# ------------------------
vendor_view = pd.read_sql("SELECT * FROM vendor_view", engine)

# ------------------------
# Merge prison reach into vendor_view
# ------------------------
vendor_view_updated = pd.merge(
    vendor_view,
    vendor_prison_reach,
    how='left',
    on='vendor_name'
)

# Fill missing vendors (who had no prison links) with 0
vendor_view_updated['vendor_prison_count'] = vendor_view_updated['vendor_prison_count'].fillna(0).astype(int)

# ------------------------
# Save updated vendor_view
# ------------------------
vendor_view_updated.to_sql(
    name="vendor_view",
    con=engine,
    if_exists="replace",
    index=False
)

print("✅ vendor_view updated successfully with vendor_prison_count column added!")
