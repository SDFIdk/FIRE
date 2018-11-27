#!/bin/sh
CONTAINER_ALREADY_STARTED="CONTAINER_ALREADY_STARTED_PLACEHOLDER"
if [ ! -e $CONTAINER_ALREADY_STARTED ]; then
    touch $CONTAINER_ALREADY_STARTED
    echo "-- First container startup --"
    echo exit | sqlplus64 -S system/oracle@//oracledb:1521/xe @test/fixtures/sql/init.sql
    echo exit | sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/fikspunkt_forvaltning.sql
else
    echo "-- Not first container startup --"
fi
bash