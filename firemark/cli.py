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
@click.argument('filnavn', nargs=1, type=click.Path(writable=False, readable=True, allow_dash=False))
def observationsliste(filnavn: click.Path, **kwargs) -> None:
    """Oplist alle observationer der indgår i et nivellementsprojekt"""
    get_all_observation_strings(filnavn, True)


@mark.command()
@firecli.default_options()
@click.argument('filnavn', nargs=1, type=click.Path(writable=False, readable=True, allow_dash=False))
def punktliste(filnavn: click.Path, **kwargs) -> None:
    """Oplist alle punkter der indgår i et nivellementsprojekt"""
    observationer = get_all_observation_strings(filnavn)
    get_observation_points(observationer, True)


@mark.command()
@firecli.default_options()
@click.argument('filnavn', nargs=1, type=click.Path(writable=False, readable=True, allow_dash=False))
def variabelliste(filnavn: click.Path, **kwargs) -> None:
    """Oplist alle kontrolvariable fra SETUP-afsnit"""
    s = get_setup_dict(filnavn)
    for k,v in s.items():
        print("s["+k+"] = '"+v+"'")


@mark.command()
@firecli.default_options()
@click.option(
    '-o', '--output', default='', type=click.Path(writable=True, readable=False, allow_dash=True),
    help='Sæt navn på outputfil'
)
@click.argument('projektfil', nargs=1, type=click.Path(writable=False, readable=True, allow_dash=False))
def gamaficer(projektfil: click.Path, output: click.Path, **kwargs) -> None:
    """
    Omsæt nivellementsprojektfil til GNU Gama-format

    PROJEKTFIL er navnet på projektet, fx 'KDI2018vest.np'

    Output skrives til en fil med samme fornavn, som første
    inputfil, men med '.xml' som efternavn.

    (Dette kan overstyres ved eksplicit at anføre et outputfilnavn
    med brug af option '-o NAVN')

    Fuldt udjævningsworkflow:

        fire mark gamaficer KDI2018vest.np
        gama-local KDI2018vest.xml --html resultat.html
        start resultat.html
        start resultat.qgz
    """

    projektnavn = os.path.splitext(projektfil)[0]

    # Generer et fornuftigt outputfilnavn
    if (output==''):
        output = projektnavn + '.xml'
    prop_punktinfo_i_cachefil (projektfil)

    # Læs alle inputfiler og opbyg oversigter over hhv.
    # anvendte punkter og udførte observationer
    observationer = get_all_observation_strings(projektfil)
    punkter = get_observation_points(observationer)
    eksporter(projektnavn, output, observationer, punkter)

def eksporter(projektnavn: str, output: str, observationer: List[str], punkter: Set[str]) -> None:
    """Skriv geojson og Gama-XML outputfiler"""
    koteid = hent_sridid(firedb, "EPSG:5799")
    assert koteid != 0, "DVR90 (EPSG:5799) ikke fundet i srid-tabel"

    # Generer dict med ident som nøgle og (placering, kote, kotevarians) tuple som indhold
    punktinfo = get_cached_punktinfo()
    for ident in sorted(punkter):
        if ident in punktinfo:
            continue
        info = punkt_information(ident)
        geom = punkt_geometri(info, ident)
        kote = punkt_kote(info, koteid)
        (H, sH) = (0, 0) if kote is None else (kote.z, kote.sz)
        punktinfo[ident] = (geom[0], geom[1], H, sH)
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
        xml_description(gamafil, "Nivellementsprojekt " + projektnavn)
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


def get_all_observation_strings(projektfil: click.Path, verbose: bool = False) -> List[str]:
    """Læs alle observationer, både fra projektfil og fra projektets markfiler"""
    try:
        observationer = get_internal_observation_strings(projektfil, verbose)
        filnavne = get_observation_filenames(projektfil)
        if 0==len(filnavne):
            return observationer
        for fil in filnavne:
            observationer += get_observation_strings(fil, verbose)
        assert len(set(observationer)) == len(observationer), "Dublerede observationer - slå evt. eksterne filer fra."
        return observationer
    except AssertionError as e:
        firecli.print(str(e))
        click.Abort()
    except:
        firecli.print("Fejl ved læsning af fil")
        click.Abort()


