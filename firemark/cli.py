from math import sqrt
from pyproj import Proj
from typing import Dict, List, Set, Tuple, IO
import json
import os
import sys

from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound
import click

from firecli import firedb
from fireapi.model import Punkt, PunktInformation, PunktInformationType, Srid, Koordinat
import firecli


@click.group()
def mark():
    """Arbejd med markdatafiler"""
    pass


@mark.command()
@firecli.default_options()
@click.option(
    '-o', '--output', default='', type=click.Path(writable=True, readable=False, allow_dash=True),
    help='Sæt navn på outputfil'
)
@click.option(
    '-p', '--preload', default='', type=click.Path(writable=False, readable=True, allow_dash=False),
    help='Angiv navn på fil med foreløbige punktnavne/placeringer'
)
@click.argument('filnavne', nargs=-1, type=click.File('rt'))
def gamaficer(filnavne: List[click.File('rt')], output: click.Path, preload: click.Path, **kwargs) -> None:
    """
    Omsæt inputfil(er) til GNU Gama-format

    FILNAVNE er navn(e) på inputfil(er), fx 'KDI2018vest.txt'

    Output skrives til en fil med samme fornavn, som første
    inputfil, men med '.xml' som efternavn.

    (Dette kan overstyres ved eksplicit at anføre et outputfilnavn
    med brug af option '-o NAVN')

    Fuldt udjævningsworkflow:

        fire mark gamaficer KDI2018vest.txt
        gama-local KDI2018vest.xml --html resultat.html
        start resultat.html
        start resultat.qgz
    """

    get_observations(get_observation_filenames(preload))
    # Generer et fornuftigt outputfilnavn
    if (output==''):
        fil = filnavne[0].name
        if (fil=='<stdin>'):
             output = '-'
        else:
            output = os.path.splitext(filnavne[0].name)[0] + '.xml'
    stuff_punktinfo (preload)

    # Læs alle inputfiler og opbyg oversigter over hhv.
    # anvendte punkter og udførte observationer
    try:
        observationer = list()
        punkter = set()
        for fil in filnavne:
            for line in fil:
                if '#'!=line[0]:
                    continue
                line = line.lstrip('#').strip()
                tokens = line.split()
                assert len(tokens) in (9, 13), "Malformed input line: "+line
                # print(tokens[0]+" "+tokens[1])
                observationer.append(line)
                punkter.add(tokens[0])
                punkter.add(tokens[1])
    except AssertionError as e:
        firecli.print(str(e))
        click.Abort()
    except:
        firecli.print("Fejl ved læsning af fil")
        click.Abort()

    print(f"OBSERVATIONER -- {len(observationer)}")
    # print(observationer)
    print(f"PUNKTER -- {len(punkter)}")
    print(punkter)

    eksporter(output, observationer, punkter)


def eksporter(output: str, observationer: List[str], punkter: Set[str]) -> None:
    """Skriv geojson og Gama-XML outputfiler"""
    koteid = None
    new_cache_records = 0

    # Generer dict med ident som nøgle og (position, kote, kotevarians) tuple som indhold
    punktinfo = get_cached_punktinfo()
    for ident in sorted(punkter):
        if ident not in punktinfo:
            if koteid is None:
                koteid = hent_sridid(firedb, "EPSG:5799")
            assert koteid != 0, "DVR90 (EPSG:5799) ikke fundet i srid-tabel"
            pinfo = punkt_information(ident)
            if pinfo is not None:
                new_cache_records += 1
            geo  = punkt_geometri(ident, pinfo)
            kote = punkt_kote(pinfo, koteid)
            (H, sH) = (0, 0) if kote is None else (kote.z, kote.sz)
            punktinfo[ident] = (geo[0], geo[1], H, sH)
    if new_cache_records > 0:
        cache_punktinfo (punktinfo)
    else:
        cache_punktinfo (punktinfo)

    # Skriv punktfil i geojson-format
    with open("punkter.geojson", "wt") as punktfil:
        til_json = {
            'type': 'FeatureCollection',
            'Features': list(punkt_feature(punktinfo))
        }
        json.dump(til_json, punktfil, indent=4)

    # Skriv observationsfil i geojson-format
    with open("observationer.geojson", "wt") as obsfil:
        til_json = {
            'type': 'FeatureCollection',
            'Features': list(obs_feature(punktinfo, observationer))
        }
        json.dump(til_json, obsfil, indent=4)

    # Skriv Gama-inputfil i XML-format
    with open(output, "wt") as gamafil:
        xml_preamble(gamafil)
        xml_description(gamafil, "bla bla bla")
        xml_fixed_points(gamafil)
        for key, val in punktinfo.items():
            if key.startswith("G."):
                xml_point(gamafil, True, key, val)
        xml_adjusted_points(gamafil)
        for key, val in punktinfo.items():
            if key.startswith("G.")==False:
                xml_point(gamafil, False, key, val)
        xml_observations(gamafil)

        for obs in obs_feature(punktinfo, observationer):
            xml_obs(gamafil, obs)
        xml_postamble(gamafil)

