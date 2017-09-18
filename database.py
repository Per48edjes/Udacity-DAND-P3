import sqlite3
import pandas as pd
import glob

# Setup database environment
conn = sqlite3.connect('SF_OSM.db')
conn.text_factory = str
c = conn.cursor()

# Import schema
f = open('schema.sql', 'r')
schema_str = f.read()
c.executescript(schema_str)
f.close()

# Look for all CSVs
file_paths = "*.csv"
csvs = glob.glob(file_paths)
table_names = []
for csv in csvs:
    table_names.append(csv.rsplit('.',1)[0])

# Import each file into database
tables = zip(csvs, table_names)
for csv, table in tables:
    df = pd.read_csv(csv)
    df.to_sql(table, conn, if_exists='append', index=False)
