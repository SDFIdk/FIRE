from datetime import datetime
from typing import List, Optional

from sqlalchemy import create_engine, func, event, and_, inspect
from sqlalchemy.orm import sessionmaker, aliased

from fire.api.model import (
    RegisteringTidObjekt,
    Sag,
    Punkt,
    PunktInformation,
    PunktInformationType,
    GeometriObjekt,
    Observation,
    ObservationType,
    Bbox,
    Sagsevent,
    Beregning,
    Geometry,
    EventType,
    Srid,
)


class FireDb(object):
    def __init__(self, connectionstring, debug=False):
        """

        Parameters
        ----------
        connectionstring : str
            Connection string for the oracle database where the FIRE database resides.
            Of the general form 'user:pass@host:port/dbname[?key=value&key=value...]'
        debug: bool
            if True, the SQLALchemy Engine will log all statements as well as a repr() of their parameter lists to the
            engines logger, which defaults to sys.stdout
        """
        self.dialect = "oracle+cx_oracle"
        self.connectionstring = connectionstring
        self.engine = create_engine(
            f"{self.dialect}://{self.connectionstring}",
            connect_args={"encoding": "UTF-8", "nencoding": "UTF-8"},
            echo=debug,
        )
        self.sessionmaker = sessionmaker(bind=self.engine)
        self.session = self.sessionmaker(autoflush=False)

        @event.listens_for(self.sessionmaker, "before_flush")
        def listener(thissession, flush_context, instances):
            for obj in thissession.deleted:
                if isinstance(obj, RegisteringTidObjekt):
                    obj._registreringtil = func.sysdate()
                    thissession.add(obj)

    # region "Hent" methods

    def hent_punkt(self, punktid: str) -> Punkt:
        p = aliased(Punkt)
        return (
            self.session.query(p)
            .filter(p.id == punktid, p._registreringtil == None)
            .one()
        )

    def hent_geometri_objekt(self, punktid: str) -> GeometriObjekt:
        go = aliased(GeometriObjekt)
        return (
            self.session.query(go)
            .filter(go.punktid == punktid, go._registreringtil == None)
            .one()
        )

    def hent_alle_punkter(self) -> List[Punkt]:
        return self.session.query(Punkt).all()

    def hent_sag(self, sagid: str) -> Sag:
        return self.session.query(Sag).filter(Sag.id == sagid).one()

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

    def hent_observationtype(self, name: str) -> ObservationType:
        """Gets ObservationType by its name.

        Parameters
        ----------
        observationstypeid : str
            Name (including namespace) of the observationtype.

        Returns
        -------
        ObservationType:
            The first ObservationType matching the specified name. None if not found.

        """
        namefilter = name
        return (
            self.session.query(ObservationType)
            .filter(ObservationType.name == namefilter)
            .first()
        )

    def hent_observationtyper(
        self, namespace: Optional[str] = None
    ) -> List[ObservationType]:
        """Gets all ObservationTyper optionally filtered by namespace.
        """
        if not namespace:
            return self.session.query(ObservationType).all()
        like_filter = f"{namespace}:%"
        return (
            self.session.query(ObservationType)
            .filter(ObservationType.name.ilike(like_filter))
            .all()
        )

    def hent_observationer(self, objectids: List[int]) -> List[Observation]:
        return (
            self.session.query(Observation)
            .filter(Observation.objectid.in_(objectids))
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
        return (
            self.session.query(Observation)
            .join(g1, Observation.opstillingspunktid == g1.punktid)
            .join(g2, g2.punktid == punkt.id)
            .filter(
                self._filter_observationer(
                    g1.geometri, g2.geometri, afstand, tidfra, tidtil
                )
            )
            .all()
        )

    def hent_observationer_naer_geometri(
        self,
        geometri: Geometry,
        afstand: float,
        tidfra: Optional[datetime] = None,
        tidtil: Optional[datetime] = None,
    ) -> List[Observation]:
        """
        Parameters
        ----------
        geometri
            Either a WKT string or a Geometry instance which will be used as
            filter to identify the set of spatial objects that are within some
            specified distance of the given object.
        """
        g = aliased(GeometriObjekt)
        return (
            self.session.query(Observation)
            .join(
                g,
                g.punktid == Observation.opstillingspunktid
                or g.punktid == Observation.sigtepunktid,
            )
            .filter(
                self._filter_observationer(
                    g.geometri, geometri, afstand, tidfra, tidtil
                )
            )
            .all()
        )

    def hent_srid(self, sridid: str):
        """Gets a Srid object by its id.

        Parameters
        ----------
        sridid : str
            srid id string. For instance "EPSG:25832"

        Returns
        -------
        Srid
            Srid object with the specified id. None if not found.

        """
        srid_filter = str(sridid).upper()
        return self.session.query(Srid).filter(Srid.name == srid_filter).one()

    def hent_srider(self, namespace: Optional[str] = None):
        """Gets Srid objects. Optionally filtering by srid namespace

        Parameters
        ----------
        namespace: str - optional
            Return only Srids with the specified namespace. For instance "EPSG". If not specified all objects are returned.

        Returns
        -------
        List of Srid

        """
        if not namespace:
            return self.session.query(Srid).all()
        like_filter = f"{namespace}:%"
        return self.session.query(Srid).filter(Srid.name.ilike(like_filter)).all()

    def hent_punktinformationtype(self, infotype: str):
        typefilter = infotype
        return (
            self.session.query(PunktInformationType)
            .filter(PunktInformationType.name == typefilter)
            .first()
        )

    def hent_punktinformationtyper(self, namespace: Optional[str] = None):
        if not namespace:
            return self.session.query(PunktInformationType).all()
        like_filter = f"{namespace}:%"
        return (
            self.session.query(PunktInformationType)
            .filter(PunktInformationType.name.ilike(like_filter))
            .all()
        )

    # endregion

    # region "Indset" methods

    def indset_sag(self, sag: Sag):
        if not self._is_new_object(sag):
            raise Exception(f"Cannot re-add already persistent sag: {sag}")
        if len(sag.sagsinfos) < 1:
            raise Exception("At least one sagsinfo must be added to the sag")
        if sag.sagsinfos[-1].aktiv != "true":
            raise Exception("Last sagsinfo should have aktiv = 'true'")
        self.session.add(sag)
        self.session.commit()

    def indset_sagsevent(self, sagsevent: Sagsevent):
        if not self._is_new_object(sagsevent):
            raise Exception(f"Cannot re-add already persistent sagsevent: {sagsevent}")
        if len(sagsevent.sagseventinfos) < 1:
            raise Exception("At least one sagseventinfo must be added to the sagsevent")
        self.session.add(sagsevent)
        self.session.commit()

    def indset_punkt(self, sagsevent: Sagsevent, punkt: Punkt):
        if not self._is_new_object(punkt):
            raise Exception(f"Cannot re-add already persistent punkt: {punkt}")
        if len(punkt.geometriobjekter) != 1:
            raise Exception("A single geometriobjekt must be added to the punkt")
        self._check_and_prepare_sagsevent(sagsevent, EventType.PUNKT_OPRETTET)
        punkt.sagsevent = sagsevent
        for geometriobjekt in punkt.geometriobjekter:
            if not self._is_new_object(geometriobjekt):
                raise Exception(f"Added punkt cannot refer to existing geometriobjekt")
            geometriobjekt.sagsevent = sagsevent
        for punktinformation in punkt.punktinformationer:
            if not self._is_new_object(punktinformation):
                raise Exception(
                    f"Added punkt cannot refer to existing punktinformation"
                )
            punktinformation.sagsevent = sagsevent
        self.session.add(punkt)
        self.session.commit()

    def indset_punktinformation(
        self, sagsevent: Sagsevent, punktinformation: PunktInformation
    ):
        if not self._is_new_object(punktinformation):
            raise Exception(
                f"Cannot re-add already persistant punktinformation: {punktinformation}"
            )
        self._check_and_prepare_sagsevent(sagsevent, EventType.PUNKTINFO_TILFOEJET)
        punktinformation.sagsevent = sagsevent
        self.session.add(punktinformation)
        self.session.commit()

    def indset_punktinformationtype(self, punktinfotype: PunktInformationType):
        if not self._is_new_object(punktinfotype):
            raise Exception(
                f"Cannot re-add already persistant punktinformationtype: {punktinfotype}"
            )
        n = self.session.query(func.max(PunktInformationType.infotypeid)).one()[0]
        if n is None:
            n = 0
        punktinfotype.infotypeid = n + 1
        self.session.add(punktinfotype)
        self.session.commit()

    def indset_observation(self, sagsevent: Sagsevent, observation: Observation):
        if not self._is_new_object(observation):
            raise Exception(
                f"Cannot re-add already persistent observation: {observation}"
            )
        self._check_and_prepare_sagsevent(sagsevent, EventType.OBSERVATION_INDSAT)
        observation.sagsevent = sagsevent
        self.session.add(observation)
        self.session.commit()

    def indset_observationtype(self, observationtype: ObservationType):
        if not self._is_new_object(observationtype):
            raise Exception(
                f"Cannot re-add already persistent observationtype: {observationtype}"
            )
        n = self.session.query(func.max(ObservationType.observationstypeid)).one()[0]
        if n is None:
            n = 0
        observationtype.observationstypeid = n + 1
        self.session.add(observationtype)
        self.session.commit()

    def indset_beregning(self, sagsevent: Sagsevent, beregning: Beregning):
        if not self._is_new_object(beregning):
            raise Exception(f"Cannot re-add already persistent beregning: {beregning}")

        self._check_and_prepare_sagsevent(sagsevent, EventType.KOORDINAT_BEREGNET)
        beregning.sagsevent = sagsevent
        for koordinat in beregning.koordinater:
            if not self._is_new_object(koordinat):
                raise Exception(
                    f"Added beregning cannot refer to existing koordinat: {koordinat}"
                )
            koordinat.sagsevent = sagsevent
        self.session.add(beregning)
        self.session.commit()

    def indset_srid(self, srid: Srid):
        if not self._is_new_object(srid):
            raise Exception(f"Cannot re-add already persistent Srid: {srid}")

        n = self.session.query(func.max(Srid.sridid)).one()[0]
        if n is None:
            n = 0
        srid.sridid = n + 1
        self.session.add(srid)
        self.session.commit()

    # endregion

    # region Private methods

    def _check_and_prepare_sagsevent(self, sagsevent: Sagsevent, eventtype: EventType):
        """Checks that the given Sagsevent is valid in the context given by eventtype.

        The sagsevent must be a "new" object (ie not persisted ot the database). It must have the specified eventtype.
        If the sagsevent doesnt have an id, this method will assign a guid.
        """
        if not self._is_new_object(sagsevent):
            raise Exception("Do not attach new objects to an existing Sagsevent")
        if sagsevent.eventtype is None:
            sagsevent.eventtype = eventtype
        elif sagsevent.eventtype != eventtype:
            raise Exception(f"'{sagsevent.eventtype}' sagsevent. Should be {eventtype}")

    def _filter_observationer(
        self,
        g1,
        g2,
        distance: float,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ):
        exps = [
            func.sdo_within_distance(
                g1, g2, "distance=" + str(distance) + " unit=meter"
            )
            == "TRUE"
        ]
        if from_date:
            exps.append(Observation.observationstidspunkt >= from_date)
        if to_date:
            exps.append(Observation.observationstidspunkt <= to_date)
        return and_(*exps)

    def _is_new_object(self, obj):
        """Check that the object has not been persisted to the database (= is 'new').

        Parameters
        ----------
        obj: object
            Object to check.

        Returns
        -------
        bool
            True if object has not been persisted. False otherwise
        """
        # here are the five states:
        # state.transient   # !session & !identity_key
        # state.pending     # session & !identity_key
        # state.persistent  # session &  identity_key
        # state.detached    # !session &  identity_key
        # state.deleted     # session & identity_key, flushed but not committed. Commit moves it to detached state
        insp = inspect(obj)
        return not (insp.persistent or insp.detached)

    # endregion
