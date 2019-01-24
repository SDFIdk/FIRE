# fire-cli

Kommandolinja interface til FIRE.

# Installation

Afhængigheder:
 - [`fireapi`](https://github.com/Septima/fikspunktsregister)
 - `click`

På nuværende tidspunkt er `fire-cli` ikke klar til produktion hvor det kun giver mening at
installere pakken i udviklingsmode:

```
pip install -e.
```

Det anbefales at installere `fire-cli` i et særskilt conda miljø.

# Plugins

Det er muligt at installere plugins i `fire-cli`. Dette gør det muligt at udvikle ny funktionalitet i et separat miljø uden at påvirke hovedapplikationen. Desuden åbner det for
muligheden for at have speciel funktionalitet kun få brugere har behov for, fx et
administrationsmodul.

Plugins laves som selvstående Pyhonpakker, der tilføjer *entry points* til
`firecli.fire_commands`. Click bruges til at håndtere disse entry points. Se
[`fire-stats`](https://github.com/Kortforsyningen/fire-stats) for et fungerende
eksempel.