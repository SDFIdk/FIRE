from typing import (
    List,
    Iterator,
    Mapping,
    Tuple,
)
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
    PunktInformation,
    PunktInformationType,
    GeometriObjekt,
    Bbox,
    Sagsevent,
    FikspunktsType,
)


def informationstyper(punkt: Punkt) -> List[PunktInformationType]:
    """Returnerer punktets informationstyper."""
    return [pi.infotype for pi in punkt.punktinformationer]


def forespørgsel_landsnumre(punkt_id_liste: List[str]) -> text:
    """
    Byg forespørgsel, der henter punkt-ID og landsnummerdistrikt for givne punkt-ID'er.

    """
    return text(
        f"""SELECT go.punktid, upper(hs.kode)
            FROM geometriobjekt go
            JOIN herredsogn hs ON sdo_relate(hs.geometri, go.geometri, 'mask=contains') = 'TRUE'
            WHERE
            go.punktid IN ({','.join([f"'{punkt_id}'" for punkt_id in punkt_id_liste])})
        """
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
        for punkt in punkter:
            if not punkt.geometri:
                raise AttributeError("Geometriobjekt ikke tilknyttet Punkt")

        landsnr = self.hent_punktinformationtype("IDENT:landsnr")
        punkter_uden_landsnr = {
            punkt.id: fikspunktstype
            for punkt, fikspunktstype in zip(punkter, fikspunktstyper)
            if landsnr in informationstyper(punkt)
        }
        if not punkter_uden_landsnr:
            return []

        distrikter = self._opmålingsdistrikt_fra_punktid(list(punkter_uden_landsnr))
        # Gruppér punkt-ID'er efter distrikt
        distrikt_punkter = cs.defaultdict(list)
        for (punkt_id, distrikt) in distrikter.items():
            distrikt_punkter[distrikt].append(punkt_id)

        # Opbyg ny tabel med punkt-ID til næste ledige landsnummer.
        landsnumre = {}
        # Løb over hvert enkelt distrikt.
        for (distrikt, punkt_id_liste) in distrikt_punkter.items():

            # Hent eksisterende, aktive løbenumre inden for distriktet.
            løbenumre_i_distrikt = self._løbenumre_i_distrikt(distrikt)

            # Løb over hvert nyetableret punkt i distriktet.
            for punkt_id in punkt_id_liste:

                # Punktets fikspunktstype afgør, hvordan løbenumrene dannes.
                fikspunktstype = punkter_uden_landsnr[punkt_id]

                # Løb over alle tilladte løbenumre fra det første til det næste ledige.
                for kandidat in self._generer_tilladte_løbenumre(fikspunktstype):

                    # Er det ikke ledigt, så fortsæt til det næste løbenummer i rækkefølgen
                    if kandidat in løbenumre_i_distrikt:
                        continue

                    # Løbenummeret er ledigt. Knyt det til punktet
                    landsnumre[punkt_id] = f"{distrikt}-{kandidat}"
                    løbenumre_i_distrikt.append(kandidat)

                    # Afbryd tildelingen og fortsæt til det næste nyetablerede punkt
                    break

        # reorganiser landsnumre-dict så rækkefølgen matcher inputlisten "punkter"
        # TODO: BUG her, hvis nogen af punkterne givet til denne metode blev taget ud, fordi de allerede havde et landsnummer?
        landsnumre = {p.id: landsnumre[p.id] for p in punkter}

        return [
            PunktInformation(punktid=punkt_id, infotype=landsnr, tekst=landsnummer)
            for punkt_id, landsnummer in landsnumre.items()
        ]

    def tilknyt_gi_nummer(self, punkt: Punkt) -> PunktInformation:
        """
        Tilknyt et G.I. ident til et punkt.
        """
        sql = text(
            fr"""SELECT max(to_number(regexp_substr(pi.tekst, 'G.I.(.+)', 1, 1, '', 1))) lbnr FROM punktinfo pi
                 JOIN punktinfotype pit ON pit.infotypeid=pi.infotypeid
                 WHERE
                 pi.registreringtil IS NULL
                     AND
                 pit.infotype = 'IDENT:GI'
                     AND
                 pi.tekst LIKE 'G.I.%'
                     AND
                 pi.tekst != 'G.I.9999'
                 ORDER BY pi.tekst DESC
                 """
        )

        løbenummer = self.session.execute(sql).first()[0]
        gi_ident = self.hent_punktinformationtype("IDENT:GI")
        return PunktInformation(
            punktid=punkt.id, infotype=gi_ident, tekst=f"G.I.{løbenummer+1}"
        )

    def fejlmeld_koordinat(self, sagsevent: Sagsevent, koordinat: Koordinat):
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
            self._luk_fikspunkregisterobjekt(koordinat, sagsevent, commit=False)

        # Er koordinaten den sidste i tidsserien?
        if koordinat.registreringtil is None:
            # Find seneste ikke-fejlmeldte koordinat så den
            # bruges som den seneste gyldige koordinat
            for forrige_koordinat in reversed(punkt.koordinater[0:-1]):
                if forrige_koordinat.srid != srid:
                    continue
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
                    _registreringfra=func.sysdate(),
                )

                sagsevent.koordinater = [ny_koordinat]

                self.session.add(sagsevent)

        koordinat.fejlmeldt = True
        if ny_koordinat:
            koordinat._registreringtil = ny_koordinat._registreringfra

        self.session.add(koordinat)
        self.session.commit()

    @property
    def basedir_skitser(self):
        """Returner absolut del af sti til skitser."""
        konf = self._hent_konfiguration()
        return konf.dir_skitser

    @property
    def basedir_materiale(self):
        """Returner absolut del af sti til sagsmateriale."""
        konf = self._hent_konfiguration()
        return konf.dir_materiale

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

    def _opmålingsdistrikt_fra_punktid(
        self, punkt_id_liste: List[str]
    ) -> Mapping[str, str]:
        """
        Udtræk relevante opmålingsdistrikter, altså dem hvor de adspurgte punkter
        befinder sig i.

        Hjælpefunktion til tilknyt_landsnumre(). Defineret i seperat funktion
        med henblik på at kunne mocke den i unit tests.

        """
<<<<<<< HEAD
        statement = text(
            f"""SELECT upper(hs.kode), go.punktid
                FROM geometriobjekt go
                JOIN herredsogn hs ON sdo_inside(go.geometri, hs.geometri) = 'TRUE'
                WHERE
                go.punktid IN ({','.join([f"'{uuid}'" for uuid in uuider])})
            """
=======
        # Returnér (distrikt, punkt-ID)-poster i samme rækkefølge som inputlisten.
        # Détte sikrer, at tilknyt_landsnumre() kan levere sit output i samme
        # orden som inputlisterne i regnearket.
        resultater = dict(
            self.session.execute(forespørgsel_landsnumre(punkt_id_liste)).fetchall()
>>>>>>> 624999f (Uddyb og refaktorisér tilnyt_landsnumre(). Tilføj kommentarer, så det er klart, hvad metoden gør.)
        )
        return {punkt_id: resultater[punkt_id] for punkt_id in punkt_id_liste}

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
            fr"""SELECT lbnr
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
