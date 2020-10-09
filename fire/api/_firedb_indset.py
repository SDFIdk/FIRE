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

    if sagsevent.eventtype == EventType.PUNKT_OPRETTET:
        self._check_and_prepare_sagsevent(sagsevent, EventType.PUNKT_OPRETTET)

        # Check at alle punkter er i orden
        for punkt in sagsevent.punkter:
            if not self._is_new_object(punkt):
                raise Exception(f"Punkt allerede tilføjet databasen: {punkt}")
            if len(punkt.geometriobjekter) != 1:
                raise Exception(
                    "Der skal tilføjes et (og kun et) GeometriObjekt til punktet"
                )
            for geometriobjekt in punkt.geometriobjekter:
                if not self._is_new_object(geometriobjekt):
                    raise Exception(
                        "Punktet kan ikke henvise til et eksisterende GeometriObjekt"
                    )
                geometriobjekt.sagsevent = sagsevent

    if sagsevent.eventtype == EventType.KOORDINAT_BEREGNET:
        self._check_and_prepare_sagsevent(sagsevent, EventType.KOORDINAT_BEREGNET)
        for beregning in sagsevent.beregninger:
            if not self._is_new_object(beregning):
                raise Exception(f"Beregning allerede tilføjet databasen: {beregning}")

        for koordinat in sagsevent.koordinater:
            if not self._is_new_object(koordinat):
                raise Exception(f"Koordinat allerede tilføjet datbasen: {koordinat}")
            koordinat.sagsevent = sagsevent

    if sagsevent.eventtype == EventType.OBSERVATION_INDSAT:
        self._check_and_prepare_sagsevent(sagsevent, EventType.OBSERVATION_INDSAT)

        for obs in sagsevent.observationer:
            if not self._is_new_object(obs):
                raise Exception(f"Observation allerede tilføjet databasen: {obs}")

    self.session.add(sagsevent)
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


def indset_srid(self, srid: Srid):
    if not self._is_new_object(srid):
        raise Exception(f"Srid allerede tilføjet datbasen: {srid}")

    n = self.session.query(func.max(Srid.sridid)).one()[0]
    if n is None:
        n = 0
    srid.sridid = n + 1
    self.session.add(srid)
    self.session.commit()
