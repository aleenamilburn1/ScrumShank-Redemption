# === Step 3: Blend actual + predicted → `swam_filled` ===
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

df = pd.read_sql("SELECT * FROM swam_predicted_table", engine)

# Use actual_swam unless all original fields were null
missing_mask = df[['swam_minority', 'swam_woman', 'swam_small', 'swam_micro_business']].isnull().all(axis=1)
df['swam_filled'] = df['actual_swam']
df.loc[missing_mask, 'swam_filled'] = df.loc[missing_mask, 'swam_predicted']

df.to_sql("swam_filled_table", engine, if_exists="replace", index=False)

print("✅ Step 3 complete: 'swam_filled' generated. You’re ready to visualize!")
