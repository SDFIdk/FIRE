from typing import List, Dict
from fire.api import FireDb
from fire.api.model import Observation
from .networkdoc import GamaNetworkDoc


class GamaWriter(object):
    def __init__(self, fireDb: FireDb, output_stream):
        # Input parameters
        self.fireDb = fireDb
        self.output_stream = output_stream
        self.fixed_points = []

        # Local parameters
        self.obsList = []

    def set_fixed_point_ids(self, fixed_points: List[str]):
        self.fixed_points = fixed_points

    def take_all_points(self):
        points = self.fireDb.hent_alle_punkter()
        obsDict = {}
        for point in points:
            of = point.observationer_fra
            for o in of:
                if o.objektid not in obsDict:
                    obsDict[o.objektid] = o
                    self.obsList.append(o)
            ot = point.observationer_til
            for o in ot:
                if o.objektid not in obsDict:
                    obsDict[o.objektid] = o
                    self.obsList.append(o)

        self.point_set_description = (
            "GamaWriter.take_all_points() Antal punkter: " + str(len(points))
        )

    def take_observations(self, observations: List[Observation]):
        self.obsList = observations
        self.point_set_description = (
            "GamaWriter.take_observations() Antal observationer: "
            + str(len(observations))
        )

    def write(self, heights, pos, parent_description, parameters: Dict):
        self.parent_description = parent_description

        doc = GamaNetworkDoc(self.fireDb, parameters)
        doc.add_description("Initiated by " + parent_description)
        doc.add_description(self.point_set_description)
        doc.set_fixed_point_ids(self.fixed_points)
        doc.set_observations(self.obsList)
        doc.write(self.output_stream, heights, pos)
