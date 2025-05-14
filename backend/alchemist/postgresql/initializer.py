from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.ext.declarative import declarative_base
from config.config import database_name, db_username, db_password, db_host, db_port, schema

DATABASE_USER: str = db_username
"""str: User of the database.
"""
DATABASE_PASSWORD: str = db_password
"""str: Password for the user of the database.
"""
DATABASE_HOST: str = db_host
"""str: Host IP of the database.
"""
DATABASE_PORT: str = db_port
"""str: Port of the database.
"""
DATABASE_NAME: str = database_name
"""str: Name of the database.
"""
DATABASE_SCHEMA_NAME: str = schema
"""str: Name of the schema in database, to which tables being used, belong to.
"""

print("Initializing or future use")

Base = declarative_base()


class DBConnector(object):
    def __init__(self):
        self.database = "inventory"
        pass

    def create_connection(self):
        engine = create_engine(URL.create(
            drivername="postgresql+psycopg2",
            username=DATABASE_USER,
            password=DATABASE_PASSWORD,
            host=DATABASE_HOST,
            port=DATABASE_PORT,
            database=DATABASE_NAME
        ),
            connect_args={'options': '-csearch_path={}'.format(DATABASE_SCHEMA_NAME)}
        )
        """
        Engine: The Engine is the starting point for any SQLAlchemy application.
        It's 'home base' for the actual database and its DBAPI, delivered to the SQLAlchemy application
        through a connection pool and a Dialect, which describes how to talk to a specific kind of database/DBAPI combination.
        """
        return engine

    def __enter__(self):
        self.dbconn = self.create_connection()
        return self.dbconn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dbconn.close()