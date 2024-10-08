"""
Funktionalitet til at lukke diverse FIRE objekter

"""
from fire.api.firedb.base import FireDbBase
from fire.api.model import (
    Sag,
    Punkt,
    PunktSamling,
    PunktInformation,
    Koordinat,
    Tidsserie,
    Observation,
    Grafik,
    Sagsevent,
    Sagsinfo,
    Beregning,
    EventType,
)


class FireDbLuk(FireDbBase):
    def luk_sag(self, sag: Sag, commit: bool = True):
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
        if commit:
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
        self._luk_fikspunktregisterobjekt(punkt, sagsevent, commit=False)

        objekter_til_lukning = (
            punkt.geometriobjekter
            + punkt.koordinater
            + punkt.punktinformationer
            + punkt.observationer_fra
            + punkt.observationer_til
            + punkt.grafikker
        )

        for objekt in objekter_til_lukning:
            # Vi lukker kun objekter som ikke er lukkede i forvejen. Ellers vil vi komme
            # til at overskrive ændringshistorikken (registrering- og sagseventtil).
            if objekt.registreringtil is not None:
                continue
            self._luk_fikspunktregisterobjekt(objekt, sagsevent, commit=False)

        if commit:
            self.session.commit()

    def luk_punktsamling(
        self, punktsamling: PunktSamling, sagsevent: Sagsevent, commit: bool = True
    ):
        """
        Luk en punktsamling.

        Hvis ikke allerede sat, ændres sagseventtypen til EventType.PUNKTGRUPPE_NEDLAGT.
        """
        if not isinstance(punktsamling, PunktSamling):
            raise TypeError("'punktsamling' er ikke en instans af PunktSamling")

        sagsevent.eventtype = EventType.PUNKTGRUPPE_NEDLAGT
        self._luk_fikspunktregisterobjekt(punktsamling, sagsevent, commit=commit)

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
        self._luk_fikspunktregisterobjekt(koordinat, sagsevent, commit=commit)

    def luk_tidsserie(
        self, tidsserie: Tidsserie, sagsevent: Sagsevent, commit: bool = True
    ):
        """
        Luk en tidsserie.

        Hvis ikke allerede sat, ændres sagseventtypen til EventType.TIDSSERIE_NEDLAGT.
        """
        if not isinstance(tidsserie, Tidsserie):
            raise TypeError("'tidsserie' er ikke en instans af Tidsserie")

        sagsevent.eventtype = EventType.TIDSSERIE_NEDLAGT
        self._luk_fikspunktregisterobjekt(tidsserie, sagsevent, commit=commit)

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
        self._luk_fikspunktregisterobjekt(observation, sagsevent, commit=commit)

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
        self._luk_fikspunktregisterobjekt(punktinfo, sagsevent, commit=commit)

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
            self._luk_fikspunktregisterobjekt(koordinat, sagsevent, commit=False)
        self._luk_fikspunktregisterobjekt(beregning, sagsevent, commit=commit)

    def luk_grafik(self, grafik: Grafik, sagsevent: Sagsevent, commit: bool = True):
        """Luk et Grafik objekt."""
        if not isinstance(grafik, Grafik):
            raise TypeError("'grafik' er ikke en instans af Grafik")

        sagsevent.eventtype = EventType.GRAFIK_NEDLAGT
        self._luk_fikspunktregisterobjekt(grafik, sagsevent, commit=commit)
