from typing import List, Dict
import math

from sqlalchemy.orm.exc import NoResultFound

from fire.api.model import Observation, Punkt
from fire.api import FireDb


class GamaNetworkDoc:
    def __init__(self, fireDb: FireDb, parameters: Dict):
        # Input parameters
        self.fireDb = fireDb
        self.parameters = parameters
        self.observations = []
        self.fixed_point_ids = []

        # Local parameters
        self.relevant_observations = []
        self.adjustable_points = []
        self.fixed_points = []
        self.description_header = (
            "Network doc created by fire-gama (https://github.com/Septima/fire-gama)"
        )
        self.description_items = [self.description_header]
        self.warning_items = ["Warnings:"]

    def add_description(self, description):
        self.description_items.append(description)

    def add_warning(self, warning):
        self.warning_items.append(warning)

    def set_observations(self, observations: List[Observation]):
        self.observations = observations
        self.add_description(
            "GamaNetworkDoc.set_observations: Antal observationer: "
            + str(len(observations))
        )

    def set_fixed_point_ids(self, fixed_point_ids: List[str]):
        self.fixed_point_ids = fixed_point_ids
        for point_id in fixed_point_ids:
            point = self.fireDb.hent_punkt(point_id)
            self.fixed_points.append(point)
        self.add_description(
            "GamaNetworkDoc.set_fixed_points: Antal punkter: "
            + str(len(fixed_point_ids))
        )

    def write(self, stream, heights: bool, positions: bool):
        output = self.get_template()

        output = self.insert_fixed_points(self.fixed_points, heights, positions, output)

        self.relevant_observations = self.filter_observations(
            self.observations, heights, positions
        )
        self.adjustable_points = self.get_points_from_observations(
            self.relevant_observations
        )
        output = self.insert_adjustable_points(
            self.adjustable_points, heights, positions, output
        )

        output = self.insert_observations(
            self.relevant_observations, heights, positions, output
        )

        output = self.insert_description(self.description_items, output)

        output = self.insert_network_attributes(self.parameters, output)
        output = self.insert_network_parameters(self.parameters, output)
        output = self.insert_points_observations_attributes(self.parameters, output)

        stream.write(output)

    def get_template(self):
        template = (
            '<?xml version="1.0" ?>\n'
            '<gama-local xmlns="http://www.gnu.org/software/gama/gama-local">\n'
            "    <network {networkAttributes}>\n"
            "        <parameters {networkParameters}/>\n"
            "        <description>\n"
            "            {description}\n"
            "        </description>\n"
            "        <points-observations {pointsObservationsAttributes}>\n"
            "            {fixedPoints}\n"
            "            {adjustablePoints}\n"
            "            <height-differences>\n"
            "                {obs}\n"
            "            </height-differences>\n"
            "        </points-observations>\n"
            "    </network>\n"
            "</gama-local>"
        )
        return template

    def insert_network_attributes(self, parameters: Dict, doc):
        attribute_values = []
        if "network-attributes" in parameters:
            for key in parameters["network-attributes"]:
                attribute_values.append(
                    key + '="' + parameters["network-attributes"][key] + '"'
                )
        return str.replace(doc, "{networkAttributes}", " ".join(attribute_values))

    def insert_network_parameters(self, parameters: Dict, doc):
        attribute_values = []
        if "network-parameters" in parameters:
            for key in parameters["network-parameters"]:
                attribute_values.append(
                    key + '="' + parameters["network-parameters"][key] + '"'
                )
        return str.replace(doc, "{networkParameters}", " ".join(attribute_values))

    def insert_points_observations_attributes(self, parameters: Dict, doc):
        attribute_values = []
        if "points-observations-attributes" in parameters:
            for key in parameters["points-observations-attributes"]:
                attribute_values.append(
                    key + '="' + parameters["points-observations-attributes"][key] + '"'
                )
        return str.replace(
            doc, "{pointsObservationsAttributes}", " ".join(attribute_values)
        )

    def insert_description(self, description_items: List[str], doc):
        if len(self.warning_items) > 1:
            description_items.extend(self.warning_items)
        return str.replace(
            doc, "{description}", "\n            ".join(description_items)
        )

    def filter_observations(
        self, observations: List[Observation], heights: bool, positions: bool
    ):
        filtered_observations = []
        for o in observations:
            # Filter for None in udgang or sigte (o.opstillingspunktid, o.sigtepunktid not none)
            if (o.opstillingspunktid is not None) and (o.sigtepunktid is not None):
                # Filter for suitability to establish height (o.observationstypeid in ['trigonometrisk_koteforskel', geometrisk_koteforskel])
                # if o.observationstypeid in ['trigonometrisk_koteforskel', 'geometrisk_koteforskel']:
                if o.observationstypeid in [1, 2]:
                    values = self.get_values(o, heights, positions)
                    if values is not None:
                        setattr(o, "gama_values", values)
                        # o['gama_values'] = values
                        filtered_observations.append(o)
        # Filter for epsg? 'trigonometrisk_koteforskel': dev=math.sqrt((o.value4 + o.value5)/o.antal) / 'geometrisk_koteforskel': dev=math.sqrt((o.value4 + o.value5)/o.antal) // val=o.value1
        return filtered_observations

    def get_values(self, observation: Observation, heights: bool, positions: bool):
        # if observation.observationstypeid == 'trigonometrisk_koteforskel':
        if observation.observationstypeid == 2:
            if (
                (observation.value4 is not None)
                and (observation.value5 is not None)
                and (observation.antal is not None)
                and (observation.antal != 0)
            ):
                dev = math.sqrt(
                    (observation.value4 + observation.value5) / observation.antal
                )
                val = observation.value1
                if observation.value2 is not None:
                    dist = observation.value2 / 1000
                else:
                    dist = "?"
                return {"dev": dev, "val": val, "dist": dist}
        # if observation.observationstypeid == 'geometrisk_koteforskel':
        if observation.observationstypeid == 1:
            if (
                (observation.value5 is not None)
                and (observation.value6 is not None)
                and (observation.antal is not None)
                and (observation.antal != 0)
            ):
                dev = math.sqrt(
                    (observation.value5 + observation.value6) / observation.antal
                )
                val = observation.value1
                if observation.value2 is not None:
                    dist = observation.value2 / 1000
                else:
                    dist = "?"
                return {"dev": dev, "val": val, "dist": dist}
        return None

    def get_points_from_observations(self, observations: List[Observation]):
        points_list = []
        point_ids_list = []
        for o in observations:
            op_id = o.opstillingspunktid
            if op_id not in point_ids_list:  # Point not already found
                if op_id not in self.fixed_point_ids:  # Not given as a fixed point
                    try:
                        op = self.fireDb.hent_punkt(op_id)
                    except NoResultFound:
                        continue
                    points_list.append(op)
                    point_ids_list.append(op_id)
            sp_id = o.sigtepunktid
            if sp_id not in point_ids_list:  # Point not already found
                if sp_id not in self.fixed_point_ids:  # Not given as a fixed point
                    try:
                        sp = self.fireDb.hent_punkt(sp_id)
                    except NoResultFound:
                        continue
                    points_list.append(sp)
                    point_ids_list.append(sp_id)
        return points_list

    def insert_fixed_points(
        self, fixed_points: List[Punkt], heights: bool, positions: bool, doc
    ):
        if len(fixed_points) == 0:
            self.add_warning("No fixed points")
            return str.replace(doc, "{fixedPoints}", "")
        else:
            fixed_points_elements = []
            for fixed_point in fixed_points:
                fixed_points_elements.append(
                    self.get_fixed_height_point_element(fixed_point)
                )
            return str.replace(
                doc, "{fixedPoints}", "\n            ".join(fixed_points_elements)
            )

    def insert_adjustable_points(
        self, points: List[Punkt], heights: bool, positions: bool, doc
    ):
        adjustable_points = []
        for adjustable_point in points:
            adjustable_points.append(
                self.get_adjustable_height_point_element(adjustable_point)
            )
        return str.replace(
            doc, "{adjustablePoints}", "\n            ".join(adjustable_points)
        )

    def insert_observations(
        self, observations: List[Observation], heights: bool, positions: bool, doc
    ):
        observation_elements = []
        observation_ids = []
        for o in observations:
            observation_elements.append(self.get_dh_element(o))
            # observation_ids.append(str(o.objectid))
        # self.add_description("{observation_ids} :[" + ",".join(observation_ids) + "]{/observation_ids}")
        return str.replace(
            doc, "{obs}", "\n                ".join(observation_elements)
        )

    def get_fixed_height_point_element(self, fixed_point: Punkt):
        point_id = fixed_point.id
        ks: List[koordinat] = fixed_point.koordinater
        for k in ks:
            if k.srid.name == "EPSG:5799":
                z = k.z
                return '<point id="{id}" z="{z}" fix="z" />'.format(id=point_id, z=z)
        self.add_warning("Fixed point with no z value. Punktid:" + point_id)
        return '<point id="{id}" fix="z" />'.format(id=point_id)

    def get_adjustable_height_point_element(self, adjustable_point: Punkt):
        point_id = adjustable_point.id
        ks: List[koordinat] = adjustable_point.koordinater
        for k in ks:
            if k.srid.name == "EPSG:5799":
                z = k.z
                return '<point id="{id}" z="{z}" adj="z" />'.format(id=point_id, z=z)
        return '<point id="{id}" adj="z" />'.format(id=point_id)

    def get_dh_element(self, observation: Observation):
        fromId = observation.opstillingspunktid
        toId = observation.sigtepunktid
        oId = observation.objectid
        gamavalues = getattr(observation, "gama_values")
        val = gamavalues["val"]
        dist = gamavalues["dist"]
        dev = gamavalues["dev"]
        return '<dh from="{fromId}" to="{toId}" val="{val}" dist="{dist}" stdev="{dev}" extern="{oId}"/>'.format(
            fromId=fromId, toId=toId, val=val, dist=dist, dev=dev, oId=oId
        )
