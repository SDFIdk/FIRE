import sys
import os
import cx_Oracle

user = os.environ.get('ORA_USER')
password = os.environ.get('ORA_PASSWORD')
host = os.environ.get('ORA_HOST')

def hello_world():
    connection = cx_Oracle.connect(user, password, host + "/xe")
    cursor = connection.cursor()
    cursor.execute("SELECT 'Hello world' FROM DUAL")
    return cursor.fetchone()

def test_answer():
    assert hello_world()[0] == "Hello world"