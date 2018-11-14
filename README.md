# fireapi

[![CircleCI](https://circleci.com/gh/Septima/fikspunktsregister.svg?style=svg)](https://circleci.com/gh/Septima/fikspunktsregister)

API til SDFEs kommende fikspunktsregister.

## Local development

Requires Docker and Docker Compose. Supplies an environment with Oracle Linux 7 and an instance of Oracle XE 12c.

Checkout the repository then prep the environment by running `docker-compose`.

In a separate terminal you can now execute commands on Oracle Linux.

To setup Oracle Linux with instant client driver and Python 36 run:
> docker-compose exec oraclelinux fikspunktsregister/test/setup.sh

The above only needs to be run once as long as the docker-compose service containers are not deleted.

Python code accessing the Oracle DB can be run from your host with fx.
> docker-compose exec oraclelinux python fikspunktsregister/test/runsql.py system oracle fikspunktsregister/test/sql/helloworld.sql

