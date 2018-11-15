# fireapi

[![CircleCI](https://circleci.com/gh/Septima/fikspunktsregister.svg?style=svg)](https://circleci.com/gh/Septima/fikspunktsregister)

API til SDFEs kommende fikspunktsregister.

## Local development

## Windows

TODO

## Ubuntu/Debian

Script to setup Oracle drivers can be found [here](misc/debian).

Unit/integration tests are implemented with [pytest](https://pytest.org).

### Python 3 virtual env

> sudo apt install -y python3-venv
> python3.6 -m venv .venv/fikspunktsregister
> source .venv/fikspunktsregister/bin/activate

## Docker

Supplies an environment with Oracle Linux 7 and an instance of Oracle XE 12c.

NOTE: Be aware that the image to run Oracle XE 12c is around 8GB so be careful about not running out of space.

Checkout the repository then bring up the containers by running `docker-compose up` with or without detach.

If detached you can now execute commands on Oracle Linux, if not detached you'll need a separate terminal.

### Initialize development environment

The environment supplied by `docker-compose.yml` needs additional "one time" setup to include a functional Python 3.6 with proper Oracle drivers and database schema/data to run code/tests against.

These steps only needs to be run once as long as the docker-compose service containers are not deleted on your host.

To setup Oracle Linux 7 with Oracle instant client driver and Python 3.6 run:
> docker-compose exec oraclelinux fikspunktsregister/misc/oraclelinux/setup.sh

To setup db user named fire:
> docker-compose exec oraclelinux sqlplus64 -S system/oracle@//oracledb:1521/xe @test/fixtures/sql/init.sql

To setup db schema (demo data forthcoming):
> docker-compose exec oraclelinux sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/fikspunkt_forvaltning.sql

### Running Python code

After setting up the environment as detailed above `pytest` should be runnable as follows from your host:

> docker-compose exec oraclelinux cd fikspunktsregister && ORA_USER=fire ORA_PASSWORD=fire ORA_HOST=localhost pytest
