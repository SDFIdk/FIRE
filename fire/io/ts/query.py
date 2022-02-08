"""
Modul til forespørgsler.

"""

hent_mulige_tidsserier = """\
SELECT
  count(s.sridid),
  s.srid
FROM koordinat k
JOIN sridtype s ON s.sridid=k.sridid
WHERE
  k.punktid = '{punkt_id}'
GROUP BY
  s.srid
ORDER BY
  count(s.sridid) DESC
"""

hent_tidsserie = """\
WITH jessen_punkter AS (
    SELECT
        p.id AS punkt_id,
        pi.tekst AS jessen_id
    FROM punkt p
    JOIN punktinfo pi ON p.id = pi.punktid
    JOIN punktinfotype pit ON pi.infotypeid = pit.infotypeid
    WHERE
        pit.infotype='IDENT:jessen'
),
landsnumre AS (
    SELECT
        p.id,
        pi.tekst AS landsnr
    FROM punkt p
    JOIN punktinfo pi ON p.id = pi.punktid
    JOIN punktinfotype pit ON pi.infotypeid = pit.infotypeid
    WHERE pit.infotype = 'IDENT:landsnr'
)
SELECT
    p.id AS punkt_id,
    k.t AS dato,
    k.z AS kote,
--    CASE jp.jessen_id WHEN jp.jessen_id THEN 1 ELSE 0 END AS er_jessen_punkt,
    jp.jessen_id,
    l.landsnr

FROM punkt p

JOIN koordinat k ON p.id = k.punktid
JOIN sridtype s ON k.sridid = s.sridid

-- Der kan være punkter med i punktgruppen, som er Jessen-puknt i en anden tidsserie.
-- Med et ekstra krav i denne left join om, at `jessen_id` skal være det samme, som tidsserie-ID'et,
-- gør, at kun tidsseriens Jessen-ID kommer med.
LEFT JOIN jessen_punkter jp ON p.id = jp.punkt_id AND jp.jessen_id = '{jessen_id}'

LEFT JOIN landsnumre l ON p.id = l.id

WHERE
    s.srid = 'TS:{jessen_id}'
ORDER BY
    jp.jessen_id ASC,
    k.t ASC
"""


def observationer_i_punktgruppe(
    punktgruppe,
    dato_fra,
    dato_til,
    observationstypeid,
):
    comma_separated = "', '".join(punktgruppe)
    sql_tuple = f"(\n'{comma_separated}'\n)"
    return f"""\
SELECT DISTINCT
    o.registreringfra,
    o.opstillingspunktid,
    o.sigtepunktid,
    o.value1 AS koteforskel,
    o.value2 AS nivlaengde,
    o.value3 AS opstillinger,
    o.value{4 if observationstypeid == 1 else 5} AS spredning_afstand,
    o.value{5 if observationstypeid == 1 else 6} AS spredning_centrering,
    o.observationstypeid,
    o.observationstidspunkt,
    o.id AS uuid
FROM punkt p
JOIN observation o ON p.id = o.opstillingspunktid OR p.id = o.sigtepunktid
WHERE
    o.observationstypeid = {observationstypeid}
  AND
    o.registreringfra BETWEEN DATE '{dato_fra}' AND DATE '{dato_til}'
  AND
    o.opstillingspunktid IN {sql_tuple}
  AND
    o.sigtepunktid IN {sql_tuple}
ORDER BY
    o.registreringfra ASC,
    o.opstillingspunktid ASC,
    o.sigtepunktid ASC
"""


def observationer_for_tidsserie(
    jessen_id,
    dato_fra,
    dato_til,
    observationstypeid,
):
    return f"""\
WITH tidsserie_punkter AS (
    SELECT DISTINCT p.id
    FROM punkt p
    JOIN koordinat k ON p.id = k.punktid
    JOIN sridtype s ON k.sridid = s.sridid
    WHERE s.srid = 'TS:{jessen_id}'
)
SELECT DISTINCT
    o.registreringfra,
    o.opstillingspunktid AS fra,
    o.sigtepunktid AS til,
    o.value1 AS koteforskel,
    o.value2 AS nivlaengde,
    o.value3 AS opstillinger,
    o.value{4 if observationstypeid == 1 else 5} AS spredning_afstand,
    o.value{5 if observationstypeid == 1 else 6} AS spredning_centrering,
    o.observationstypeid,
    o.observationstidspunkt,
    o.id AS uuid
FROM tidsserie_punkter tp
JOIN observation o ON tp.id = o.opstillingspunktid OR tp.id = o.sigtepunktid
WHERE
    o.observationstypeid = {observationstypeid}
  AND
    o.registreringfra BETWEEN DATE '{dato_fra}' AND DATE '{dato_til}'
  AND
    o.opstillingspunktid IN (SELECT tp.id FROM tidsserie_punkter tp)
  AND
    o.sigtepunktid IN (SELECT tp.id FROM tidsserie_punkter tp)
ORDER BY
    o.registreringfra ASC,
    o.opstillingspunktid ASC,
    o.sigtepunktid ASC
"""
