class DBQueries(object):
    connection = None

    @classmethod
    def execute_query(cls, session):
        """execute query on singleton db connection"""

        try:
            # cursor = connection.cursor()
            cursor = session.execute("CREATE TABLE test_hcmp.table_name(\
                id INT PRIMARY KEY AUTO INCREMENT,\
                name CHAR(50),\
                code INT,\
                desc CHAR(100);")
        except Exception as e:
            print("Exception guys : ",e)
        # except pyodbc.ProgrammingError:
            connection = cls.get_connection(new=True)  # Create new connection
            cursor = connection.cursor()