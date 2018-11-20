from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from .model import *

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
        self.engine = create_engine(f"{self.dialect}://{self.connectionstring}", echo=DEBUG)
        self.sessionmaker = sessionmaker(bind=self.engine)
        self.session = self.sessionmaker()

    def hent_alle_punkter(self):
        return self.session.query(Punkt).all()

    def hent_alle_sager(self):
        return self.session.query(Sag).all()

    def soeg_geometriobjekt(self, bbox):
        if not isinstance(bbox, Bbox):
            bbox = Bbox(bbox)
        return self.session.query(GeometriObjekt).filter(func.sdo_filter(GeometriObjekt.geometri, bbox) == 'TRUE').all()
