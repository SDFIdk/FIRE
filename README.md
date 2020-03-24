# fireapi

[![CircleCI](https://circleci.com/gh/Septima/fikspunktsregister.svg?style=svg)](https://circleci.com/gh/Septima/fikspunktsregister) [![Join the chat at https://gitter.im/Septima/fikspunktsregister](https://badges.gitter.im/Septima/fikspunktsregister.svg)](https://gitter.im/Septima/fikspunktsregister?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

API til SDFEs kommende fikspunktsregister.

[UML diagram](./misc/fireapi-uml.png)
![fireapi UML](./misc/fireapi-uml.png)

## API
Work in progress:
```python
from fireapi import FireDb
db = FireDb("fire:fire@localhost:1521/xe")
punkter = db.hent_alle_punkter()
```

For now there are no data in the database so `punkter` is an empty list.


## Local development
Install and activate development environment (called `fiskpunktsregister-dev`) and then run tests. Note that almost all
tests require an active database.
```bash
conda env update -f environment-dev.yml
conda activate fikspunktsregister-dev
pytest
```

### Tests
Unit/integration tests are implemented with [pytest](https://pytest.org). Tests are run like described above.

Most tests require an active database. Connection parameters used by the tests are set by the following code
```python
user = os.environ.get("ORA_USER") or "fire"
password = os.environ.get("ORA_PASSWORD") or "fire"
host = os.environ.get("ORA_HOST") or "localhost"
port = os.environ.get("ORA_PORT") or "1521"
db = os.environ.get("ORA_db") or "xe"
```

 With an active conda environment tests can be run against a custom database on *nix by
```bash
export ORA_USER=custom_username
export ORA_PASSWORD=custom_password
export ORA_HOST=custom_host
export ORA_PORT=1522
export ORA_DB=custom_databasename
pytest
```
and on windows by
```bash
ORA_USER=custom_username
ORA_PASSWORD=custom_password
ORA_HOST=custom_host
ORA_PORT=1522
ORA_DB=custom_databasename
pytest
```
See section on [Docker](#Docker) for an easy way to create a local database.

### UML
A [UML diagram](./misc/fireapi-uml.png) of the `fireapi` datamodel can be exported using the script [export-uml.py](./misc/export-uml.py).

Run it in the `fikspunktsregister-dev` environment using
```bash
cd misc
python export-uml.py
```
It isn't beautiful but it is useful.

## Windows

TODO

## Ubuntu/Debian

Script to setup Oracle drivers can be found [here](misc/debian).

Script to setup Oracle database can be found [here](misc/oracle).

## Docker

Supplies an environment with Ubuntu 18.04 LTS + dependencies and an instance of Oracle XE 12c.

NOTE: Be aware that the image to run Oracle XE 12c is around 8GB so be careful about not running out of space.

Checkout the repository then bring up the containers by running `docker-compose up`.

To get an interactive bash prompt:

> docker-compose exec devenv bash

Initialize the database schema with:

> echo exit | sqlplus64 -S system/oracle@//oracledb:1521/xe @test/fixtures/sql/init.sql

> echo exit | sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/fikspunkt_forvaltning.sql

Then load data
```bash
# Point to dir containing login.sql for sqlplus to accepts newlines in sql scripts. Sigh
export ORACLE_PATH="`pwd`/misc/oracle"

# Change OBJECTID column type to allow inserting IDs
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/pre_dataload.sql
# Load data
# EVENTTYPEs IS LOADED in the main DDL echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.EVENTTYPE.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.SAG.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.SAGSINFO.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.SAGSEVENT.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.SAGSEVENTINFO.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.SAGSEVENTINFO_HTML.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.SRIDNAMESPACE.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.PUNKTINFOTYPE.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.SRIDTYPE.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.PUNKT.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.PUNKTINFOTYPENAMESPACE.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.PUNKTINFO.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.KOORDINAT.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.GEOMETRIOBJEKT.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.OBSERVATION.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.BEREGNING.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.BEREGNING_KOORDINAT.sql
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/data/FIRE_ADM.BEREGNING_OBSERVATION.sql
# Change OBJECTID column type back to original setting
echo exit |  sqlplus64 -S fire/fire@//oracledb:1521/xe @test/fixtures/sql/post_dataload.sql
```

Activate the conda environment with:

> source /opt/conda/bin/activate fikspunktsregister

At this point you should be able to execute `pytest` as follows:

> ORA_USER=fire ORA_PASSWORD=fire ORA_HOST=oracledb pytest

## Docs
Docs can be compiled locally using sphinx:

```
sphinx-build -b html ./docs ./docs/_build
```
This will build html documents in the directory [./docs/_build](./docs/_build).

Whenever modules have been added or deleted the api docs (files residing in docs/api) need to be updated. This can be done by

```
cd docs
sphinx-apidoc -e -o api ../fireapi
```


# fire-cli

Kommandolinje interface til FIRE.

## Installation

Afhængigheder:
 - `click`

På nuværende tidspunkt er `fire-cli` ikke klar til produktion hvorfor det kun giver mening at
installere pakken i udviklingsmode:

```
pip install -e.
```

Det anbefales at installere `fire-cli` i et særskilt conda miljø.

## Dokumentation

`fire-cli` installerer kommandolinjeapplikationen `fire`. `fire` er indgangen til en række
kommandoer, der igen gør en række underkommandoer tilgængelige. Kald til `fire` følger mønsteret:

```
fire <kommando> <underkommda> <argumenter>
```

Det er hensigten at `fire` i så høj grad som muligt er selv-dokumenterende. Dokumentationen tilgås
ved hjælp af valgmuligheden `--help` efterfulgt af en kommando eller underkommando. En oversigt over
tilgængelige kommandoer fås ved at køre `--help` på `fire`:

```
> fire --help
Usage: fire [OPTIONS] COMMAND [ARGS]...

  🔥 Kommandolinje adgang til FIRE.

Options:
  --help     Vis denne hjælp tekst
  --version  Vis versionsnummer

Commands:
  info  Information om objekter i FIRE
  stat  Statistik plugin til FIRE.
```

Bemærk at de tilgængelige kommandoer kan variere fra installation til installation, da det er muligt
at installere plugins i `fire` som tilføjer yderligere funktionalitet.

### Konfigurationsfil

For at `fire-cli` kan forbinde til databasen er det nødvendigt at tilføje en konfigurationsfil til
systemet hvori adgangsinformation til databasen er registreret. Konfigurationsfilen er en JSON fil,
der er struktureret på følgende måde:
```
{
    "connection":
    {
        "password": "<adgangskode>",
        "username": "<brugernavn>",
        "hostname": "<netværksadresse>",
        "database": "<databasenavn>",
        "service": "<servicenavn>"
    }
}
```

Under Windows placeres konfigurationsfilen i en af følgende stier:

```
    C:\Users\<brugernavn>\fire_settings.json
    C:\Users\Default\AppData\Local\\fire\fire_settings.json
```

og på et UNIX-baseret system placeres filen et af følgende steder:

```
    home/<brugernavn>/fire_settings.json
    home/<brugernavn>/.fire_settings.json
    /etc/fire_settings.json
```

## Udvikling

### Sprog

`fire-cli` taler dansk til brugeren. Dokumentation skrives ligeledes på dansk. Det er tilladt
at skrive kommentarer, funktions- og variabelnavne på engelsk. git commits bør så vidt muligt
skrives på dansk.

## Plugins

Det er muligt at installere plugins i `fire-cli`. Dette gør det muligt at udvikle ny funktionalitet i et separat miljø uden at påvirke hovedapplikationen. Desuden åbner det for
muligheden for at have speciel funktionalitet kun få brugere har behov for, fx et
administrationsmodul.

Plugins laves som selvstående Pythonpakker, der tilføjer *entry points* til
`firecli.fire_commands`. Click bruges til at håndtere disse entry points. Se
[`fire-stats`](https://github.com/Kortforsyningen/fire-stats) for et fungerende
eksempel.

### Kodestil

`fire-cli` formateres med `black`, der sørger for at koden følger best practice for formatering
af Python kode. Inden kode commites bør `black` køres:

```
> black --line-length 100 --py36 setup.py firecli
```


# fire-gama
FireDb Gama import/export plugin til fire-cli (https://github.com/Kortforsyningen/fire-cli)

### Forudsætninger
Python 3+
Installér https://github.com/Septima/fikspunktsregister
Installér https://github.com/Kortforsyningen/fire-cli
installér click (pip install click)

## Installér
Installér https://github.com/Septima/fire-gama

## Brug

fire gama KOMMANDO [PARAMETRE]

```
fire gama --help

Kommandoer:
  read   Indlæs en gama output fil (fire gama read --help)
  write  Skab en gama input file fra fire (fire gama write --help)
```
### parametre til write

```
fire gama write --help

  -o, --out FILENAME             Navn på gama input, der skal skabes (.xml) [default: output.xml]
  -g, --geometri TEXT            wkt. Anvendes som geometri i udvælgelsen af observationer
  -gf, --geometrifil FILENAME    Fil, som indeholder en wkt-streng. Anvendes som geometri i udvælgelsen af observationer
  -b, --buffer INTEGER           Den buffer omkring den givne geometri som skal bruges i udvælgelsen af observationer [default: 0]
  -df, --fra DATE                Fra-dato, som bruges i udvælgelsen af observationer
  -dt, --til DATE                Til-dato, som bruges i udvælgelsen af observationer
  -f, --fixpunkter TEXT          Komma-separeret liste af punkt-id'er, som skal fastholdes
  -ff, --fixpunkterfil FILENAME  Fil, som indeholder komma-separeret liste af punkt-id'er, som skal fastholdes
  -pf, --parameterfil FILENAME   Fil, som indeholder netværks-parametre og -attributter  [required]
  --help                         Show this message and exit.
```
#### format på parameterfil

Parameter-filen er en .ini-fil med følgende indhold:
```
[network-attributes]
axes-xy=en
angles=left-handed
epoch=0.0

[network-parameters]
algorithm=gso
angles=400
conf-pr=0.95
cov-band=0
ellipsoid=grs80
latitude=55.7
sigma-act=apriori
sigma-apr=1.0
tol-abs=1000.0
update-constrained-coordinates=no

[points-observations-attributes]
```

### Database-forbindelse

Læs venligst https://github.com/Kortforsyningen/fire-cli#konfigurationsfil


# flame
QGIS plugin til FIRE database

## Installation
Installér afhængigheder

### QGIS from OSGEO4W
Åbn OSGEO4W console med administrator-rettigheder.

```
C:\> py3_env
C:\> pip3 install https://github.com/Kortforsyningen/fikspunktsregister/zipball/master
```

### Download og installér plugin
* Download seneste flame.zip fra releases
* I QGIS: Vælg menuen _plugins->Administrér og installér plugins_.
* Klik på _Installér fra ZIP_
