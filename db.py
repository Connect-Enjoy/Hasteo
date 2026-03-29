import os
import pg8000
import logging

# Neon Database Connection
CONNECTION_STRING = os.environ.get('DATABASE_URL','postgresql://neondb_owner:npg_iQmKogO2kqv0@ep-odd-glitter-aifc8x7w-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require')

def get_db_connection():
    try:
        database_url = os.environ.get('DATABASE_URL', CONNECTION_STRING)
        
        if database_url.startswith('postgresql://'):
            url_parts = database_url[13:]
            user_pass, host_db = url_parts.split('@', 1)
            username, password = user_pass.split(':', 1)
            
            if '/' in host_db:
                host_port, database = host_db.split('/', 1)
            else:
                host_port = host_db
                database = 'neondb'
            
            if ':' in host_port:
                host, port = host_port.split(':', 1)
            else:
                host = host_port
                port = '5432'
            
            if '?' in database:
                database = database.split('?')[0]
            
            # Use logging or print
            print(f"Connecting to: {host}:{port}/{database}")
            
            conn = pg8000.connect(
                host=host,
                user=username,
                password=password,
                database=database,
                port=int(port),
                ssl_context=True
            )
            print("Database connection successful!")
            return conn
            
    except Exception as err:
        print(f"Database connection failed: {err}")
        return None
