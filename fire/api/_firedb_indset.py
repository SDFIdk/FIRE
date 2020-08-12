"""
Definition af indset-metoder brugt i FireDb klassen. Funktionerne
i dette modul importeres i fire.api.FireDb og tilgås altså som
metoder fra klassen. Dette gøres for at splitte klassen op over
flere filer og gøre det mere overskueligt at finde rundt i.
"""

from typing import List

from sqlalchemy import func

from fire.api.model import (
    Sag,
    Punkt,
    PunktInformation,
    PunktInformationType,
    Observation,
    ObservationsType,
    Sagsevent,
    Beregning,
    EventType,
    Srid,
)


def indset_sag(self, sag: Sag):
    if not self._is_new_object(sag):
        raise Exception(f"Sag allerede tilføjet databasen: {sag}")
    if len(sag.sagsinfos) < 1:
        raise Exception("Mindst et SagsInfo objekt skal tilføjes Sagen")
    if sag.sagsinfos[-1].aktiv != "true":
        raise Exception("Sidst SagsInfo på sagen skal have aktiv = 'true'")
    self.session.add(sag)
    self.session.commit()


def indset_sagsevent(self, sagsevent: Sagsevent):
    if not self._is_new_object(sagsevent):
        raise Exception(f"Sagsevent allerede tilføjet databasen: {sagsevent}")
    if len(sagsevent.sagseventinfos) < 1:
        raise Exception("Mindst et SagseventInfo skal tilføjes Sag")
    self.session.add(sagsevent)
    self.session.commit()


def indset_flere_punkter(self, sagsevent: Sagsevent, punkter: List[Punkt]) -> None:
    """Indsæt flere punkter i punkttabellen, alle under samme sagsevent

    Parameters
    ----------
    sagsevent: Sagsevent
        Nyt (endnu ikke persisteret) sagsevent.

        NB: Principielt ligger "indset_flere_punkter" på et højere API-niveau
        end "indset_punkter", så det bør overvejes at generere sagsevent her.
        Argumentet vil så skulle ændres til "sagseventtekst: str", og der vil
        skulle tilføjes et argument "sag: Sag". Alternativt kan sagseventtekst
        autogenereres her ("oprettelse af punkterne nn, mm, ...")

    punkter: List[Punkt]
        De punkter der skal persisteres under samme sagsevent

    Returns
    -------
    None

    """
    # Check at alle punkter er i orden
    for punkt in punkter:
        if not self._is_new_object(punkt):
            raise Exception(f"Punkt allerede tilføjet databasen: {punkt}")
        if len(punkt.geometriobjekter) != 1:
            raise Exception(
                "Der skal tilføjes et (og kun et) GeometriObjekt til punktet"
            )

    self._check_and_prepare_sagsevent(sagsevent, EventType.PUNKT_OPRETTET)

    for punkt in punkter:
        punkt.sagsevent = sagsevent
        for geometriobjekt in punkt.geometriobjekter:
            if not self._is_new_object(geometriobjekt):
                raise Exception(
                    "Punktet kan ikke henvise til et eksisterende GeometriObjekt"
                )
            geometriobjekt.sagsevent = sagsevent
        for punktinformation in punkt.punktinformationer:
            if not self._is_new_object(punktinformation):
                raise Exception(
                    "Punktet kan ikke henvise til et eksisterende PunktInformation objekt"
                )
            punktinformation.sagsevent = sagsevent
        self.session.add(punkt)

    self.session.commit()


def indset_punkt(self, sagsevent: Sagsevent, punkt: Punkt):
    if not self._is_new_object(punkt):
        raise Exception(f"Punkt er allerede tilføjet databasen: {punkt}")
    if len(punkt.geometriobjekter) != 1:
        raise Exception("Der skal tilføjes et (og kun et) GeometriObjekt til punktet")
    self._check_and_prepare_sagsevent(sagsevent, EventType.PUNKT_OPRETTET)
    punkt.sagsevent = sagsevent
    for geometriobjekt in punkt.geometriobjekter:
        if not self._is_new_object(geometriobjekt):
            raise Exception(
                "Punktet kan ikke henvise til et eksisterende GeometriObjekt"
            )
        geometriobjekt.sagsevent = sagsevent
    for punktinformation in punkt.punktinformationer:
        if not self._is_new_object(punktinformation):
            raise Exception(
                "Punktet kan ikke henvise til et eksisterende PunktInformation objekt"
            )
        punktinformation.sagsevent = sagsevent
    self.session.add(punkt)
    self.session.commit()


def indset_punktinformation(
    self, sagsevent: Sagsevent, punktinformation: PunktInformation
):
    if not self._is_new_object(punktinformation):
        raise Exception(
            f"PunktInformation allerede tilføjet databasen: {punktinformation}"
        )
    self._check_and_prepare_sagsevent(sagsevent, EventType.PUNKTINFO_TILFOEJET)
    punktinformation.sagsevent = sagsevent
    self.session.add(punktinformation)
    self.session.commit()


def indset_punktinformationtype(self, punktinfotype: PunktInformationType):
    if not self._is_new_object(punktinfotype):
        raise Exception(
            f"PunktInformationType allerede tilføjet databasen: {punktinfotype}"
        )
    n = self.session.query(func.max(PunktInformationType.infotypeid)).one()[0]
    if n is None:
        n = 0
    punktinfotype.infotypeid = n + 1
    self.session.add(punktinfotype)
    self.session.commit()


def indset_observation(self, sagsevent: Sagsevent, observation: Observation):
    if not self._is_new_object(observation):
        raise Exception(f"Observation allerede tilføjet databasen: {observation}")
    self._check_and_prepare_sagsevent(sagsevent, EventType.OBSERVATION_INDSAT)
    observation.sagsevent = sagsevent
    self.session.add(observation)
    self.session.commit()


def indset_observationstype(self, observationstype: ObservationsType):
    if not self._is_new_object(observationstype):
        raise Exception(
            f"ObservationsType allerede tilføjet databasen: {observationstype}"
        )
    n = self.session.query(func.max(ObservationsType.observationstypeid)).one()[0]
    if n is None:
        n = 0
    observationstype.observationstypeid = n + 1
    self.session.add(observationstype)
    self.session.commit()


def indset_beregning(self, sagsevent: Sagsevent, beregning: Beregning):
    if not self._is_new_object(beregning):
        raise Exception(f"Beregning allerede tilføjet datbasen: {beregning}")

    self._check_and_prepare_sagsevent(sagsevent, EventType.KOORDINAT_BEREGNET)
    beregning.sagsevent = sagsevent
    for koordinat in beregning.koordinater:
        if not self._is_new_object(koordinat):
            raise Exception(f"Koordinat allerede tilføjet datbasen: {koordinat}")
        koordinat.sagsevent = sagsevent
    self.session.add(beregning)
    self.session.commit()


def indset_srid(self, srid: Srid):
    if not self._is_new_object(srid):
        raise Exception(f"Srid allerede tilføjet datbasen: {srid}")

    n = self.session.query(func.max(Srid.sridid)).one()[0]
    if n is None:
        n = 0
    srid.sridid = n + 1
    self.session.add(srid)
    self.session.commit()
