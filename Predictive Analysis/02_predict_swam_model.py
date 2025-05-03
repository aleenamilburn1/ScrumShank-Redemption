# === Step 2: Train model and generate `swam_predicted` ===
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

df = pd.read_sql("SELECT * FROM actual_swam", engine)

df['IsLocal'] = df['vendor_address_state'].astype(str).str.strip().str.upper().apply(lambda x: 1 if x == 'VA' else 0)
df['Category_encoded'] = LabelEncoder().fit_transform(df['nigp_description'].astype(str))
df['Transaction_encoded'] = LabelEncoder().fit_transform(df['procurement_transaction_desc'].astype(str))

X = df[['Category_encoded', 'Transaction_encoded', 'IsLocal']]
y = df['actual_swam']

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

df['swam_predicted'] = model.predict(X)

df.to_sql("swam_predicted_table", engine, if_exists="replace", index=False)

print("✅ Step 2 complete: 'swam_predicted' added using trained model.")
