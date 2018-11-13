#!/usr/bin/python3

# runsql.py

import sys
import cx_Oracle

user = sys.argv[1]
password = sys.argv[2]
path = sys.argv[3]

sqlfile = open(path,'r')
sql = sqlfile.read()

connection = cx_Oracle.connect(user, password, "localhost/xe")

cursor = connection.cursor()
cursor.execute(sql)
