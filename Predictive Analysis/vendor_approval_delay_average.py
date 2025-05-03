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
# 3. Load approval date data
# ------------------------
query = """
SELECT 
    vendor_name, 
    requisition_submitted_date, 
    requisition_approved_date
FROM doc_data_enriched
"""
doc_data = pd.read_sql(query, engine)

# ------------------------
# 4. Compute Approval Delay per Order
# ------------------------

# Ensure date columns are datetime type
doc_data['requisition_submitted_date'] = pd.to_datetime(doc_data['requisition_submitted_date'])
doc_data['requisition_approved_date'] = pd.to_datetime(doc_data['requisition_approved_date'])

# Calculate approval delay in days
doc_data['approval_delay_days'] = (doc_data['requisition_approved_date'] - doc_data['requisition_submitted_date']).dt.days

# Filter valid delays
doc_data = doc_data[doc_data['approval_delay_days'].notnull()]
doc_data = doc_data[doc_data['approval_delay_days'] >= 0]

# ------------------------
# 5. Calculate Average Approval Delay by Vendor
# ------------------------

vendor_approval_delay = (
    doc_data.groupby('vendor_name')
    .agg(
        avg_approval_delay_days=('approval_delay_days', 'mean')
    )
    .reset_index()
)

# Round for readability
vendor_approval_delay['avg_approval_delay_days'] = vendor_approval_delay['avg_approval_delay_days'].round(2)

# ------------------------
# 6. Merge Approval Delay into vendor_view
# ------------------------

# Merge on vendor_name
vendor_view_updated = pd.merge(
    vendor_view,
    vendor_approval_delay,
    how='left',  # keep all vendors, even if they have no delay data
    on='vendor_name'
)

# ------------------------
# 7. Save updated vendor_view back to Postgres
# ------------------------

vendor_view_updated.to_sql(
    name="vendor_view",
    con=engine,
    if_exists="replace",  # Overwrite vendor_view
    index=False
)

print("✅ Updated vendor_view with avg_approval_delay_days saved to Postgres!")
