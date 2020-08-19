.. _for_udviklere:

Udviklingsguide
=======================

Denne side indeholder alverdens information der er relevant for dem der arbejder
på kildekoden bag FIRE.

Opsætning
----------

.. note::

    Alt herunder forudsætter at det foretages i en Conda terminal og at
    Oracle Instantclient er installeret. Se
    :ref:`installationsvejledningen <installation>` for mere om Conda og
    Oracle Instantclient.

Start med at clone git repositoriet::

    > git clone https://github.com/Kortforsyningen/FIRE.git

Et godt udviklingsmiljø at tage udgangspunkt i er `fire-dev.yaml`, som nemt
installeres med Conda. Fra fire git-repositoriet køres::

    > conda env create --file environment-dev.yml
    > conda activate fire-dev

Herefter burde alle de essentielle programmer og biblioteker være til rådighed.

Installer en udviklingsversion af fire med::

    > pip install -e .

Test-suiten køres med::

    > pytest

.. warning::

    Test-suiten kræver adgang til en Oracle database hvor DDL og testdata er
    indlæst. Normalvis er det ikke filfældet på SIT arbejdsstationer hvorfor
    tests som udgangspunkt ikke kan afvikles lokalt. Test-suiten kører automatisk
    på pull requests mod https://github.com/Kortforsyningen/FIRE.

    Se :ref:`testlokalt` for mere om hvordan et testmiljø kan sættes op lokalt.

For at test-suiten kører korrekt skal der i `fire.ini` indsættes en `[test_connection]`
sektion::

    [test_connection]
    password = <adgangskode>
    username = <brugernavn>
    hostname = <netværksadresse>
    database = <databasenavn>
    service = <servicenavn>

På maskiner der både arbejder op mod produktions- og testdatabase er det vigtigt at
`[test_connection]` er forskellig fra `[connection]`, da det ellers risikeres at der
indsættes ugyldigt data i produktionsdatabasen.

Kodestil
--------

`fire` kommandoen og QGIS pluginen Flame taler dansk til brugeren. Dokumentation
skrives ligeledes på dansk. Det er tilladt at skrive kommentarer, funktions- og
variabelnavne på engelsk. git commits bør så vidt muligt skrives på dansk.

Al kode i fire repositoriet skal køres gennem ``black`` inden det committes.
Dette gøres for at skabe et ensartet udtryk på tværs af hele kodebasen. Desuden
har black den bivirking at forstyrrende, overflødige ændringer typisk forsvinder
fra diffs mellem to commits, hvilket gør det væsentligt nemmere at lave review
af kodeændringer.

Kør ``black`` med::

    > black .

Hvis ikke ``black`` er kørt inden kode pushes til GitHub vil CI tests fejle.


Dokumentation
-------------

HTML dokumentation kan genereres lokalt ved hjælp af følgende kommando::

    sphinx-build -b html ./docs ./docs/_build

hvorefter dokumentationen vil være at finde i ``docs/_build``.

Det er muligt at Sphinx ikke kan finde `graphviz` (fx relevant på :ref:`datamodel`), i så
fald kan placeringen til denne angives som følger::

    sphinx-build -b html -D graphviz_dot=C:\Users\<USERNAME>\AppData\Local\Continuum\miniconda3\envs\fire-dev\Library\bin\graphviz\dot.exe ./docs ./docs/_build

Når der tilføjes eller fjernes moduler til API koden skal dokumentationen
opdaters (filer i ``docs/api``). Dette kan gøres med::

    sphinx-apidoc -E -d 3 -o docs\api fire


GitHub og Continuous Integration
---------------------------------

Fire repositoriet håndteres på GitHub, hvor der er sat en række Continous
Integration (CI) services op. Disse benyttes blandt andet til at afvikle test
suiten og til at generere HTML dokumentation efter hvert commit.

GitHub er konfigureret sådan at man ikke kan lave ``git push`` direkte til ``master``.
For at inkludere kode i ``master`` kræves det at man laver et pull request med mindst
et godkendt review fra en kollega, samt at alle CI tests gennemføres successfuldt.

QGIS Plugin
------------

Flame pakkes til release ved brug af ``pb_tool``::

    > cd flame
    > pb_tool zip

hvorefter filen ``flame_plugin.zip`` placeres i ``flame/zip``.

Mere om ``pb_tool`` her https://github.com/g-sherman/plugin_build_tool.


.. _testlokalt:

Lokalt testmiljø
----------------

Forudsat du har Docker og nogle Oracle-værktøjer (instaclient og SQLplus) installeret
er det muligt at sætte en lokal testdatbase op. Fremgangsmåden er nogenlunde som følger.
Først startes en Oracle-database med ``docker-compose``. Fra roden af repositoryet
køres::

    > docker-compose up

Først gang kommandoen køres downloades en række Docker images. Det tager sin tid, så
vær tålmodig. Når databasen er færdig installeret og startet op får du besked herom.

Start en ny terminal op og initialiser databasen med brugerrettigheder, DDL og
testdata::

    ORACLE_PATH=misc/oracle sqlplus -S system/oracle@//localhost:1521/xe @.circleci/init.sql
    ORACLE_PATH=misc/oracle sqlplus -S fire/fire@//localhost:1521/xe @sql/ddl.sql
    ORACLE_PATH=misc/oracle sqlplus -S fire/fire@//localhost:1521/xe @test/sql/testdata.sql

.. note::

    Databasen skal initialiseres hver gang den startes op. Det anbefales at lave et
    script der automatiserer processen.

Kopier opsætningsfilen ``.circleci/fire_settings.json`` til din :envvar:`HOME`-mappe.
Herefter burde det være muligt at køre test-suiten.