def get_observations(filnavne: str) -> List[str]:
    observationer = list()
    punkter = set()

    try:
        for fil in filnavne:
            with open(fil, "rt") as obsfil:
                for line in obsfil:
                    if '#'!=line[0]:
                        continue
                    line = line.lstrip('#').strip()
                    tokens = line.split()
                    print(line)
                    assert len(tokens) in (9, 13), "Malformed input line: "+line+" in file: "+fil
                    # print(tokens[0]+" "+tokens[1])
                    observationer.append(line)
                    punkter.add(tokens[0])
                    punkter.add(tokens[1])
    except AssertionError as e:
        firecli.print(str(e))
        click.Abort()
    except:
        firecli.print("Fejl ved læsning af fil")
        click.Abort()
    for obs in observationer:
        print(obs)
    return observationer


def get_observation_filenames(nivproj: click.Path) -> List[str]:
    """Indlæs foreløbige registreringer i cachefil"""
    if nivproj=='':
        return
    names = list()

    with open(nivproj, "rt") as niv:
        level = 0
        for line in niv:
            line = line.strip()
            level = skip_until_section("OBSERVATIONSFILER", line, level)
            if (level!=4):
                continue

            # remove leading and trailing comments
            line = line.split('#')[0]
            line.rstrip()
            names += line.split()
            print("OEPHGREASE")
            print(names)
    return names


def get_cached_punktinfo() -> Dict:
    if not os.path.isfile("cached_punktinfo.json"):
        return {}
    with open("cached_punktinfo.json", "rt") as cache:
        r = json.load(cache)
    return {} if r is None else r


def cache_punktinfo(punktinfo: Dict):
    with open("cached_punktinfo.json", "wt") as cache:
        r = json.dump(punktinfo, cache, indent=4)


def stuff_punktinfo(preload: click.Path):
    """Indlæs foreløbige registreringer i cachefil"""
    if preload=='':
        return
    pinfo = get_cached_punktinfo()
    utm32 = Proj('+proj=utm +zone=32 +ellps=GRS80', preserve_units=False)

    with open(preload, "rt") as pre:
        level = 0
        for line in pre:
            line = line.strip()
            level = skip_until_section("NYETABLEREDE PUNKTER", line, level)
            if (level!=4):
                continue

            # remove leading and trailing comments
            line = line.split('#')[0]
            line.rstrip()

            # parse input line
            tokens = line.split()
            if (len(tokens)<3):
                continue
            ident = tokens[0]
            lat = float(tokens[1])
            lon = float(tokens[2])
            # Heuristic for determining whether coordinate is UTM or degrees
            if (abs(lat) > 1000):
                (lon, lat) = utm32(lon, lat, inverse=True)
                print(f'{line} -- transformeres til: {lat}, {lon}')
            pinfo[ident] = [lon, lat, 0, 0]
    cache_punktinfo(pinfo)


def skip_until_section(section: str, line: str, level: int) -> int:
    if level==3:
        return 4
    if line[0:5]=="-----":
        if level==0:
            return 1
        if level==1:
            return 0
        if level==2:
            return 3
        if level==4:
            return 1
    if level!=1:
        return level
    if line==section:
        return 2
    return level


def obs_feature(punkter: Dict, observationer: List[str]) -> Dict:
    """Omsæt observationsinformationer til JSON-egnet dict"""
    for obs in observationer:
        dele = obs.split()
        assert len(dele) in (9, 13), "Malformet observation: " + obs

        fra = punkter[dele[0]]
        til = punkter[dele[1]]
        # Endnu ikke registrerede punkter sendes ud i Kattegat
        if fra is None:
            fra = [11, 56, 0]
        if til is None:
            til = [11, 56, 0]

        # Reparer mistænkelig formateringsfejl
        if dele[5].endswith("-557"):
            dele[5] = dele[5][:-4]

        feature = {
            'type': 'Feature',
            'properties': {
               'fra': dele[0],
               'til': dele[1],
               'dist': float(dele[4]),
               'dH':  float(dele[5]),
               'setups': int(dele[8]),
               'journal': dele[6]
            },
            'geometry': {
                'type': 'LineString',
                'coordinates': [
                    [float(fra[0]), float(fra[1])],
                    [float(til[0]), float(til[1])]
                ]
            }
        }
        yield feature


