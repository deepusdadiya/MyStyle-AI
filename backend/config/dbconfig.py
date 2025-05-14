import psycopg2
from psycopg2.extras import RealDictCursor
from config.config import db_username, db_password, db_host, db_port, database_name, schema

def db_src_connect(DBDetails):
    if DBDetails.get('db_type').lower() == 'postgres':
        conn = psycopg2.connect(database=DBDetails.get('dbname'),
                                host=DBDetails.get('host'),
                                user=DBDetails.get('username'),
                                password=DBDetails.get('password'),
                                port=DBDetails.get('port')
                                )
        c = conn.cursor(cursor_factory=RealDictCursor)
        conn.autocommit = True
        return c, conn


def dbconnect():
    conn = psycopg2.connect(database=database_name,
                            host=db_host,
                            user=db_username,
                            password=db_password,
                            port=db_port,
                            options=f'''-c search_path={schema} ''')
    c = conn.cursor(cursor_factory=RealDictCursor)
    conn.autocommit = True
    return c, conn