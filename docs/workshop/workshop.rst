.. _workshop:

Workshop
=======================

Indledning
--------

Velkommen til arbejdet med FIRE! Vi vil starte med at give en gennemgang af hvad man kan med det nuværende setup, og løbende vil der komme mere på.


Generelle kommandoer i linjen 
------------


MTL
---------------------

Revision
++++++++++++++++

Opdatering af database
++++++++++++++++++++++

Beregning
++++++++++++++++

Visualisering i QGIS
------------------------



Oracle Instantclient
++++++++++++++++++++

Download "Basic package" fra denne side:
https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html

Pak den downloadede zip-fil ud i ``C:\oracle\``. Det skulle gerne resultere i en
mappe på placeringen ``C:\oracle\Instantclient_19_6`` som indeholder en masse
``*.dll``-filer og lignende.

Herefter skal miløvariablen ``%PATH%`` tilpasses. I Start-menuens søgefelt skrives
"miljøvariable", hvilken gerne skulle resultere i et enkelt resultat: "Rediger
miljøvariabler for din konto". Åben dialogboksen.

.. figure:: ./images/envvar.png
   :align: center
   :alt:   Rediger miljøvariable

   Rediger miljøvariable

I miljøvariabeldialogboksen skal variablen "Path" ændres.

.. figure:: ./images/path1.png
   :align: center
   :alt:   Rediger Path

   Rediger Path

Herefter tilføjes en ny sti til "Path" ved at trykke på "Ny":

.. figure:: ./images/path1.png
   :align: center
   :alt:   Tilføj Instantclient til Path

   Tilføj Instantclient til Path

Indsæt stien hvor du har gemt Oracle Instantclient, eksempelvis
``C:\oracle\instantclient_19_6`` (bemærk at versionsnummeret kan være
anderledes hos dig). Klik "OK" i de to vinduer og fortsæt til næste
afsnit.

Conda
+++++

Download og kør `Miniconda3-latest-Windows-x86_64.exe
<https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe>`_.
Installationen er forholdsvis triviel, og man kan trykke "next" i alle trin og
slutte af med "install". Det indbefatter at Conda kun installeres til den
lokale bruger ("just me") og at ingen af de avancerede muligheder slås til.

Når Conda er installeret kan du nu i start menuen finde "Anaconda Prompt
(miniconda3)" Alle efterfølgende kommandoer i denne installationsvejledning skal
afvikles i denne terminal. Det anbefales at lave en genvej til "Anaconda Prompt"
i Windows' proceslinjen (åben programmet, højreklik på ikonet i proceslinjen,
vælg "fastgør til proceslinje").

FIRE
+++++++++++++++++

.. note::

    Det er for nuværende mere kompliceret at installere koden end det bliver i fremtiden.
    Hav tålmodighed, der er smartere løsninger på vej!

Åben "Anaconda Prompt". Start med at lave en ny mappe til FIRE koden og download
den med git::

    > mkdir C:\fire
    > cd C:\fire
    > git clone https://github.com/Kortforsyningen/FIRE.git

Initialiser et "conda environment" til FIRE::

    > cd FIRE
    > conda env create --file environment.yml -y

Gør som ``conda`` siger og aktiver dit nye "fire environment"::

    > conda activate fire

Installer FIRE::

    > pip install -e .


Konfigurationsfil
.................

For at FIRE kan forbinde til databasen er det nødvendigt at tilføje en
konfigurationsfil til systemet hvori adgangsinformation til databasen er
registreret. Konfigurationsfilen er en INI fil, der er struktureret på følgende
måde

.. code-block:: ini

    [connection]
    password = <adgangskode>
    username = <brugernavn>
    hostname = <netværksadresse>
    database = <databasenavn>
    service = <servicenavn>

.. note::

    Tag fat i en kollega for at få oplyst brugernavn, adgangskode osv.

Under Windows placeres konfigurationsfilen i en af følgende stier::

    C:\Users\<brugernavn>\fire.ini
    C:\Users\Default\AppData\Local\fire\fire.ini

og på et UNIX-baseret system placeres filen et af følgende steder::

    home/<brugernavn>/fire.ini
    home/<brugernavn>/.fire.ini
    /etc/fire.ini


Flame - QGIS plugin
+++++++++++++++++++

.. note::

    Installationsvejledning til Flame afventer beslutninger om deployment
    procedurer.
