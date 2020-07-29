export NLS_LANG=.AL32UTF8
docker-compose down
docker-compose up -d
echo "Start 15 sec sleep"
sleep 15
echo "Waky waky"

echo exit | ORACLE_PATH=misc/oracle sqlplus64 -S system/oracle@//localhost:1521/xe @.circleci/init.sql
echo exit | ORACLE_PATH=misc/oracle sqlplus64 -S fire/fire@//localhost:1521/xe @sql/ddl.sql
echo exit | ORACLE_PATH=misc/oracle sqlplus64 -S fire/fire@//localhost:1521/xe @test/sql/testdata.sql

python scripts/load_shapefile.py
