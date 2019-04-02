#!/bin/sh
# Point to dir containing login.sql for sqlplus to accepts newlines in sql scripts. Sigh
export ORACLE_PATH="`pwd`/misc/oracle"

echo exit | sqlplus64 -S system/oracle@//35.158.182.161:1521/xe @test/fixtures/sql/init.sql
echo exit | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/fikspunkt_forvaltning.sql

# Change OBJECTID column type to allow inserting IDs
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/pre_dataload.sql
# Load data
# EVENTTYPEs IS LOADED in the main DDL echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.EVENTTYPE.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.SAG.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.SAGSINFO.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.SAGSEVENT.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.SAGSEVENTINFO.sql
# echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.SAGSEVENTINFO_HTML.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.SRIDNAMESPACE.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.PUNKTINFOTYPE.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.SRIDTYPE.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.PUNKT.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.PUNKTINFOTYPENAMESPACE.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.PUNKTINFO.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.KOORDINAT.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.GEOMETRIOBJEKT.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.OBSERVATION.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.BEREGNING.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.BEREGNING_KOORDINAT.sql
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/data/FIRE_ADM.BEREGNING_OBSERVATION.sql
# Change OBJECTID column type back to original setting
echo exit |  sqlplus64 -S fire/fire@//35.158.182.161:1521/xe @test/fixtures/sql/post_dataload.sql