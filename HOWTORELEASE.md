# HOW TO RELEASE

FIRE følger [Semantisk Versionering][]

Følg disse skridt i forbindelse med en ny release:

**Bemærk:** `origin` henviser til kilden `github.com/Kortforsyningen/FIRE`. Din opsætning kan afvige herfra.

* I din egen fork:

  - Synkronisér din version af `master` med `master` på `origin`

  - Opret en ny branch fra `master` og kald den eksempelvis `ny_version`

* Er det *ikke* en patch-release, så prøv om FIREs test-suite (`.github/workflows/tests.yml`) kan køre uden fejl med opdaterede versioner af alle afhængigheder:

  - Fjern alle specifikke versioner i `environment.yml` og `environment-dev.yml`, så de nyeste tilgængelige versioner af alle pakker installeres og anvendes i vores continuous integration-test suite, når koden skubbes til GitHub.

  - Kører alle GitHub actions fejlfrit, kan de installerede versioner aflæses i test-loggen. Skriv disse versioner ind i `environment.yml` og `environment-dev.yml` i formatet `x.y.*`, så det kun er major- og minor-versionerne, der fastholdes i miljøerne.

  - Efter fejlfri kørsel med de nye fastholdte versioner, saml alle ændringerne (med `git rebase`) i et enkelt commit: `git commit -a -m "Opdatér afhængigheder"`

* Opdatér versionsnummer:

  - I samme branch i din fork, opdatér versionsnummeret i `fire/__init__.py` efter ovennævnte regler i [Semantisk Versionering][]

  - Commit ændring af versionsnummer: `git commit -a -m "Opdatér version til x.y.z"`

* I GitHub, opret et pull request til `master` på `origin` og lav en merge fra din branch på din fork.

* I din lokale version fra terminalen:

  - Check `master` ud (hvis det er en patch-release, så check branch `x.y` ud)

  - Synkronisér din version af `master` (eller `x.y`) med den tilsvarende branch på `origin`

  - Tilføj et tag med versionsnummer

    ```sh
    git tag fire-x.y.z
    ```

  - Send tagget direkte til `origin`:

    ```sh
    git push origin tag fire-x.y.z
    ```

* På GitHub luk milestone og opret ny til næste nummer i rækken.

* Send mail til kolleger om at der er en ny version klar. Inkluder brugervendt changelog, inkl. eventuelle ændringer i dataformater etc.

* Hvis denne release er en ny major eller minor release:

  - Opret en maintenance branch til håndtering af bug fixes og skub direkte til `origin`:

    ```sh
    git checkout -b x.y
    git push origin x.y
    ```

  - På GitHub opret ny label `backport x.y` med beskrivelsen `Backport pull requests til x.y branch`

  - Fra din fork på branch `x.y`, ret `.github/workflows/docs.yml` så ``github.ref`` peger på den nye, aktuelle maintenance branch `x.y`.

  - Commit til din fork-destination med beskeden `Gør branch x.y til aktiv dokumentationsbranch`

  - I GitHub, opret et pull request med ændringen og tilføj den nye label.

  - Flet dit PR sammen med `master` på `origin`. Med den påsatte label bliver der automatisk lavet en merge til den tilsvarende maintenance branch `x.y`

* På GitHub opret et nyt release fra listen over releases. Tilføj samme beskrivelse af ændringer, som er sendt ud til brugerne.

[Semantisk Versionering]: https://semver.org/

---
