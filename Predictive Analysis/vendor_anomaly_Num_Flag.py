import pandas as pd
from sqlalchemy import create_engine

# ------------------------
# 1. Connect to Postgres
# ------------------------
engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

# ------------------------
# 2. Load vendor_view
# ------------------------
vendor_view = pd.read_sql("SELECT * FROM vendor_view", engine)

# ------------------------
# 3. Drop old anomaly columns if they exist
# ------------------------
for col in ['vendor_is_anomaly', 'is_anomaly', 'num_anomalous']:
    if col in vendor_view.columns:
        vendor_view = vendor_view.drop(columns=[col])

# ------------------------
# 4. Load vendor_anomaly_results
# ------------------------
query = """
SELECT vendor_name, import_year, is_anomaly
FROM vendor_anomaly_results
"""
vendor_anomalies = pd.read_sql(query, engine)

# ------------------------
# 5. Aggregate: count years vendor was anomalous
# ------------------------

# Only keep rows where is_anomaly = 1
anomalous_years = vendor_anomalies[vendor_anomalies['is_anomaly'] == 1]

# Count how many different years were anomalous per vendor
vendor_anomalies_agg = (
    anomalous_years.groupby('vendor_name')['import_year']
    .nunique()
    .reset_index()
    .rename(columns={'import_year': 'num_anomalous'})
)

# Create is_anomaly flag: 1 if vendor had ANY anomaly
vendor_anomalies_agg['is_anomaly'] = vendor_anomalies_agg['num_anomalous'].apply(lambda x: 1 if x >= 1 else 0)

# ------------------------
# 6. Merge into vendor_view
# ------------------------

vendor_view_updated = pd.merge(
    vendor_view,
    vendor_anomalies_agg[['vendor_name', 'is_anomaly', 'num_anomalous']],
    how='left',
    on='vendor_name'
)

# Fill missing vendors (vendors with no anomalies)
vendor_view_updated['is_anomaly'] = vendor_view_updated['is_anomaly'].fillna(0).astype(int)
vendor_view_updated['num_anomalous'] = vendor_view_updated['num_anomalous'].fillna(0).astype(int)

# ------------------------
# 7. Save updated vendor_view
# ------------------------

vendor_view_updated.to_sql(
    name="vendor_view",
    con=engine,
    if_exists="replace",
    index=False
)

print("✅ vendor_view updated successfully with clean is_anomaly and num_anomalous columns!")
