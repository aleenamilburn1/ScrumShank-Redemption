import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine

# ============================
# Step 1: Load and Prepare Data
# ============================
file_path = "/Users/aleenamilburn/Desktop/2024-2025 Classes/2025/IS Capstone/ScrumShank-Redemption/Predictive Analysis/doc_data_enriched.csv"
use_cols = [
    'vendor_location_name', 'vendor_name', 'import_year', 'order_number',
    'quantity_ordered', 'unit_price', 'nigp_description',
    'requisition_submitted_date', 'requisition_approved_date',
    'ordered_date', 'most_recent_receiving_date'
]

# Dates to parse
date_cols = [
    'requisition_submitted_date', 'requisition_approved_date',
    'ordered_date', 'most_recent_receiving_date'
]

aggregated_data = []

for chunk in pd.read_csv(file_path, usecols=use_cols, parse_dates=date_cols, chunksize=100000):
    chunk = chunk.dropna(subset=[
        'vendor_location_name', 'import_year', 'order_number',
        'quantity_ordered', 'unit_price'
    ])
    
    # Compute spend
    chunk['spend'] = chunk['quantity_ordered'] * chunk['unit_price']
    
    # Compute delay features
    chunk['approval_delay_days'] = (chunk['requisition_approved_date'] - chunk['requisition_submitted_date']).dt.days
    chunk['fulfillment_delay_days'] = (chunk['most_recent_receiving_date'] - chunk['ordered_date']).dt.days
    
    # Replace negative or missing delays with NaN, we'll handle later
    chunk.loc[chunk['approval_delay_days'] < 0, 'approval_delay_days'] = np.nan
    chunk.loc[chunk['fulfillment_delay_days'] < 0, 'fulfillment_delay_days'] = np.nan

    # Aggregate
    grouped = chunk.groupby(['vendor_name', 'import_year']).agg(
        total_spend=('spend', 'sum'),
        num_transactions=('order_number', 'nunique'),
        num_categories=('nigp_description', 'nunique'),
        mean_approval_delay=('approval_delay_days', 'mean'),
        mean_fulfillment_delay=('fulfillment_delay_days', 'mean'),
    ).reset_index()

    aggregated_data.append(grouped)

vendor_yearly = pd.concat(aggregated_data, ignore_index=True)

# Drop any rows where delay features are still missing
vendor_yearly = vendor_yearly.dropna(subset=['mean_approval_delay', 'mean_fulfillment_delay'])

# ============================
# Step 2: Normalize Features
# ============================
features = vendor_yearly[[
    'total_spend', 'num_transactions', 'num_categories',
    'mean_approval_delay', 'mean_fulfillment_delay'
]]

scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

# ============================
# Step 3: Train Isolation Forest
# ============================
contamination_rate = 0.05
iso_forest = IsolationForest(n_estimators=100, contamination=contamination_rate, random_state=42)
iso_forest.fit(scaled_features)

# ============================
# Step 4: Apply and Evaluate
# ============================
vendor_yearly['anomaly_score'] = iso_forest.decision_function(scaled_features)
vendor_yearly['is_anomaly'] = iso_forest.predict(scaled_features) == -1

# Terminal output
print("\n📊 Anomaly Detection Summary:")
print(vendor_yearly['is_anomaly'].value_counts())
print("\n🧪 Anomaly % detected: {:.2f}%".format(vendor_yearly['is_anomaly'].mean() * 100))

print("\n🔍 Top 10 Anomalous Vendor-Year Combinations:")
print(vendor_yearly[vendor_yearly['is_anomaly']].sort_values('anomaly_score').head(10))

from sqlalchemy import create_engine

username = "postgres"
password = "ScrumShankRedemp!"
host = "localhost"
port = "5432"
database = "ScrumRedemp"

# 🔌 Connect to your database
engine = create_engine(f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")

# 📝 Write your anomaly dataframe (e.g., vendor_yearly) to Postgres
# Make sure the dataframe exists and has no index issues

vendor_yearly.to_sql(
    name="vendor_anomaly_results",
    con=engine,
    if_exists="replace",  # overwrite with latest results
    index=False
)

print("✅ Done! Anomaly results are now in the 'vendor_anomaly_results' table.")

