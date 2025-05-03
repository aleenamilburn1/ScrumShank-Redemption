import pandas as pd
from sqlalchemy import create_engine

# -------------------------------
# 1. Load Excel data
# -------------------------------
file_path = "/Users/aleenamilburn/Desktop/2024-2025 Classes/2025/IS Capstone/ScrumShank-Redemption/Predictive Analysis/doc_data_enriched.xlsx"

df = pd.read_excel(file_path)

# -------------------------------
# 2. Normalize SWaM fields (force proper nulls)
# -------------------------------
swam_fields = ['swam_minority', 'swam_micro_business', 'swam_woman', 'swam_small']

for col in swam_fields:
    df[col] = pd.to_numeric(df[col], errors='coerce')  # Converts blanks/strings to NaN

# -------------------------------
# 3. Compute actual_swam
# -------------------------------
df['actual_swam'] = df[swam_fields].apply(
    lambda row: None if row.isnull().all() else int((row == 1).any()), axis=1
)

# -------------------------------
# 4. Optional sanity check (preview)
# -------------------------------
print(df[['swam_minority', 'swam_micro_business', 'swam_woman', 'swam_small', 'actual_swam']].head(10))

# -------------------------------
# 5. Write to Postgres (if needed)
# -------------------------------
engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

df.to_sql("actual_swam", engine, if_exists="replace", index=False)

print("✅ actual_swam column successfully created and exported.")
