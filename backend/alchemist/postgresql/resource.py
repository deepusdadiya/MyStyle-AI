from sqlalchemy.orm import sessionmaker
from .initializer import DBConnector
from contextlib import contextmanager


class DBConnection(object):

    @classmethod
    @contextmanager
    def get_connection(cls):
        """Creates and returns a context-managed DB session."""
        db_conn = DBConnector()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_conn.create_connection())
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    @classmethod
    def close_connection(cls, new=False):
        """Creates return new Singleton database connection"""
        if cls.connection:
            DBConnector().__exit__()