def punkt_feature(punkter: Dict) -> Dict:
    """Omsæt punktinformationer til JSON-egnet dict"""
    for key, val in punkter.items():
        feature = {
            'type': 'Feature',
            'properties': {
               'id': key,
               'H':  val[2],
               'sH': val[3]
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [val[0], val[1]]
            }
        }
        yield feature


def punkt_information(ident: str) -> PunktInformation:
    """Find alle informationer for et fikspunkt"""
    pi = aliased(PunktInformation)
    pit = aliased(PunktInformationType)
    try:
        punktinfo = (
            firedb.session.query(pi).filter(
                pit.name.startswith("IDENT:"),
                pi.tekst == ident
            ).first()
        )
    except NoResultFound:
        firecli.print(f"Error! {ident} not found!", fg="red", err=True)
        sys.exit(1)
    firecli.print(f"Fandt {ident}", fg="green", err=False)
    print(punktinfo)
    return punktinfo


def punkt_kote(punktinfo: PunktInformation, koteid: int) -> Koordinat:
    """Find aktuelle koordinatværdi for koordinattypen koteid"""
    if punktinfo is None:
        return None
    for koord in punktinfo.punkt.koordinater:
        if (koord.sridid != koteid):
            continue
        if koord.registreringtil is None:
            return koord
    return None


def punkt_geometri(ident: str, punktinfo: PunktInformation) -> Tuple[float, float]:
    """Find placeringskoordinat for punkt"""
    if punktinfo is None:
        return (11, 56)
    try:
        geom = firedb.hent_geometri_objekt(punktinfo.punktid)
        # Turn the string "POINT (lon lat)" into the tuple "(lon, lat)"
        geo = eval(str(geom.geometri).lstrip("POINT ").replace(' ', ','))
        assert len(geo)==2, "Bad geometry format: " + str(geom.geometri)
    except NoResultFound:
        firecli.print(f"Error! Geometry for {ident} not found!", fg="red", err=True)
        sys.exit(1)
    return geo


# Bør nok være en del af API
def hent_sridid(db, srid: str) -> int:
    srider = db.hent_srider()
    for s in srider:
        if (s.name==srid):
            return s.sridid
    return 0


# XML-hjælpefunktioner herfra

def xml_preamble(fil: IO['wt']) -> None:
    fil.writelines(
        '<?xml version="1.0" ?><gama-local>\n'
        '<network angles="left-handed" axes-xy="en" epoch="0.0">\n'
        '<parameters\n'
        '    algorithm="gso" angles="400" conf-pr="0.95"\n'
        '    cov-band="0" ellipsoid="grs80" latitude="55.7" sigma-act="apriori"\n'
        '    sigma-apr="1.0" tol-abs="1000.0"\n'
        '    update-constrained-coordinates="no"\n'
        '/>\n\n'
    )

def xml_description(fil: IO['wt'], desc: str) -> None:
    fil.writelines(
        f"<description>\n{desc}\n</description>\n<points-observations>\n\n"
    )

def xml_fixed_points(fil: IO['wt']) -> None:
    fil.writelines("\n\n<!-- Fixed -->\n\n")

def xml_adjusted_points(fil: IO['wt']) -> None:
    fil.writelines("\n\n<!-- Adjusted -->\n\n")

def xml_observations(fil: IO['wt']) -> None:
    fil.writelines("\n\n<height-differences>\n\n")

def xml_postamble(fil: IO['wt']) -> None:
    fil.writelines(
        "\n</height-differences></points-observations></network></gama-local>"
    )


def xml_point(fil: IO['wt'], fix: bool, key: str, val: Dict) -> None:
    """skriv punkt i Gama XML-notation"""
    fixadj = 'fix="Z"' if fix==True else 'adj="z"'
    z = val[2]
    fil.write(f'<point {fixadj} id="{key}" z="{z}"/>\n')


def xml_obs(fil: IO['wt'], obs: Dict) -> None:
    """skriv observation i Gama XML-notation"""
    fra = obs['properties']['fra']
    til = obs['properties']['til']
    val = obs['properties']['dH']
    dist = obs['properties']['dist'] / 1000.0
    # TODO: Brug rette udtryk til opmålingstypen
    stdev = sqrt(dist)*0.6+0.01*obs['properties']['setups']
    fil.write(
        f'<dh from="{fra}" to="{til}" '
        f'val="{val:+.5f}" dist="{dist:.5f}" stdev="{stdev:.2f}"/>\n'
    )
