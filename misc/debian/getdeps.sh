#!/bin/sh
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
wget http://yum.oracle.com/repo/OracleLinux/OL7/oracle/instantclient/x86_64/getPackage/oracle-instantclient18.3-basic-18.3.0.0.0-2.x86_64.rpm
wget http://yum.oracle.com/repo/OracleLinux/OL7/oracle/instantclient/x86_64/getPackage/oracle-instantclient18.3-sqlplus-18.3.0.0.0-2.x86_64.rpm
alien -d oracle-instantclient18.3-basic-18.3.0.0.0-2.x86_64.rpm
alien -d oracle-instantclient18.3-sqlplus-18.3.0.0.0-2.x86_64.rpm
cp ../../environment.yml