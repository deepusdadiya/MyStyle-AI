import os

from dotenv import load_dotenv
load_dotenv()

database_name  = os.getenv('POSTGRES_DATABASE')
db_username  = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWD')
db_host = os.getenv('POSTGRES_HOST')
db_port = os.getenv('POSTGRES_PORT')
schema = os.getenv('POSTGRES_SCHEMA')


def ExtractDBDetails(db_type, db_name):
    DBDetails = {}
    if db_type.lower() == 'postgres':
        DBDetails['host'] = db_host
        DBDetails['username'] = db_username
        DBDetails['password'] = db_password
        DBDetails['port'] = db_port
        DBDetails['dbname'] = db_name

    return DBDetails