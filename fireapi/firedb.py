from datetime import datetime

from sqlalchemy import create_engine, func, event
from sqlalchemy.orm import sessionmaker
from .model import (
    Bbox,
    GeometriObjekt,
    Sag,
    Punkt,
    Koordinat,
    Observation,
    Beregning,
    RegisteringTidObjekt,
)

from typing import List, Union

DEBUG = True


class URN:
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return "EPSG:" + str(self.code)


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

    def hent_alle_punkter(self):
        return self.session.query(Punkt).all()

    def hent_alle_sager(self):
        return self.session.query(Sag).all()

    def soeg_geometriobjekt(self, bbox):
        if not isinstance(bbox, Bbox):
            bbox = Bbox(bbox)
        return (
            self.session.query(GeometriObjekt)
            .filter(func.sdo_filter(GeometriObjekt.geometri, bbox) == "TRUE")
            .all()
        )

    ### Søgnings
    def soeg_punkt(
        self, bbox: Bbox = None, navn=None, tid: datetime = None
    ) -> List[Punkt]:
        """ ... """
        pass

    def soeg_koordinat(
        self,
        bbox: Bbox = None,
        srid: URN = None,
        t1: datetime = None,
        t2: datetime = None,
    ) -> List[Koordinat]:
        """ find koordinater ud fra diverse søgekriterier (flere bør tilføjes)"""
        pass

    def soeg_observation(
        self,
        bbox: Bbox = None,
        srid: URN = None,
        t1: datetime = None,
        t2: datetime = None,
    ) -> List[Observation]:
        """ find observationer ud fra diverse søgekriterier (flere bør tilføjes)"""
        pass

    def soeg_sager(
        self, objekt: Union[Punkt, Observation, Beregning, Bbox]
    ) -> List[Sag]:
        """ søg efter en sag baseret på diverse kriterier """
        pass

    ### Læsning
    def hent_punkt(self, punkt: Punkt, tid: datetime = None) -> Punkt:
        """ Returner et specifikt punkt. Seneste version hvis tid==None. """
        pass

    def hent_koordinater(
        self,
        punkt: Punkt,
        fra: datetime = None,
        til: datetime = None,
        srid: List[URN] = None,
    ) -> List[Koordinat]:
        """ returner samtlige koordinater tilknyttet et givent punkt."""
        pass

    def hent_koordinat(
        self, punkt: Punkt, tid: datetime = None, srid: URN = None
    ) -> Koordinat:
        """ Hent koordinat fra et givent punkt, evt til et bestemt tidspunkt (ellers det seneste). """
        pass

    def hent_observationer(
        self, til_punkt: Punkt, fra: datetime = None, til: datetime = None
    ) -> List[Observation]:
        """ Hent alle observation hvori et specifikt punkt indgår. """
        pass

    def hent_observation(
        self, fra: Punkt, til1: Punkt = None, til2: Punkt = None
    ) -> Observation:
        """ Hent observation tilhørende et punkt, evt. til flere andre punkter. """
        pass

    def hent_beregning(self) -> Beregning:
        """ Hent en beregning """
        pass

    ### Indsættelse i database

    # def opret_sag(self, beskrivelse: str, behandler: str, sagstype: SagsType):
    #    ''' Opret en fikspunktssag '''
    #    pass

    def opret_punkt(self, sag: Sag, punkt: Punkt):
        """ Opret et punkt i databasen """
        pass

    def opret_observation(self, sag: Sag, observation: Observation):
        """ opret en observation i databasen """
        pass

    def opret_koordinat(self, sag: Sag, koordinat: Koordinat):
        """ opret koordinat """
        pass

    def opret_beregning(self, sag: Sag, beregning: Beregning):
        """ opret beregning """
        pass
