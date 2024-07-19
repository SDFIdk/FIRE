from typing import List, Iterator
from itertools import chain
import collections as cs

from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import text

from fire.api.firedb.hent import FireDbHent
from fire.api.firedb.indset import FireDbIndset
from fire.api.firedb.luk import FireDbLuk
from fire.api.model import (
    Punkt,
    Koordinat,
    Observation,
    PunktInformation,
    PunktInformationType,
    GeometriObjekt,
    Bbox,
    Sag,
    Sagsinfo,
    Sagsevent,
    FikspunktsType,
)


class FireDb(FireDbLuk, FireDbHent, FireDbIndset):
    def soeg_geometriobjekt(self, bbox) -> List[GeometriObjekt]:
        if not isinstance(bbox, Bbox):
            bbox = Bbox(bbox)
        return (
            self.session.query(GeometriObjekt)
            .filter(func.sdo_filter(GeometriObjekt.geometri, bbox) == "TRUE")
            .all()
        )

    def soeg_punkter(self, ident: str, antal: int = None) -> List[Punkt]:
        """
        Returnerer alle punkter der 'like'-matcher 'ident'

        Hvis intet punkt findes udsendes en NoResultFound exception.
        """
        result = (
            self.session.query(Punkt)
            .join(PunktInformation)
            .join(PunktInformationType)
            .filter(
                PunktInformationType.name.startswith("IDENT:"),
                PunktInformation.tekst.ilike(ident),
                Punkt._registreringtil == None,  # NOQA
            )
            .order_by(PunktInformation.tekst)
            .limit(antal)
            .all()
        )

        if not result:
            raise NoResultFound
        return result

    def ny_sag(self, behandler: str, beskrivelse: str) -> Sag:
        """
        Fabrik til oprettelse af nye sager.

        Oprettede sager er altid aktive, samt tilføjet og flushed
        på databasesessionen.
        """
        sagsinfo = Sagsinfo(
            aktiv="true",
            behandler=behandler,
            beskrivelse=beskrivelse,
        )
        sag = Sag(sagsinfos=[sagsinfo])
        self.session.add(sag)
        self.session.flush()

        return sag

    def tilknyt_landsnumre(
        self,
        punkter: List[Punkt],
        fikspunktstyper: List[FikspunktsType],
    ) -> List[PunktInformation]:
        """
        Tilknytter et landsnummer til punktet hvis der ikke findes et i forvejen.

        Returnerer en liste med IDENT:landsnr PunktInformation'er for alle de fikspunkter i
        `punkter` som ikke i forvejen har et landsnummer. Hvis alle fikspunkter i `punkter`
        allerede har et landsnummer returneres en tom liste.

        Kun punkter i Danmark kan tildeles et landsnummer. Det forudsættes at punktet
        har et tilhørende geometriobjekt og er indlæst i databasen i forvejen.

        Den returnerede liste er sorteret på samme vis som inputlisterne, dvs at det n'te
        element i outputlisten hører sammen med de n'te punkter i inputlisterne.
        """
        landsnr = self.hent_punktinformationtype("IDENT:landsnr")

        uuider = []
        punkttyper = {}
        for punkt, fikspunktstype in zip(punkter, fikspunktstyper):
            if not punkt.geometri:
                raise AttributeError("Geometriobjekt ikke tilknyttet Punkt")

            # Ignorer punkter, der allerede har et landsnummer
            if landsnr in [pi.infotype for pi in punkt.punktinformationer]:
                continue
            uuider.append(f"{punkt.id}")
            punkttyper[punkt.id] = fikspunktstype

        if not uuider:
            return []

        distrikter = self._opmålingsdistrikt_fra_punktid(uuider)
        distrikt_punkter = cs.defaultdict(list)
        for distrikt, pktid in distrikter:
            distrikt_punkter[distrikt].append(pktid)

        landsnumre = {}
        for distrikt, pkt_ider in distrikt_punkter.items():
            brugte_løbenumre = self._løbenumre_i_distrikt(distrikt)
            for punktid in pkt_ider:
                for kandidat in self._generer_tilladte_løbenumre(punkttyper[punktid]):
                    if kandidat in brugte_løbenumre:
                        continue

                    landsnumre[punktid] = f"{distrikt}-{kandidat}"
                    brugte_løbenumre.append(kandidat)
                    break

        # reorganiser landsnumre-dict så rækkefølgen matcher inputlisten "punkter"
        landsnumre = {p.id: landsnumre[p.id] for p in punkter}

        punktinfo = []
        for punktid, landsnummer in landsnumre.items():
            pi = PunktInformation(punktid=punktid, infotype=landsnr, tekst=landsnummer)
            punktinfo.append(pi)

        return punktinfo

    def tilknyt_gi_numre(self, punkter: List[Punkt]) -> List[PunktInformation]:
        """
        Tilknyt G.I. identer til punkter.

        Det højest anvendt løbenummer findes og punkterne tildeles de næste numre
        i rækken.
        """
        pit_gi = self.hent_punktinformationtype("IDENT:GI")

        def gi_ident(punkt, løbenummer):
            return PunktInformation(
                punkt=punkt, infotype=pit_gi, tekst=f"G.I.{løbenummer}"
            )

        sql = text(
            rf"""SELECT
                    max(to_number(
                        regexp_substr(pi.tekst, 'G.I.(.+)', 1, 1, '', 1)
                    )) lbnr
                 FROM punktinfo pi
                 WHERE
                    pi.registreringtil IS NULL
                        AND
                    pi.infotypeid = {pit_gi.infotypeid}
                        AND
                    pi.tekst LIKE 'G.I.%'
                        AND
                    pi.tekst != 'G.I.9999'
                 ORDER BY pi.tekst DESC
                 """
        )

        # Først ledige løbenummer
        løbenr = self.session.execute(sql).first()[0] + 1

        return [gi_ident(p, lnr) for lnr, p in enumerate(punkter, start=løbenr)]

    def fejlmeld_koordinat(self, koordinat: Koordinat, sagsevent: Sagsevent, commit = True):
        """
        Fejlmeld en allerede eksisterende koordinat.

        Hvis koordinaten er den eneste af sin slags på det tilknyttede punkt fejlmeldes
        og afregistreres den. Hvis koordinaten indgår i en tidsserie sker en af to ting:

        1. Hvis koordinaten forekommer midt i en tidsserie fejlmeldes den uden videre.
        2. Hvis koordinaten er den seneste i tidsserien fejlmeldes den, den foregående
           koordinat fejlmeldes og en ny koordinat indsættes med den foregåendes værdier.
           Denne fremgangsmåde sikrer at der er en aktuel og gyldig koordinat, samt at
           den samme koordinat ikke fremtræder to gange i en tidsserie.
        """
        punkt = koordinat.punkt
        srid = koordinat.srid
        ny_koordinat = None

        if len(punkt.koordinater) == 1:
            self._luk_fikspunktregisterobjekt(koordinat, sagsevent, commit=False)

        # byg relevant tidsserie
        tidsserie = []
        for k in punkt.koordinater:
            if k.srid != srid:
                continue
            tidsserie.append(k)

        # Er koordinaten den sidste i tidsserien?
        if koordinat.registreringtil is None and len(tidsserie) > 1:
            # Find seneste ikke-fejlmeldte koordinat så den
            # bruges som den seneste gyldige koordinat
            for forrige_koordinat in reversed(tidsserie[0:-1]):
                if not forrige_koordinat.fejlmeldt:
                    break

            if not forrige_koordinat.fejlmeldt:
                ny_koordinat = Koordinat(
                    punktid=forrige_koordinat.punktid,
                    sridid=forrige_koordinat.sridid,
                    x=forrige_koordinat.x,
                    y=forrige_koordinat.y,
                    z=forrige_koordinat.z,
                    t=forrige_koordinat.t,
                    sx=forrige_koordinat.sx,
                    sy=forrige_koordinat.sy,
                    sz=forrige_koordinat.sz,
                    transformeret=forrige_koordinat.transformeret,
                    artskode=forrige_koordinat.artskode,
                    _registreringfra=func.current_timestamp(),
                )

                # Sikr at den forrige koordinat *også* fejlmeldes, så vi
                # kan tilføje en ny kopi af den uden at komme i problemer med
                # KOORDINAT_UNIQ2_IDX constraint i databasen
                forrige_koordinat.fejlmeldt = True
                self.session.add(forrige_koordinat)
                self.session.flush()

                sagsevent.koordinater = [ny_koordinat]

                self.session.add(sagsevent)

        koordinat.fejlmeldt = True
        koordinat._registreringtil = func.current_timestamp()

        if ny_koordinat:
            koordinat._registreringtil = ny_koordinat._registreringfra

        self.session.add(koordinat)
        if commit:
            self.session.commit()

    def fejlmeld_observation(self, observation: Observation, sagsevent: Sagsevent, commit = True):
        """
        Fejlmeld en allerede eksisterende observation.
        """
        self._luk_fikspunktregisterobjekt(observation, sagsevent, commit=False)

        observation.fejlmeldt = True
        observation._registreringtil = func.current_timestamp()

        self.session.add(observation)
        if commit:
            self.session.commit()


    def _generer_tilladte_løbenumre(
        self, fikspunktstype: FikspunktsType
    ) -> Iterator[str]:
        """
        Returner en generator med alle tilladte løbenumre for en given type fikspunkt.

        Hjælpefunktion til tilknyt_landsnumre.
        """

        interval = lambda start, stop: (str(i).zfill(5) for i in range(start, stop + 1))

        if fikspunktstype == FikspunktsType.GI:
            return chain(interval(1, 10), interval(801, 8999))

        if fikspunktstype == FikspunktsType.MV:
            return interval(11, 799)

        if fikspunktstype == FikspunktsType.HØJDE:
            return chain(interval(9001, 10000), interval(19001, 19999))

        if fikspunktstype == FikspunktsType.JESSEN:
            return interval(81001, 81999)

        if fikspunktstype == FikspunktsType.HJÆLPEPUNKT:
            return interval(90001, 99999)

        if fikspunktstype == FikspunktsType.VANDSTANDSBRÆT:
            raise NotImplementedError(
                "Fikspunktstypen 'VANDSTANDSBRÆT' er endnu ikke understøttet"
            )

        raise ValueError("Ukendt fikspunktstype")

    def _opmålingsdistrikt_fra_punktid(self, uuider: List[str]):
        """
        Udtræk relevante opmålingsdistrikter, altså dem hvor de adspurgte punkter
        befinder sig i.

        Hjælpefunktion til tilknyt_landsnumre(). Defineret i seperat funktion
        med henblik på at kunne mocke den i unit tests.
        """
        statement = text(
            f"""SELECT upper(hs.kode), go.punktid
                FROM geometriobjekt go
                JOIN herredsogn hs ON sdo_inside(go.geometri, hs.geometri) = 'TRUE'
                WHERE
                go.punktid IN ({','.join([f"'{uuid}'" for uuid in uuider])})
            """
        )

        # sørg for at output returneres i samme rækkefølge som inputlisten, sikrer at tilknyt_landsnumre()
        # kan levere sit endelige output i samme orden som inputlisterne
        temp = {
            punktid: distrikt
            for distrikt, punktid in self.session.execute(statement).fetchall()
        }

        distrikter = [(temp[u], u) for u in uuider]

        return distrikter

    def _løbenumre_i_distrikt(self, distrikt: str):
        """
        For et givent opmålingsdistrikt findes alle landsnumre på formen
        xx-yyy-*****, hvorefter løbenummrene (*****) udskilles og returneres
        i sorteret orden.

        Hjælpefunktion til tilknyt_landsnumre(). Defineret i seperat funktion
        med henblik på at kunne mocke den i unit tests.
        """
        landsnr = self.hent_punktinformationtype("IDENT:landsnr")
        sql = text(
            rf"""SELECT lbnr
                FROM (
                    SELECT
                        regexp_substr(tekst, '.*-.*-(.+)', 1, 1, '', 1) lbnr
                    FROM punktinfo
                    WHERE infotypeid={landsnr.infotypeid} AND REGEXP_LIKE(tekst, '^{distrikt}-.+$')
                )
                ORDER BY lbnr ASC
                """
        )

        return [løbenummer[0] for løbenummer in self.session.execute(sql)]
