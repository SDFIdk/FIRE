export NLS_LANG=.AL32UTF8

if docker container ls | grep fire_oracle > /dev/null ; then
    docker container stop fire_oracle
    docker container rm fire_oracle
fi

docker run --name fire_oracle -d -p 1521:1521 -e ORACLE_PASSWORD=oracle gvenzl/oracle-xe:full
echo "Start 60 sec sleep"
sleep 60
echo "Waky waky"


echo exit | ORACLE_PATH=misc/oracle sqlplus -S system/oracle@//localhost:1521/XEPDB1 @test/ci/init.sql
echo exit | ORACLE_PATH=misc/oracle sqlplus -S fire/fire@//localhost:1521/XEPDB1 @sql/ddl.sql
echo exit | ORACLE_PATH=misc/oracle sqlplus -S fire/fire@//localhost:1521/XEPDB1 @test/sql/testdata.sql

conda deactivate
conda activate fire-dev

python scripts/load_shapefile.py
