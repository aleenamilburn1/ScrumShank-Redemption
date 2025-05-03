# === Step 2: Train model and generate `swam_predicted` ===
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# Connect to Postgres
engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

# Load cleaned SWaM data
df = pd.read_sql("SELECT * FROM actual_swam", engine)

# Exclude rows with null actual_swam values — we can't train on these
df_train = df[df['actual_swam'].notnull()].copy()

# Feature engineering
df_train['IsLocal'] = df_train['vendor_address_state'].astype(str).str.strip().str.upper().apply(lambda x: 1 if x == 'VA' else 0)
df_train['Category_encoded'] = LabelEncoder().fit_transform(df_train['nigp_description'].astype(str))
df_train['Transaction_encoded'] = LabelEncoder().fit_transform(df_train['procurement_transaction_desc'].astype(str))

X_train = df_train[['Category_encoded', 'Transaction_encoded', 'IsLocal']]
y_train = df_train['actual_swam']

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# --- Step 2B: Apply model to ALL rows (even ones with null actual_swam)
df['IsLocal'] = df['vendor_address_state'].astype(str).str.strip().str.upper().apply(lambda x: 1 if x == 'VA' else 0)
df['Category_encoded'] = LabelEncoder().fit(df['nigp_description'].astype(str)).transform(df['nigp_description'].astype(str))
df['Transaction_encoded'] = LabelEncoder().fit(df['procurement_transaction_desc'].astype(str)).transform(df['procurement_transaction_desc'].astype(str))

X_full = df[['Category_encoded', 'Transaction_encoded', 'IsLocal']]
df['swam_predicted'] = model.predict(X_full)

# Save full results
df.to_sql("swam_predicted_table", engine, if_exists="replace", index=False)

print("✅ Step 2 complete: 'swam_predicted' added using trained model.")
