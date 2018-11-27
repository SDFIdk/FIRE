FROM ubuntu:18.04
COPY oracle-instantclient18.3-basic_18.3.0.0.0-3_amd64.deb /
COPY oracle-instantclient18.3-sqlplus_18.3.0.0.0-3_amd64.deb /
COPY Miniconda3-latest-Linux-x86_64.sh /
RUN apt-get update && apt-get -y install libaio1
RUN dpkg -i oracle-instantclient18.3-basic_18.3.0.0.0-3_amd64.deb
RUN dpkg -i oracle-instantclient18.3-sqlplus_18.3.0.0.0-3_amd64.deb
RUN sh -c "echo /usr/lib/oracle/18.3/client64/lib > /etc/ld.so.conf.d/oracle-instantclient.conf"
RUN ldconfig
COPY environment.yml /
RUN /bin/bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc
RUN /opt/conda/bin/conda env create -f environment.yml
CMD [ "/bin/bash" ]