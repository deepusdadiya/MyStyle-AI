from sqlalchemy.orm import sessionmaker
from .initializer import DBConnector


class DBConnection(object):

    @classmethod
    def get_connection(cls):
        """Creates return new Singleton database connection"""
        db_conn = DBConnector()
        try:
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_conn.create_connection())
            session = SessionLocal()
            yield session
        finally:
            session.close()

    @classmethod
    def close_connection(cls, new=False):
        """Creates return new Singleton database connection"""
        if cls.connection:
            DBConnector().__exit__()
