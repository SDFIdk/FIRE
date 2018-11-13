#!/usr/bin/python3

# runsql.py

import sys
import cx_Oracle

sqlfile = open(sys.argv[1],'r')
sql = sqlfile.read()

connection = cx_Oracle.connect("system", "oracle", "localhost/xe")

cursor = connection.cursor()
cursor.execute(sql)
for v in cursor:
    print("Value:", v)