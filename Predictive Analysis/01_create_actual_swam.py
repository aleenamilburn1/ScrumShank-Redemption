# === Step 1: Create `actual_swam` column from original SWaM flags ===
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

df = pd.read_sql("SELECT * FROM doc_data_enriched", engine)

df['actual_swam'] = df[['swam_minority', 'swam_woman', 'swam_small', 'swam_micro_business']].sum(axis=1).apply(lambda x: 1 if x > 0 else 0)

df.to_sql("actual_swam", engine, if_exists="replace", index=False)

print("✅ Step 1 complete: 'actual_swam' column added.")
