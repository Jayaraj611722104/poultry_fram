import pymysql

# Database connection details from .env
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Root12345',
    'database': 'poultry_farm_db'
}

def add_sold_count_column():
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # Check if column already exists
            cursor.execute("DESCRIBE chickens_daily")
            columns = [col[0] for col in cursor.fetchall()]
            
            if 'sold_count' not in columns:
                print("Adding 'sold_count' column to 'chickens_daily'...")
                cursor.execute("ALTER TABLE chickens_daily ADD COLUMN sold_count INT DEFAULT 0 AFTER deaths;")
                connection.commit()
                print("Column added successfully.")
            else:
                print("Column 'sold_count' already exists.")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    add_sold_count_column()
