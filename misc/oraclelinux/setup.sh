#!/bin/sh
yum -y install wget
mv /etc/yum.repos.d/public-yum-ol7.repo /etc/yum.repos.d/public-yum-ol7.repo.bak  
wget http://yum.oracle.com/public-yum-ol7.repo -O /etc/yum.repos.d/public-yum-ol7.repo
yum install -y yum-utils
yum-config-manager --enable ol7_developer_EPEL ol7_oracle_instantclient
yum -y install python36 oracle-instantclient18.3-basic.x86_64 oracle-instantclient18.3-sqlplus.x86_64
sh -c "echo /usr/lib/oracle/18.3/client64/lib > /etc/ld.so.conf.d/oracle-instantclient.conf"
ldconfig
alternatives --install /usr/bin/python python /usr/bin/python3.6 60
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py
python -m pip install cx_Oracle pytest --upgrade
