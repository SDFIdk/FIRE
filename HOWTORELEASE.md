# HOW TO RELEASE

FIRE følger [Semantisk Versionering][]

Følg disse skridt i forbindelse med en ny release:

**Bemærk:** `origin` henviser til kilden `github.com/Kortforsyningen/FIRE`. Din opsætning kan afvige herfra.

* Hvis der *ikke* er tale om en patch-release:

  - Lav en branch i din egen fork og test FIRE med opdaterede versioner af alle afhængigheder, så `environment.yml` og `environment-dev.yml` reflekterer "seneste anvendelige version" af hver afhængighed.

    -   Saml ændringerne i et enkelt commit: `git commit -a -m "Opdatér afhængigheder"`

* Opdatér versionsnummer:

  - I `fire/__init__.py` ret til efter ovennævnte regler i [Semantisk Versionering][]

  - Commit ændring af versionsnummer: `git commit -a -m "Opdatér version til x.y"`

* Opret et pull request til `master` på `origin` og lav en merge fra din branch på din fork.

* Tilføj tag med versionsnummer og send direkte til `master` på `origin`:

  ```sh
  git tag fire-x.y.z
  git push --tags origin/master
  ```

* På GitHub luk milestone og opret ny til næste nummer i rækken.

* Send mail til kolleger om at der er en ny version klar. Inkluder brugervendt changelog, inkl. eventuelle ændringer i dataformater etc.

* Hvis denne release er en ny major eller minor release:

  - Opret en maintenance branch til håndtering af bug fixes og skub direkte til `origin`:

    ```sh
    git checkout -b x.y
    git push origin x.y
    ```

  - I `.github/workflows/docs.yml` ret ``github.ref`` til den aktuelle maintenance branch `x.y`.

  - Commit til `origin` med beskeden (tilpas `x.y`) `Omdirigér x.y branch til aktiv dokumentationsbranch`

[Semantisk Versionering]: https://semver.org/