def get_internal_observation_strings(nivproj: click.Path, verbose: bool = False) -> List[str]:
    """Returner liste med alle observationsstrenge fra OBSERVATIONER afsnittet i projektfil"""
    observationer = list()
    if verbose:
        print(f"\n# Interne fra {nivproj}\n")
    with open(nivproj, "rt") as niv:
        level = 0
        for line in niv:
            line = line.strip()
            level = skip_until_section("OBSERVATIONER", line, level)
            if (level!=4):
                continue
            # remove leading and trailing comments
            line = line.split('#')[0].rstrip()
            if len(line)==0:
                continue
            if verbose:
                print(line)
            observationer.append(line)
    return observationer


def get_observation_strings(filnavn: str, verbose: bool = False) -> List[str]:
    observationer = list()
    with open(filnavn, "rt") as obsfil:
        if verbose:
            print(f"\n# Fra {filnavn}\n")
        for line in obsfil:
            if '#'!=line[0]:
                continue
            line = line.lstrip('#').strip()
            if verbose:
                print(line)
            tokens = line.split()
            assert len(tokens) in (9, 13), "Malformed input line: "+line+" in file: "+fil
            observationer.append(line)
    return observationer


def get_observation_points(obstrings: List[str], verbose: bool = False) -> Set[str]:
    points = set()
    for obs in obstrings:
        tokens = obs.split()
        points.add(tokens[0])
        points.add(tokens[1])
    if verbose:
        for p in sorted(points):
            print(p)
    return points


def get_setup_dict(nivproj: click.Path) -> Dict[str, str]:
    """Læs setup-strenge fra nivellementsprojektfil"""
    if nivproj=='':
        return
    names = dict()

    with open(nivproj, "rt") as niv:
        level = 0
        for line in niv:
            level = skip_until_section("SETUP", line, level)
            if (level!=4):
                continue
            # remove leading and trailing comments
            line = line.split('#')[0].strip().split("=")
            if type(line) is not list:
                continue
            if len(line)!=2:
                continue
            names[line[0].strip()] = line[1].strip()
    return names



def get_observation_filenames(nivproj: click.Path) -> List[str]:
    """Læs observationsfilnavne fra nivellementsprojektfil"""
    if nivproj=='':
        return
    names = list()

    with open(nivproj, "rt") as niv:
        level = 0
        for line in niv:
            level = skip_until_section("OBSERVATIONSFILER", line, level)
            if (level!=4):
                continue
            # remove leading and trailing comments
            line = line.split('#')[0].strip()
            names += line.split()
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


def prop_punktinfo_i_cachefil(nivproj: click.Path):
    """Indlæs foreløbige registreringer i cachefil"""
    if nivproj=='':
        return
    pinfo = get_cached_punktinfo()
    utm32 = Proj('+proj=utm +zone=32 +ellps=GRS80', preserve_units=False)
    assert utm32 is not None, "Kan ikke initialisere projektionselelement utm32"

    with open(nivproj, "rt") as np:
        level = 0
        for line in np:
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
    """Utterly ugly logic. Returns 4 at the start of the section wanted"""

    if level==3:
        return 4     # we are now in the correct section

    # At start or end of banner?
    if line[0:5]=="-----":
        if level==0:
            return 1  # we just entered a banner
        if level==1:
            return 0  # we just finished a wrong banner
        if level==2:
            return 3  # we just finished the correct banner
        if level==4:
            return 1  # we now entered a new banner at the end of the correct section

    if level!=1:
        return level  # nothing new

    current_section = line.split(":")[0].strip()
    if current_section==section:
        return 2      # we are inside the right banner - continue skipping until "end of banner"

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


def punkt_geometri(punktinfo: PunktInformation, ident: str) -> Tuple[float, float]:
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
