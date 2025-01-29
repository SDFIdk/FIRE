# FIRE - FIkspunktRegister

-- Af team Geodætisk Informatik i kontoret [Geografiske Referencer][GRF].

[GRF]: https://sdfi.dk/om-os/organisation/geografiske-referencer


FIRE er SDFIs interne grænseflade til at læse og skrive data i vores
fikspunktregister, ét af vores vigtigste dataarkiver.

Det erstatter REFGEO og indeholder alle de samme informationer, herunder
punktnumre, identer, skitser, koordinater, tidsserier, beskrivelse og
afmærkningstyper. FIRE er imidlertid mere overskueligt opbygget og derfor
nemmere at vedligeholde.

Materialet i dette arkiv indeholder kode og andet materiale, der gør det muligt
for brugerne at opdatere databasen [også kaldet FIRE, eller ved tvetydighed
FIREDB] eller læse oplysninger om punkter, herunder historik, grafik og en
masse andre attributter knyttet til punkterne.

Indhold:

*   En Python-pakke `fire` med API-modul [`fire.api`] til interaktion med den
    bagvedliggende database.

    Med pakken kommer også kommandolinjeprogrammet `fire`, der indeholder en
    række brugbare underapplikationer, såsom `fire info`.

*   Et QGIS-plugin kaldet `flame`, der tilbyder en grafisk brugerflade til
    fikspunktsregisteret og adgang til beregningsprogrammellet i `fire`.

    `flame` er endnu ikke klar til brug, men afventer en nærmere gennemgang.

    Formålet med programmet er let at få vist punkter fra databasen i et
    brugbart regi [QGIS]. Det skal eksempelvis være muligt at fremsøge alle
    punkter inden for en given kommune, et givent distrikt osv.

[GNU Gama]: https://www.gnu.org/software/gama/


## Bruger-installation

FIRE-programmet forudsætter følgende installerede programmer:

*   Python-distributionen MambaForge
*   Git
*   Oracle Instantclient

MambaForge skal installeres efter [SDFIs generelle retningslinjer][pydist].

Git og Oracle Instantclient kan installeres via Software Center [jævnfør FIRE-dokumentationen][Git og Oracle].

[pydist]: https://sdfidk.github.io/SDFIPython/setup.html
[Git og Oracle]: https://sdfidk.github.io/FIRE/installation.html

For at installere FIRE gøres overordnet følgende:

*   Brug Git til at hente dette arkiv.
*   Vælg dén version af FIRE, der skal installeres.
*   Opret et isoleret Python-miljø [af os også kaldet `mamba`- eller
    `conda`-miljø] til installation.
*   Installér de pakker, som FIRE afhænger af.
*   Installér FIRE i Python-miljøet.
*   Efter installationen kan `fire`-pakken og -kommandoen bruges fra alle
    mapper, når blot Python-miljøet er aktiveret.

Installationsskridt:

*   Åbn en terminal.

    Hvis du har fulgt SDFI-vejledningen, er det ligegyldigt hvilken terminal, du
    bruger. MambaForge-Python burde være tilgængelig alle steder, fordi din
    miljø-variabel `%PATH%` inkluderer stien til programmet.

*   Tilgå roden af dit filsystem (her viser vi det for Windows), hvor vi
    opretter mappen til Git-arkivet med FIRE:

    ```sh
    > cd C:\
    C:\>
    ```

    Man kan i princippet selv vælge, hvor koden skal ligge, men vi gør det
    nemmere for os selv og andre ved at vælge samme placering.

*   Med Git kan arkivet hentes, så indholdet ligger i mappen `C:\FIRE`
    (som bliver oprettet automatisk med følgende):

    ```sh
    C:\> git clone https://github.com/SDFIdk/FIRE
    ```

*   Gå ind i mappen:

    ```sh
    C:\> cd C:\FIRE
    ```

