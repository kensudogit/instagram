import psycopg2
from psycopg2 import sql
import os

# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'your_database')
DB_USER = os.getenv('DB_USER', 'your_username')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')

# Function to insert data into the database
def insert_data(table_name, data):
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor()

        # Create an insert query
        insert_query = sql.SQL("""
            INSERT INTO {table} (column1, column2) VALUES (%s, %s)
        """).format(table=sql.Identifier(table_name))

        # Execute the insert query
        cursor.execute(insert_query, data)

        # Commit the transaction
        connection.commit()

        print("Data inserted successfully")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")

    finally:
        if connection:
            cursor.close()
            connection.close()

# Example usage
if __name__ == "__main__":
    # Example data to insert
    example_data = ('value1', 'value2')
    insert_data('your_table_name', example_data) 