import pandas as pd
from sqlalchemy import create_engine, text

# Connect to database
engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

# Read from existing model output
df = pd.read_sql("SELECT * FROM swam_predicted_table", engine)

# Correct swam_filled logic
df['swam_filled'] = df.apply(
    lambda row: row['actual_swam'] if pd.notnull(row['actual_swam']) else row['swam_predicted'],
    axis=1
)

# 🔄 Manual overwrite logic:
with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE swam_filled_table;"))
    df.to_sql("swam_filled_table", con=conn, if_exists="append", index=False)

print("✅ Table cleared and refreshed without dropping or breaking views.")