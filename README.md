# fire-cli

Kommandolinja interface til FIRE.

# Installation

Afhængigheder:
 - [`fireapi`](https://github.com/Septima/fikspunktsregister)
 - `click`

På nuværende tidspunkt er `fire-cli` ikke klar til produktion hvorfor det kun giver mening at
installere pakken i udviklingsmode:

```
pip install -e.
```

Det anbefales at installere `fire-cli` i et særskilt conda miljø.

# Dokumentation

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

## Konfigurationsfil

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

# Udvikling

## Sprog

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

## Kodestil

`fire-cli` formateres med `black`, der sørger for at koden følger best practice for formatering
af Python kode. Inden kode commites bør `black` køres:

```
> fire --line-length 100 --py36 setup.py firecli
```