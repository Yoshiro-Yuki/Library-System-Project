import pandas as pd
import mysql.connector

def extract_from_db(ssl_path='isrgroot.pem', description=False):
    try: 
        conn = mysql.connector.connect(
            host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
            user="3c7nm7q6RHzNf6t.root",
            port=4000,
            password="6tTTy8Rk1cEiH1dR",
            database='library_db',
            ssl_ca= ssl_path,
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