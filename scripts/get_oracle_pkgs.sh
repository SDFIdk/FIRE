#!/bin/sh

wget -nv https://yum.oracle.com/repo/OracleLinux/OL7/oracle/instantclient/x86_64/getPackage/oracle-instantclient19.13-basic-19.13.0.0.0-1.x86_64.rpm
wget -nv https://yum.oracle.com/repo/OracleLinux/OL7/oracle/instantclient/x86_64/getPackage/oracle-instantclient19.13-sqlplus-19.13.0.0.0-1.x86_64.rpm

sudo alien -d oracle-instantclient19.13-basic-19.13.0.0.0-1.x86_64.rpm
sudo alien -d oracle-instantclient19.13-sqlplus-19.13.0.0.0-1.x86_64.rpm