"""
Funktionalitet til at indsætte diverse FIRE objekter

"""

from sqlalchemy import func
from fire.api.firedb.base import FireDbBase

from fire.api.model import (
    Sag,
    PunktInformationType,
    ObservationsType,
    Sagsevent,
    EventType,
    Srid,
)


class FireDbIndset(FireDbBase):
    def indset_sag(self, sag: Sag, commit: bool = True):
        if not self._is_new_object(sag):
            raise Exception(f"Sag allerede tilføjet databasen: {sag}")
        if len(sag.sagsinfos) < 1:
            raise Exception("Mindst et SagsInfo objekt skal tilføjes Sagen")
        if sag.sagsinfos[-1].aktiv != "true":
            raise Exception("Sidst SagsInfo på sagen skal have aktiv = 'true'")
        self.session.add(sag)

        if commit:
            self.session.commit()

    def indset_sagsevent(self, sagsevent: Sagsevent, commit: bool = True):
        """
        Indsætter sagsevent og tilføjer eller ændrer tilknytteede FikspunktsregisterObjekter
        i databasen.
        """
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
                    raise Exception(
                        f"Beregning allerede tilføjet databasen: {beregning}"
                    )

            for koordinat in sagsevent.koordinater:
                if not self._is_new_object(koordinat):
                    raise Exception(
                        f"Koordinat allerede tilføjet datbasen: {koordinat}"
                    )
                koordinat.sagsevent = sagsevent

        if sagsevent.eventtype == EventType.KOORDINAT_NEDLAGT:
            self._check_and_prepare_sagsevent(sagsevent, EventType.KOORDINAT_NEDLAGT)
            for koordinat in sagsevent.koordinater_slettede:
                self._luk_fikspunkregisterobjekt(koordinat, sagsevent, commit=commit)

        if sagsevent.eventtype == EventType.OBSERVATION_INDSAT:
            self._check_and_prepare_sagsevent(sagsevent, EventType.OBSERVATION_INDSAT)

            for obs in sagsevent.observationer:
                if not self._is_new_object(obs):
                    raise Exception(f"Observation allerede tilføjet databasen: {obs}")

        if sagsevent.eventtype == EventType.OBSERVATION_NEDLAGT:
            self._check_and_prepare_sagsevent(sagsevent, EventType.OBSERVATION_NEDLAGT)

            for obs in sagsevent.observationer_slettede:
                self._luk_fikspunkregisterobjekt(obs, sagsevent, commit=commit)

        if sagsevent.eventtype == EventType.PUNKTINFO_TILFOEJET:
            self._check_and_prepare_sagsevent(sagsevent, EventType.PUNKTINFO_TILFOEJET)

            for punktinformation in sagsevent.punktinformationer:
                if not self._is_new_object(punktinformation):
                    raise Exception(
                        f"PunktInformation allerede tilføjet databasen: {punktinformation}"
                    )

        if sagsevent.eventtype == EventType.PUNKTINFO_FJERNET:
            self._check_and_prepare_sagsevent(sagsevent, EventType.PUNKTINFO_FJERNET)

            for punktinformation in sagsevent.punktinformationer_slettede:
                self._luk_fikspunkregisterobjekt(
                    punktinformation, sagsevent, commit=commit
                )

        if sagsevent.eventtype == EventType.GRAFIK_INDSAT:
            self._check_and_prepare_sagsevent(sagsevent, EventType.GRAFIK_INDSAT)

            for grafik in sagsevent.grafikker:
                if not self._is_new_object(grafik):
                    raise Exception(f"Grafik allerede tilføjet datbasen: {grafik}")
                grafik.sagsevent = sagsevent

        if sagsevent.eventtype == EventType.GRAFIK_NEDLAGT:
            self._check_and_prepare_sagsevent(sagsevent, EventType.GRAFIK_NEDLAGT)

            for grafik in sagsevent.grafikker:
                self._luk_fikspunktsregisterobjekt(grafik, sagsevent, commit=commit)

        self.session.add(sagsevent)
        if commit:
            self.session.commit()

    def indset_punktinformationtype(
        self, punktinfotype: PunktInformationType, commit: bool = True
    ):
        if not self._is_new_object(punktinfotype):
            raise Exception(
                f"PunktInformationType allerede tilføjet databasen: {punktinfotype}"
            )
        n = self.session.query(func.max(PunktInformationType.infotypeid)).one()[0]
        if n is None:
            n = 0
        punktinfotype.infotypeid = n + 1
        self.session.add(punktinfotype)

        if commit:
            self.session.commit()

    def indset_observationstype(
        self, observationstype: ObservationsType, commit: bool = True
    ):
        if not self._is_new_object(observationstype):
            raise Exception(
                f"ObservationsType allerede tilføjet databasen: {observationstype}"
            )
        n = self.session.query(func.max(ObservationsType.observationstypeid)).one()[0]
        if n is None:
            n = 0
        observationstype.observationstypeid = n + 1
        self.session.add(observationstype)

        if commit:
            self.session.commit()

    def indset_srid(self, srid: Srid, commit: bool = True):
        if not self._is_new_object(srid):
            raise Exception(f"Srid allerede tilføjet datbasen: {srid}")

        n = self.session.query(func.max(Srid.sridid)).one()[0]
        if n is None:
            n = 0
        srid.sridid = n + 1
        self.session.add(srid)
        if commit:
            self.session.commit()
