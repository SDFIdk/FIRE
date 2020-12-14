"""
Definition af luk-metoder brugt i FireDb klassen. Funktionerne
i dette modul importeres i fire.api.FireDb og tilgås altså som
metoder fra klassen. Dette gøres for at splitte klassen op over
flere filer og gøre det mere overskueligt at finde rundt i.
"""
from fire.api.model import (
    Sag,
    Punkt,
    PunktInformation,
    Koordinat,
    Observation,
    Sagsevent,
    Sagsinfo,
    Beregning,
    EventType,
)


def luk_sag(self, sag: Sag):
    """Sætter en sags status til inaktiv"""
    if not isinstance(sag, Sag):
        raise TypeError("'sag' er ikke en instans af Sag")

    current = sag.sagsinfos[-1]
    new = Sagsinfo(
        aktiv="false",
        journalnummer=current.journalnummer,
        behandler=current.behandler,
        beskrivelse=current.beskrivelse,
        sag=sag,
    )
    self.session.add(new)
    self.session.commit()


def luk_punkt(self, punkt: Punkt, sagsevent: Sagsevent, commit: bool = True):
    """
    Luk et punkt.

    Lukker udover selve punktet også tilhørende geometriobjekt,
    koordinater og punktinformationer. Alle lukkede objekter tilknyttes
    samme sagsevent af typen EventType.PUNKT_NEDLAGT.

    Dette er den ultimative udrensning. BRUG MED OMTANKE!
    """
    if not isinstance(punkt, Punkt):
        raise TypeError("'punkt' er ikke en instans af Punkt")

    sagsevent.eventtype = EventType.PUNKT_NEDLAGT
    self._luk_fikspunkregisterobjekt(punkt, sagsevent, commit=False)
    self._luk_fikspunkregisterobjekt(
        punkt.geometriobjekter[-1], sagsevent, commit=False
    )

    for koordinat in punkt.koordinater:
        self._luk_fikspunkregisterobjekt(koordinat, sagsevent, commit=False)

    for punktinfo in punkt.punktinformationer:
        self._luk_fikspunkregisterobjekt(punktinfo, sagsevent, commit=False)

    for observation in punkt.observationer_fra:
        self._luk_fikspunkregisterobjekt(observation, sagsevent, commit=False)

    for observation in punkt.observationer_til:
        self._luk_fikspunkregisterobjekt(observation, sagsevent, commit=False)

    if commit:
        self.session.commit()


def luk_koordinat(
    self, koordinat: Koordinat, sagsevent: Sagsevent, commit: bool = True
):
    """
    Luk en koordinat.

    Hvis ikke allerede sat, ændres sagseventtypen til EventType.KOORDINAT_NEDLAGT.
    """
    if not isinstance(koordinat, Koordinat):
        raise TypeError("'koordinat' er ikke en instans af Koordinat")

    sagsevent.eventtype = EventType.KOORDINAT_NEDLAGT
    self._luk_fikspunkregisterobjekt(koordinat, sagsevent, commit=commit)


def luk_observation(
    self, observation: Observation, sagsevent: Sagsevent, commit: bool = True
):
    """
    Luk en observation.

    Hvis ikke allerede sat, ændres sagseventtypen til EventType.OBSERVATION_NEDLAGT.
    """
    if not isinstance(observation, Observation):
        raise TypeError("'observation' er ikk en instans af Observation")

    sagsevent.eventtype = EventType.OBSERVATION_NEDLAGT
    self._luk_fikspunkregisterobjekt(observation, sagsevent, commit=commit)


def luk_punktinfo(
    self, punktinfo: PunktInformation, sagsevent: Sagsevent, commit: bool = True
):
    """
    Luk en punktinformation.

    Hvis ikke allerede sat, ændres sagseventtypen til EventType.PUNKTINFO_FJERNET.
    """
    if not isinstance(punktinfo, PunktInformation):
        raise TypeError("'punktinfo' er ikke en instans af PunktInformation")

    sagsevent.eventtype = EventType.PUNKTINFO_FJERNET
    self._luk_fikspunkregisterobjekt(punktinfo, sagsevent, commit=commit)


def luk_beregning(
    self, beregning: Beregning, sagsevent: Sagsevent, commit: bool = True
):
    """
    Luk en beregning.

    Lukker alle koordinater der er tilknyttet beregningen.
    Hvis ikke allerede sat, ændres sagseventtypen til EventType.KOORDINAT_NEDLAGT.
    """
    if not isinstance(beregning, Beregning):
        raise TypeError("'beregning' er ikke en instans af Beregning")

    sagsevent.eventtype = EventType.KOORDINAT_NEDLAGT
    for koordinat in beregning.koordinater:
        self._luk_fikspunkregisterobjekt(koordinat, sagsevent, commit=False)
    self._luk_fikspunkregisterobjekt(beregning, sagsevent, commit=commit)
