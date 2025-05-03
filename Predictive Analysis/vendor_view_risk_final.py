import pandas as pd
from sqlalchemy import create_engine

# ------------------------
# 1. Connect to Postgres Database
# ------------------------
engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

# ------------------------
# 2. Load Existing Vendor View Table
# ------------------------
# Pull the latest vendor-level view, which already contains key aggregated features 
# such as dependency percentages, anomaly flags, prison reach, and spend share.
vendor_view = pd.read_sql("SELECT * FROM vendor_view", engine)

# ------------------------
# 3. Dynamically Scale Features for Risk Modeling
# ------------------------

# Calculate maximum values needed for normalization between 0 and 1.
# This avoids intermediate scaled columns being stored.

max_num_anomalous = vendor_view['num_anomalous'].max()
max_prison_count = vendor_view['vendor_prison_count'].max()
max_spend_share = vendor_view['vendor_spend_share_2024'].max()

# Perform scaling only inside the risk calculation (on the fly)
num_anomalous_scaled = vendor_view['num_anomalous'] / max_num_anomalous if max_num_anomalous > 0 else 0
vendor_prison_count_scaled = vendor_view['vendor_prison_count'] / max_prison_count if max_prison_count > 0 else 0
vendor_spend_share_scaled = vendor_view['vendor_spend_share_2024'] / max_spend_share if max_spend_share > 0 else 0

# ------------------------
# 4. Calculate Vendor Risk Score
# ------------------------

# Create a composite risk score based on weighted feature contributions.


vendor_view['vendor_risk_score'] = (
    0.2941 * vendor_view['vendor_max_category_dependency_pct'] +  
    # 29.41% weight:
    # Vendors dominating a major PO category represent macro-level supply chain risk.

    0.2941 * vendor_view['vendor_max_nigp_dependency_pct'] +       
    # 29.41% weight:
    # Vendors dominating at the commodity (NIGP) level introduce micro-level dependency risk.

    0.1176 * vendor_view['is_anomaly'] * 100 +                     
    # 11.76% weight:
    # Behavioral anomalies are strong indicators of potential instability.

    0.1176 * num_anomalous_scaled * 100 +             
    # 11.76% weight:
    # Recurring anomalies demonstrate deeper systemic risk.

    0.0882 * vendor_prison_count_scaled * 100 +
    # 8.82% weight:
    # Broader prison reach expands operational risk exposure.

    0.0882 * vendor_spend_share_scaled * 100
    # 8.82% weight:
    # Financial monopolization risk through disproportionate spend control.
)

# Round risk scores to two decimal places for clean presentation.
vendor_view['vendor_risk_score'] = vendor_view['vendor_risk_score'].round(2)

# ------------------------
# 5. Assign Vendor Risk Tiers Based on Score
# ------------------------

# Categorize vendors into defined risk bands:
# High Risk = score >= 70
# Medium Risk = score between 40 and 70
# Low Risk = score < 40

def assign_risk_tier(score):
    if score >= 70:
        return 'High Risk'
    elif score >= 40:
        return 'Medium Risk'
    else:
        return 'Low Risk'

vendor_view['vendor_risk_tier'] = vendor_view['vendor_risk_score'].apply(assign_risk_tier)

vendor_view = vendor_view.drop(columns=[col for col in columns_to_drop if col in vendor_view.columns])

# ------------------------
# 6. Save Updated Vendor View Back to Database
# ------------------------

# Replace the existing vendor_view table with the newly updated version 
# containing only final calculated fields: vendor_risk_score and vendor_risk_tier.

vendor_view.to_sql(
    name="vendor_view",
    con=engine,
    if_exists="replace",
    index=False
)

print("vendor_view updated successfully without extra scaled columns!")
