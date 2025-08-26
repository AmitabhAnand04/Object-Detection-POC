import psycopg2

def connect_to_db():
    try:
        # Connect to your postgres DB
        connection = psycopg2.connect(user="admin_bengal_beverage", password="ZTrail1234@#$", host="server-bengal-beverage.postgres.database.azure.com", port=5432, database="fridge_audit")
        
        print(connection)
        
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"Connected to database: {db_version[0]}")
        return cursor, connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None
 