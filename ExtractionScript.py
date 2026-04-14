import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv  

load_dotenv()  # Load environment variables from .env file

def extract_from_db(description=False):
    try: 
        cert_content = os.getenv('cert')
        with open("temp_cert.pem", "w") as f:
            f.write(cert_content)

        conn = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            port=4000,
            password=os.getenv('password'),
            database='library_db',
            ssl_ca= "temp_cert.pem",
            ssl_disabled=False
        )

        if not description:
            query = '''
            SELECT * FROM dim_books
            INNER JOIN book_categories ON dim_books.book_id = book_categories.book_id
            INNER JOIN dim_categories ON book_categories.category_id = dim_categories.category_id
            '''
        else:
            query = '''
            SELECT * FROM dim_books
            INNER JOIN book_categories ON dim_books.book_id = book_categories.book_id
            INNER JOIN dim_categories ON book_categories.category_id = dim_categories.category_id
            '''
    
        df = pd.read_sql(query, con=conn)
    
        return df
    
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
    
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print('Connection closed')

if __name__ == "__main__":
    print(extract_from_db()['title'])