# runsql.py

from __future__ import print_function

import cx_Oracle

connection = cx_Oracle.connect("system", "oracle", "localhost/xe")

cursor = connection.cursor()
cursor.execute("""
    SELECT 1""")
for v in cursor:
    print("Value:", v)