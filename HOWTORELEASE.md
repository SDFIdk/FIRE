# HOW TO RELEASE

FIRE følger [Semantisk Versionering](https://semver.org/).

Følg disse skridt i forbindelse med en ny release:

- Opdater versionsnummer i `fire/__init__.py`
- Commit ændring af versionsnummer
- Tag dette commit med versionsnummere: `git tag fire-x.y.z` + `git push --tags`
- Luk milestone på GitHub, opret ny til næste nummer i rækken
- Send mail til kolleger om at der er en ny version klar. Inkluder brugervendt changelog.
- Hvis denne release er første en ny major eller minor release oprettes en ny branch til håndtering af bug fixes: `git checkout -b x.y` + `git push origin x.y`
