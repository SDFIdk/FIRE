prompt run login.sql
show sqlterminator
show sqlblanklines
set sqlblanklines on
set sqlterminator ';'
set linesize 32000
column title format a20 truncated
column summary format a40 word_wrapped
show sqlterminator
show sqlblanklines
WHENEVER SQLERROR EXIT SQL.SQLCODE
prompt ready login.sql
set echo on
