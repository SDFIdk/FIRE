# fireapi

[![CircleCI](https://circleci.com/gh/Septima/fikspunktsregister.svg?style=svg)](https://circleci.com/gh/Septima/fikspunktsregister)

API til SDFEs kommende fikspunktsregister.

## Local development

Requires Docker and Docker Compose. Supplies an environment with Oracle Linux 7 and an instance of Oracle XE 12c.

Checkout the repository then prep the environment by running `docker-compose up'.

In a separate terminal you can now execute commands on Oracle Linux. (optionally you could detach `docker-compose up` and reuse that terminal)

## Initialize development environment

The environment supplied by `docker-compose.yml` needs additional setup to include a functional Python 3.6 with proper Oracle drivers and database schema/data to run code/tests against.

These steps only needs to be run once as long as the docker-compose service containers are not deleted on your host.

To setup Oracle Linux 7 with Oracle instant client driver and Python 3.6 run:
> docker-compose exec oraclelinux fikspunktsregister/test/setup.sh

To setup db user named fire:
> docker-compose exec oraclelinux sqlplus64 -S system/oracle@//oracledb:1521/xe @test/sql/init.sql

To setup db schema (demo data forthcoming):
> docker-compose exec oraclelinux sqlplus64 -S fire/fire@//oracledb:1521/xe @test/sql/20181023.v0.4.FikspunktForvaltning.sql

## Running Python code

After setting up the environment as detailed above, Python code accessing the Oracle DB can now be run from your host:

> docker-compose exec oraclelinux python fikspunktsregister/test/runsql.py system oracle fikspunktsregister/test/sql/helloworld.sql
