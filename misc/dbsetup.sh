#!/bin/sh
sqlplus64 -S system/oracle@//localhost:1521/xe @test/fixtures/sql/init.sql
sqlplus64 -S fire/fire@//localhost:1521/xe @test/fixtures/sql/fikspunkt_forvaltning.sql
