# Nulstil testdatabase.
#
# Kald fra roden af repository:
#
# fire$ ./scripts/reset-test-db.sh
#
# Køres scriptet uden argumenter forbindes til database på localhost.
# Tilføj adresse på databasen for at nulstille remote, fx:
#
# fire$ ./scripts/reset-test-db.sh 192.168.0.81

export NLS_LANG=.AL32UTF8

HOSTNAME=${1:-localhost}

echo exit | ORACLE_PATH=misc/oracle sqlplus -S fire/fire@//"$HOSTNAME":1521/XEPDB1 @sql/sweep_db.sql

echo exit | ORACLE_PATH=misc/oracle sqlplus -S fire/fire@//"$HOSTNAME":1521/XEPDB1 @sql/ddl.sql
echo exit | ORACLE_PATH=misc/oracle sqlplus -S fire/fire@//"$HOSTNAME":1521/XEPDB1 @test/sql/testdata.sql

python scripts/load_shapefile.py