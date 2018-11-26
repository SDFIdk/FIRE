# fireapi

[![CircleCI](https://circleci.com/gh/Septima/fikspunktsregister.svg?style=svg)](https://circleci.com/gh/Septima/fikspunktsregister) [![Join the chat at https://gitter.im/Septima/fikspunktsregister](https://badges.gitter.im/Septima/fikspunktsregister.svg)](https://gitter.im/Septima/fikspunktsregister?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

API til SDFEs kommende fikspunktsregister.

## API
Work in progress:
```python
from fireapi import FireDb
db = FireDb("fire:fire@localhost:1521/xe")
punkter = db.hent_alle_punkter()
```

For now there are no data in the database so `punkter` is an empty list.

## Local development

## Windows

TODO

## Ubuntu/Debian

Script to setup Oracle drivers can be found [here](misc/debian).

Script to setup Oracle database can be found [here](misc/oracle).

Unit/integration tests are implemented with [pytest](https://pytest.org).

## Docker

Supplies an environment with Oracle Linux 7 and an instance of Oracle XE 12c.

NOTE: Be aware that the image to run Oracle XE 12c is around 8GB so be careful about not running out of space.

Checkout the repository then bring up the containers by running `docker-compose up` with or without detach.

If detached you can now execute commands on Oracle Linux, if not detached you'll need a separate terminal.

If you need a fresh start run `docker-compose down` and remove file `CONTAINER_ALREADY_STARTED_PLACEHOLDER` to make sure setup scripts runs again.

To get an interactive bash prompt:

> docker-compose exec oraclelinux bash

Then active the conda environment with:

> source $HOME/miniconda/bin/activate fikspunktsregister

At this point you should be able to execute `pytest` as follows:

> ORA_USER=fire ORA_PASSWORD=fire ORA_HOST=oracledb pytest