*   Vælg nu her, hvilken version, du ønsker at installere [her bruger vi version
    `1.5` som eksempel]:

    Du kan vælge at fastholde versionen ud fra et bestemt Git-tag. her checker
    du en specifik Git-revision ud, som har fået mærkaten [*en* tag]
    `fire-1.5.0`.

    ```sh
    C:\FIRE> git checkout fire-1.5.0
    ```

    Alternativt kan du vælge at følge alle mindre opdateringer til en given
    version [her igen med version `1.5` som eksempel].

    ```sh
    C:\FIRE> git checkout 1.5
    ```

    Her er det grenen [*en* branch], der er navngivet `1.5`, du i så fald
    følger, frem for en specifik Git-revision. Dét betyder, at du fremover kan
    få seneste patch-version [`1.5.1`, `1.5.2`, `1.5.3`, etc.] ved blot at
    skrive følgende:

    ```sh
    C:\FIRE> git pull
    ```

    ... og dernæst opdatere programmerne i mamba-miljøet (se nedenfor).

*   Når du har valgt FIRE-version med én af de ovenstående metoder, kan du nu
    installere alle de pakker, som FIRE afhænger af med følgende kommando:

    ```sh
    C:\FIRE> mamba env create --file environment.yml
    ```

*   Aktivér mamba-miljøet, du nu har oprettet, og installér FIRE:

    ```sh
    C:\FIRE> mamba activate fire
    (fire) C:\FIRE> python -m pip install -e .
    ```

    Husk punktummet til sidst, da det peger på mappen, du befinder dig i
    [`C:\FIRE`].

*   Kontrollér, at opdateringen er gået korrekt med følgende kommando:

    ```sh
    (fire) C:\FIRE> fire --version
    ```

    hvilket gerne skulle returnere

    ```sh
    fire, version 1.5.0
    ```

### Opdatering af FIRE

Ved opdateringer kan du gøre følgende:

*   Gå til appen med Git-arkivet:

    ```sh
    cd C:\FIRE
    ```

*   Hent seneste revisioner, så den nyere version er tilgængelig lokalt på din maskine.

    Skal du blot opdatere patch-version for en given version, eksempelvis `1.5`,
    kan du gøre følgende fra denne branch:

    ```sh
    C:\FIRE> git pull
    ```

    Er du ikke på branchen for version `1.5`, kan du komme det med følgende:

    ```sh
    C:\FIRE> git checkout 1.5
    ```

    ... og dernæst køre `git pull` som ovenfor,

    Skal du skifte til en specifik revision med et Git-tag, eksempelvis
    fire-1.5.2, så skal du være på hoved-branchen [`master` for FIRE-arkivet],
    inden du kører `git fetch` [for at hente koden] og checker revisionen ud.
    Her er kommandoerne:

    ```sh
    C:\FIRE> git checkout master
    C:\FIRE> git fetch
    C:\FIRE> git checkout fire-1.5.2
    ```

    Når du har udført de ønskede kommandoer i dette skridt, har du opdateret FIRE.

    Sidste skridt består i at opdatere programmets afhængigheder, som er installeret i mamba-miljøet.

*   Når du har skiftet til dén git-revision, der svarer til dén version af FIRE,
    du ønsker at benytte [specifik version eller seneste patch-version på
    version-branchen], kan du opdatere dit eksisterende mamba-miljø til FIRE
    med følgende kommando:

    Har du ikke allerede aktiveret mamba-miljøet, skal du først aktivere det:

    ```sh
    C:\FIRE> mamba activate fire
    (fire) C:\FIRE> python -m pip install -e .
    ```

    Nu kan du opdatere det aktive mamba-miljø ud fra miljø-konfigurationen
    `environment.yml`, der passer til dén version af FIRE, du installerede ved
    at checke den ønskede revision/branch ud i ovenstående skridt.

    ```sh
    (fire) C:\FIRE> mamba env update -f environment.yml
    ```

Som under installationen kan du bekræfte, at du kører den ønskede version af FIRE ved at køre `fire --version` i terminalen.

Bemærk, at den officielle dokumentation altid er bygget ud fra seneste patch-version af FIRE.

God fornøjelse!
