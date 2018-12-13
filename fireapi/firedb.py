import uuid
from sqlalchemy import create_engine, func, event, and_
from sqlalchemy.orm import sessionmaker, aliased
from .model import (
    RegisteringTidObjekt,
    Sag,
    Punkt,
    GeometriObjekt,
    Observation,
    Bbox,
    Sagsevent,
    Beregning,
    Koordinat,
)
from typing import List, Optional
from datetime import datetime

DEBUG = True


class FireDb(object):
    def __init__(self, connectionstring):
        """

        Parameters
        ----------
        connectionstring : str
            Connection string for the oracle database where the FIRE database resides.
            Of the general form 'user:pass@host:port/dbname[?key=value&key=value...]'
        """
        self.dialect = "oracle+cx_oracle"
        self.connectionstring = connectionstring
        self.engine = create_engine(
            f"{self.dialect}://{self.connectionstring}", echo=DEBUG
        )
        self.sessionmaker = sessionmaker(bind=self.engine)
        self.session = self.sessionmaker()

        @event.listens_for(self.sessionmaker, "before_flush")
        def listener(thissession, flush_context, instances):
            for obj in thissession.deleted:
                if isinstance(obj, RegisteringTidObjekt):
                    obj.registreringtil = func.sysdate()
                    thissession.add(obj)

    def hent_punkt(self, id: str) -> Punkt:
        return self.session.query(Punkt).filter(Punkt.id == id).first()

    def hent_alle_punkter(self) -> List[Punkt]:
        return self.session.query(Punkt).all()

    def hent_alle_sager(self) -> List[Sag]:
        return self.session.query(Sag).all()

    def soeg_geometriobjekt(self, bbox) -> List[GeometriObjekt]:
        if not isinstance(bbox, Bbox):
            bbox = Bbox(bbox)
        return (
            self.session.query(GeometriObjekt)
            .filter(func.sdo_filter(GeometriObjekt.geometri, bbox) == "TRUE")
            .all()
        )

    def hent_observationer_naer_opstillingspunkt(
        self,
        punkt: Punkt,
        afstand: float,
        tidfra: Optional[datetime] = None,
        tidtil: Optional[datetime] = None,
    ) -> List[Observation]:
        g1 = aliased(GeometriObjekt)
        g2 = aliased(GeometriObjekt)

        filterExps = [
            func.sdo_within_distance(
                g1.geometri, g2.geometri, "distance=" + str(afstand) + " unit=meter"
            )
            == "TRUE"
        ]

        if tidfra:
            filterExps.append(Observation.observationstidspunkt >= tidfra)

        if tidtil:
            filterExps.append(Observation.observationstidspunkt <= tidtil)

        filter = and_(*filterExps)

        return (
            self.session.query(Observation)
            .join(g1, Observation.opstillingspunktid == g1.punktid)
            .join(g2, g2.punktid == punkt.id)
            .filter(filter)
            .all()
        )

    def hent_observationer_naer(
        self, pointgeom, afstand, tidfra, tidtil
    ) -> List[Observation]:
        return self.session.query(Observation).all()

    def indset_sag(self, sag: Sag):
        if len(sag.sagsinfos) < 1:
            raise Exception("At least one sagsinfo must be added to the sag")
        if sag.sagsinfos[-1].aktiv != "true":
            raise Exception("Last sagsinfo should have aktiv = 'true'")
        self.session.add(sag)
        self.session.commit()

    def indset_observation(self, sag: Sag, observation: Observation):
        sagsevent = Sagsevent(id=str(uuid.uuid4()), sag=sag, event="observation_indsat")
        observation.sagsevent = sagsevent
        # self.session.add(sagsevent)
        self.session.add(observation)
        self.session.commit()


""" TODO: API need more thought
    def indset_beregning(self, sag: Sag, beregning: Beregning):
        sagsevent = Sagsevent(id=str(uuid.uuid4()), sag=sag, event="koordinat_beregnet")
        #self.session.add(sagsevent)
        beregning.sagsevent = sagsevent
        self.session.add(beregning)
        self.session.commit()
"""

