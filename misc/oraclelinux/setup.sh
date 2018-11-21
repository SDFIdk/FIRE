#!/bin/sh
yum -y install wget yum-utils bzip2
mv /etc/yum.repos.d/public-yum-ol7.repo /etc/yum.repos.d/public-yum-ol7.repo.bak  
wget http://yum.oracle.com/public-yum-ol7.repo -O /etc/yum.repos.d/public-yum-ol7.repo
yum-config-manager --enable ol7_developer_EPEL ol7_oracle_instantclient
yum -y install oracle-instantclient18.3-basic.x86_64 oracle-instantclient18.3-sqlplus.x86_64
sh -c "echo /usr/lib/oracle/18.3/client64/lib > /etc/ld.so.conf.d/oracle-instantclient.conf"
ldconfig
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
source $HOME/miniconda/bin/activate
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py
python -m pip install cx_Oracle pytest --upgrade
