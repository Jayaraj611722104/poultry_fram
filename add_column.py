import sqlite3
import os

db_path = 'c:/Users/jayar/OneDrive/Documents/New folder/PeruFarm_Poultry_System/poultry_farm/instance/poultry_farm.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE chickens_daily ADD COLUMN sold_count INTEGER DEFAULT 0;")
        conn.commit()
        print("Column 'sold_count' added successfully.")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
else:
    print(f"DB not found at {db_path}")
