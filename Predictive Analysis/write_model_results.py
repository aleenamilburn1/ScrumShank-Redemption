# write_model_results.py

import pandas as pd
from sqlalchemy import create_engine

# ----------------------------
# 1. Configure your connection
# ----------------------------

def get_db_engine(user, password, host, port, dbname):
    """
    Creates a SQLAlchemy engine to connect to your Postgres database.
    """
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")


# ----------------------------
# 2. Write any DataFrame to Postgres
# ----------------------------

def write_to_postgres(df, table_name, engine, if_exists='replace'):
    """
    Writes a DataFrame to a PostgreSQL table.
    
    Parameters:
        df (pd.DataFrame): Your model's results
        table_name (str): The name of the destination table
        engine (SQLAlchemy Engine): The DB connection engine
        if_exists (str): 'replace', 'append', or 'fail'
    """
    df.to_sql(table_name, con=engine, if_exists=if_exists, index=False)
    print(f"✅ Data written to Postgres table: {table_name} (mode: {if_exists})")
