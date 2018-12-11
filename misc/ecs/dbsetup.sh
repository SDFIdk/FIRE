#!/bin/sh
echo exit | sqlplus64 -S system/oracle@//localhost:1521/xe @test/fixtures/sql/init.sql
echo exit | sqlplus64 -S fire/fire@//localhost:1521/xe @test/fixtures/sql/fikspunkt_forvaltning.sql
awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.SAG.sql | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe
awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.SAGSINFO.sql | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe
awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.SAGSEVENT.sql | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe
#awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.SAGSEVENTINFO.sql | sqlplus64 -S fire/fire@//localhost:1521/xe
awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.SRIDNAMESPACE.sql | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe
awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.PUNKTINFOTYPE.sql | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe
awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.SRIDTYPE.sql | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe
awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.PUNKT.sql | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe
awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.PUNKTINFOTYPENAMESPACE.sql | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe
awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.PUNKTINFO.sql | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe
awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.KOORDINAT.sql | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe
awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.GEOMETRIOBJEKT.sql | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe
#awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.OBSERVATIONTYPENAMESPACE.sql | sqlplus64 -S fire/fire@//localhost:1521/xe
#awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.OBSERVATIONTYPE.sql | sqlplus64 -S fire/fire@//localhost:1521/xe
awk -f misc/deobjectidify.awk test/fixtures/sql/data/FIRE_ADM.OBSERVATION.sql | sqlplus64 -S fire/fire@//35.158.182.161:1521/xe
