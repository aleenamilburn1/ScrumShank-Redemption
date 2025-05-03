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
# 3. Load necessary fields from doc_data_enriched
# ------------------------
query = """
SELECT 
    vendor_name, 
    po_category_description, 
    line_total
FROM doc_data_enriched
"""
doc_data = pd.read_sql(query, engine)

# ------------------------
# 4. Calculate Vendor Dependency by PO Category
# ------------------------

# Step 1: Total spend per PO Category (all vendors combined)
category_total_spend = (
    doc_data.groupby('po_category_description')['line_total']
    .sum()
    .reset_index()
    .rename(columns={'line_total': 'total_category_spend'})
)

# Step 2: Vendor spend per PO Category
vendor_category_spend = (
    doc_data.groupby(['vendor_name', 'po_category_description'])['line_total']
    .sum()
    .reset_index()
    .rename(columns={'line_total': 'vendor_spend_in_category'})
)

# Step 3: Merge total category spend into vendor category spend
vendor_category = pd.merge(
    vendor_category_spend,
    category_total_spend,
    on='po_category_description',
    how='left'
)

# Step 4: Calculate Vendor's Share % within the Category
vendor_category['vendor_category_share_pct'] = (
    vendor_category['vendor_spend_in_category'] / vendor_category['total_category_spend'] * 100
)

# Step 5: For each vendor, find the category with the highest dependency
vendor_max_dependency = (
    vendor_category.sort_values(['vendor_name', 'vendor_category_share_pct'], ascending=[True, False])
    .groupby('vendor_name')
    .first()
    .reset_index()
)

# Select only necessary columns
vendor_max_dependency = vendor_max_dependency[['vendor_name', 'vendor_category_share_pct', 'po_category_description']]
vendor_max_dependency = vendor_max_dependency.rename(columns={
    'vendor_category_share_pct': 'vendor_max_category_dependency_pct',
    'po_category_description': 'vendor_max_dependency_category'
})

# Round the dependency % for cleanliness
vendor_max_dependency['vendor_max_category_dependency_pct'] = vendor_max_dependency['vendor_max_category_dependency_pct'].round(2)

# ------------------------
# 5. Merge into vendor_view
# ------------------------

vendor_view_updated = pd.merge(
    vendor_view,
    vendor_max_dependency,
    how='left',
    on='vendor_name'
)

# ------------------------
# 6. Save updated vendor_view back to Postgres
# ------------------------

vendor_view_updated.to_sql(
    name="vendor_view",
    con=engine,
    if_exists="replace",  # Overwrite vendor_view
    index=False
)

print("✅ vendor_view updated successfully with dependency metrics!")
